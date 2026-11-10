#!/usr/bin/env python3
"""Neo AI Terminal dashboard: Duck.ai Free in-panel engine + optional official API."""
from __future__ import annotations

import json
import re
import sqlite3
import os
import tempfile
import threading
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

import duck_cli
import api_providers
import secure_store
import duckai_catalog
import duck_voice

# PyInstaller stores read-only application resources under sys._MEIPASS.
# User data (SQLite history and generated images) must live outside that bundle.
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ROOT = BUNDLE_ROOT
WEB_DIR = BUNDLE_ROOT / "web"
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    if (EXE_DIR / "portable.flag").is_file():
        # Portable release: keep history, generated files and DB next to the EXE.
        USER_DATA_ROOT = EXE_DIR / "data"
    else:
        USER_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Neo AI Terminal"
else:
    USER_DATA_ROOT = Path(__file__).resolve().parent
USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)
GENERATED_DIR = USER_DATA_ROOT / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = USER_DATA_ROOT / "neo_ai_terminal.sqlite3"
DB_LOCK = threading.RLock()
APP_STARTED = time.time()

def init_database() -> None:
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            owner_session TEXT NOT NULL,
            title TEXT NOT NULL,
            model TEXT NOT NULL,
            history_json TEXT NOT NULL,
            messages_json TEXT NOT NULL,
            turns INTEGER NOT NULL DEFAULT 0,
            requests INTEGER NOT NULL DEFAULT 0,
            images INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_owner_updated ON conversations(owner_session, updated_at DESC)")
        conn.execute("""CREATE TABLE IF NOT EXISTS user_preferences (
            owner_session TEXT PRIMARY KEY,
            default_model TEXT NOT NULL DEFAULT 'duckai:gpt-6-luna',
            updated_at REAL NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS provider_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            provider TEXT NOT NULL,
            base_url TEXT NOT NULL,
            model TEXT NOT NULL,
            secret_value TEXT NOT NULL DEFAULT '',
            updated_at REAL NOT NULL
        )""")
        conn.execute(
            "INSERT OR IGNORE INTO provider_config (id,provider,base_url,model,secret_value,updated_at) VALUES (1,?,?,?,?,?)",
            ("openai", api_providers.PROVIDER_INFO["openai"]["base_url"], api_providers.PROVIDER_INFO["openai"]["model"], "", time.time()),
        )
        for legacy_model in duckai_catalog.FREE_MODEL_IDS:
            conn.execute("UPDATE user_preferences SET default_model=? WHERE default_model=?", ("duckai:" + legacy_model, legacy_model))
            conn.execute("UPDATE conversations SET model=? WHERE model=?", ("duckai:" + legacy_model, legacy_model))
        conn.commit()


init_database()

@dataclass
class WebSession:
    session_id: str
    model: str = "duckai:gpt-6-luna"
    proxy: Optional[str] = None
    client: Optional[duck_cli.DuckAI] = None
    history: list = field(default_factory=list)
    turns: int = 0
    image_count: int = 0
    requests: int = 0
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    lock: threading.RLock = field(default_factory=threading.RLock)
    activity: deque = field(default_factory=lambda: deque(maxlen=30))
    conversation_id: str = ""
    conversation_title: str = "New conversation"
    display_messages: list = field(default_factory=list)

    def get_client(self) -> duck_cli.DuckAI:
        if self.client is None:
            self.client = duck_cli.DuckAI(proxy=self.proxy)
        return self.client

    def add_activity(self, kind: str, detail: str) -> None:
        now = time.time()
        self.last_active = now
        self.activity.appendleft({
            "kind": kind,
            "detail": detail[:120],
            "timestamp": now,
        })


sessions: dict[str, WebSession] = {}
sessions_lock = threading.Lock()


def _valid_uuid(value: Optional[str]) -> str:
    try:
        return str(uuid.UUID(value or ""))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid session or conversation identifier")


def _get_provider_config() -> dict:
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT provider,base_url,model,secret_value FROM provider_config WHERE id=1").fetchone()
    if not row:
        info = api_providers.PROVIDER_INFO["openai"]
        return {"provider": "openai", "base_url": info["base_url"], "model": info["model"], "secret_value": ""}
    provider, base_url, model, secret_value = row
    if provider not in api_providers.PROVIDER_INFO:
        provider = "openai"
    info = api_providers.PROVIDER_INFO[provider]
    # Migration guard: earlier local builds could leave a Duck.ai private URL
    # in the provider configuration. Restore the selected provider's official
    # base URL automatically while preserving its model ID and encrypted key.
    migrated = False
    if api_providers.is_duckai_url(base_url):
        base_url = info["base_url"]
        migrated = True
    # Keep active provider model IDs intact; only explicit aliases are normalized.
    normalized_model = api_providers.normalize_model_id(provider, model or "")
    if normalized_model != (model or ""):
        model = normalized_model
        migrated = True
    if migrated:
        with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE provider_config SET base_url=?,model=?,updated_at=? WHERE id=1", (base_url, model, time.time()))
            conn.commit()
    return {"provider": provider, "base_url": base_url or info["base_url"], "model": model or info["model"], "secret_value": secret_value or ""}


def _provider_api_key(config: dict) -> str:
    return secure_store.load_secret("api-key-" + config["provider"], config.get("secret_value"))


def _save_provider_config(provider: str, base_url: str, model: str, api_key: str | None = None, clear_api_key: bool = False) -> None:
    if provider not in api_providers.PROVIDER_INFO:
        raise HTTPException(status_code=400, detail="Unsupported API provider")
    info = api_providers.PROVIDER_INFO[provider]
    base_url = (base_url or info["base_url"]).strip().rstrip("/")
    model = api_providers.normalize_model_id(provider, (model or "").strip())
    if not model or len(model) > 160:
        raise HTTPException(status_code=400, detail="Enter a valid model ID (maximum 160 characters).")
    try:
        base_url = api_providers.validate_base_url(base_url)
    except api_providers.ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT provider,secret_value FROM provider_config WHERE id=1").fetchone()
        old_provider, old_secret = row if row else (provider, "")
        secret_value = old_secret if old_provider == provider else ""
        if clear_api_key:
            secure_store.delete_secret("api-key-" + old_provider, old_secret)
            secret_value = ""
        if api_key and api_key.strip():
            secret_value = secure_store.save_secret("api-key-" + provider, api_key.strip())
        updated_at = time.time()
        conn.execute(
            "INSERT INTO provider_config (id,provider,base_url,model,secret_value,updated_at) VALUES (1,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET provider=excluded.provider,base_url=excluded.base_url,model=excluded.model,secret_value=excluded.secret_value,updated_at=excluded.updated_at",
            (provider, base_url, model, secret_value, updated_at),
        )
        conn.commit()
    if old_provider != provider and old_secret:
        secure_store.delete_secret("api-key-" + old_provider, old_secret)


def _available_model_catalog() -> list[dict]:
    config = _get_provider_config()
    provider = config["provider"]
    info = api_providers.PROVIDER_INFO[provider]
    model_id = config["model"]
    normalized_model = model_id.lower()
    reasoning = {"options": [], "default": "auto"}
    if provider == "openai" and normalized_model.startswith(("gpt-5", "gpt-6", "o1", "o3", "o4")):
        reasoning = {"options": ["none", "low", "medium", "high"], "default": "medium"}
    elif provider == "anthropic":
        supported_efforts = api_providers.anthropic_effort_options(normalized_model)
        if supported_efforts:
            reasoning = {
                "options": ["none", *supported_efforts],
                "default": "medium" if normalized_model in {"claude-haiku-5-5", "claude-opus-5-5"} else "high",
            }
    # Legacy Claude 4.5 models without API effort support remain model-managed.
    elif provider == "gemini" and normalized_model in {"gemini-3.8-flash", "gemini-3.7-flash"}:
        reasoning = {"options": ["none", "low", "medium", "high"], "default": "medium"}
    elif provider == "gemini" and normalized_model == "gemini-3.6-flash":
        reasoning = {"options": ["none", "minimal", "low", "medium", "high"], "default": "medium"}
    return [{"id": model_id, "key": model_id, "name": model_id, "provider": info["label"],
             "description": "Configured API model", "color": "cyan", "reasoning": reasoning,
             "api_configured": bool(config.get("secret_value"))}]


def _combined_model_catalog() -> list[dict]:
    models = []
    for item in duckai_catalog.get_free_models():
        models.append({
            "id": item["id"], "key": item["key"], "model_id": item["model_id"],
            "name": item["name"], "provider": item["provider"],
            "description": "Duck.ai Free model · used directly inside this panel",
            "color": "violet" if item["provider"] == "Anthropic" else "cyan",
            # Per-model capability metadata prevents unsupported parameters.
            "reasoning": duckai_catalog.get_reasoning_profile(item["model_id"]),
            "engine": "duckai", "tier": "free",
        })
    config = _get_provider_config()
    info = api_providers.PROVIDER_INFO[config["provider"]]
    api_item = _available_model_catalog()[0]
    models.append({
        "id": "api:configured", "key": "api:configured", "model_id": config["model"],
        "name": f"{info['label']} · {config['model']}", "provider": info["label"],
        "description": "Optional official API model", "color": "cyan",
        "reasoning": api_item["reasoning"], "engine": "official_api",
        "api_configured": bool(config.get("secret_value")),
    })
    return models


def _normalise_panel_model(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return "duckai:gpt-6-luna"
    if raw == "api:configured":
        return raw
    try:
        return "duckai:" + duckai_catalog.resolve_free_model(raw)
    except ValueError:
        config = _get_provider_config()
        if raw == config["model"]:
            return "api:configured"
        raise HTTPException(status_code=400, detail="Choose one of the six Duck.ai Free models or the optional configured API model.")


def _duckai_model_id(panel_model: str) -> str:
    if not panel_model.startswith("duckai:"):
        raise HTTPException(status_code=400, detail="Select a Duck.ai Free model first.")
    try:
        return duckai_catalog.resolve_free_model(panel_model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _get_default_model(owner_session: str) -> str:
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT default_model FROM user_preferences WHERE owner_session=?", (owner_session,)).fetchone()
    if row and row[0]:
        try:
            return _normalise_panel_model(row[0])
        except HTTPException:
            return "duckai:gpt-6-luna"
    return "duckai:gpt-6-luna"


def _set_default_model(owner_session: str, model: str) -> None:
    now = time.time()
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO user_preferences (owner_session,default_model,updated_at) VALUES (?,?,?) "
            "ON CONFLICT(owner_session) DO UPDATE SET default_model=excluded.default_model, updated_at=excluded.updated_at",
            (owner_session, model, now),
        )
        conn.commit()


def _load_conversation(owner_session: str, conversation_id: str) -> dict:
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM conversations WHERE id=? AND owner_session=?",
            (conversation_id, owner_session),
        ).fetchone()
        if row is None:
            now = time.time()
            default_model = _get_default_model(owner_session)
            conn.execute(
                "INSERT INTO conversations (id,owner_session,title,model,history_json,messages_json,turns,requests,images,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (conversation_id, owner_session, "New conversation", default_model, "[]", "[]", 0, 0, 0, now, now),
            )
            conn.commit()
            return {"id": conversation_id, "title": "New conversation", "model": default_model, "history": [], "messages": [], "turns": 0, "requests": 0, "images": 0, "created_at": now, "updated_at": now}
        return {
            "id": row["id"], "title": row["title"], "model": row["model"],
            "history": json.loads(row["history_json"] or "[]"),
            "messages": json.loads(row["messages_json"] or "[]"),
            "turns": row["turns"], "requests": row["requests"], "images": row["images"],
            "created_at": row["created_at"], "updated_at": row["updated_at"],
        }


def _save_conversation(state: WebSession) -> None:
    if not state.conversation_id:
        return
    now = time.time()
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO conversations (id,owner_session,title,model,history_json,messages_json,turns,requests,images,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET title=excluded.title, model=excluded.model,
               history_json=excluded.history_json, messages_json=excluded.messages_json,
               turns=excluded.turns, requests=excluded.requests, images=excluded.images,
               updated_at=excluded.updated_at
               WHERE owner_session=excluded.owner_session""",
            (state.conversation_id, state.session_id, state.conversation_title, state.model,
             json.dumps(state.history, ensure_ascii=False), json.dumps(state.display_messages, ensure_ascii=False),
             state.turns, state.requests, state.image_count, state.created_at, now),
        )
        conn.commit()
    state.last_active = now


def get_session(session_id: Optional[str], conversation_id: Optional[str] = None) -> WebSession:
    normalized = _valid_uuid(session_id)
    conv_id = _valid_uuid(conversation_id) if conversation_id else str(uuid.uuid4())
    with sessions_lock:
        state = sessions.get(normalized)
        if state is None:
            state = WebSession(session_id=normalized)
            sessions[normalized] = state
    with state.lock:
        if state.conversation_id != conv_id:
            saved = _load_conversation(normalized, conv_id)
            state.conversation_id = conv_id
            state.conversation_title = saved["title"]
            try:
                state.model = _normalise_panel_model(saved["model"])
            except HTTPException:
                state.model = _get_default_model(normalized)
            state.history = saved["history"]
            state.display_messages = saved["messages"]
            state.turns = saved["turns"]
            state.requests = saved["requests"]
            state.image_count = saved["images"]
            state.created_at = saved["created_at"]
    return state


_STOP_TOKEN_RE = re.compile(r"<\|(?:im_end|endoftext)\|>", re.IGNORECASE)
_STOP_TOKENS = ("<|im_end|>", "<|endoftext|>")


def clean_stop_tokens(text: str) -> str:
    """Remove model control tokens before text is streamed or persisted."""
    return _STOP_TOKEN_RE.sub("", str(text or ""))


def clean_stream_deltas(chunks):
    """Filter stop tokens even when the provider splits one across deltas."""
    pending = ""
    for chunk in chunks:
        pending += str(chunk or "")
        while True:
            match = _STOP_TOKEN_RE.search(pending)
            if match:
                before = pending[:match.start()]
                if before:
                    yield before
                pending = pending[match.end():]
                continue
            hold = 0
            for token in _STOP_TOKENS:
                limit = min(len(token) - 1, len(pending))
                for size in range(limit, 0, -1):
                    if pending.endswith(token[:size]):
                        hold = max(hold, size)
                        break
            emit = pending[:-hold] if hold else pending
            if emit:
                yield emit
            pending = pending[-hold:] if hold else ""
            break
    tail = clean_stop_tokens(pending)
    if tail:
        yield tail


def ndjson(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


class ModelUpdate(BaseModel):
    model: str = Field(min_length=1, max_length=160)


class SettingsUpdate(BaseModel):
    proxy: Optional[str] = Field(default=None, max_length=500)


class ProviderConfigUpdate(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    base_url: Optional[str] = Field(default=None, max_length=500)
    model: str = Field(min_length=1, max_length=160)
    api_key: Optional[str] = Field(default=None, max_length=4000)
    clear_api_key: bool = False


app = FastAPI(title="Neo AI Terminal", version="2.6.2")
app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")
# Vazir is installed locally by npm, so Persian text does not depend on a CDN.
VAZIR_DIR = APP_DIR / "node_modules" / "vazir-font" / "dist"
app.mount("/fonts", StaticFiles(directory=VAZIR_DIR, check_dir=False), name="fonts")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")


@app.get("/")
def dashboard():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    with sessions_lock:
        session_count = len(sessions)
    return {
        "ok": True,
        "service": "Neo AI Terminal",
        "version": "2.6.2",
        "engine": "Duck.ai Free in-panel chat + image generation + optional official API",
        "sessions": session_count,
        "uptime": int(time.time() - APP_STARTED),
    }


@app.get("/api/models")
def list_models():
    return {"models": _combined_model_catalog()}


@app.get("/api/duckai/catalog")
def get_duckai_catalog():
    """Return the full Duck.ai catalogue; six Free models are selectable in-panel."""
    return duckai_catalog.get_catalog()


@app.get("/api/provider/config")
def get_provider_config():
    config = _get_provider_config()
    info = api_providers.PROVIDER_INFO[config["provider"]]
    return {
        "provider": config["provider"], "provider_label": info["label"],
        "base_url": config["base_url"], "model": config["model"],
        "has_api_key": bool(config.get("secret_value")),
        "providers": [{"id": key, "label": value["label"], "base_url": value["base_url"], "model": value["model"]}
                      for key, value in api_providers.PROVIDER_INFO.items()],
    }


@app.post("/api/provider/config")
def save_provider_config(data: ProviderConfigUpdate):
    try:
        _save_provider_config(data.provider, data.base_url or "", data.model, data.api_key, data.clear_api_key)
    except (secure_store.SecretStoreError, api_providers.ProviderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    config = _get_provider_config()
    return {"ok": True, "provider": config["provider"], "model": config["model"],
            "base_url": config["base_url"], "has_api_key": bool(config.get("secret_value"))}


@app.post("/api/provider/test")
def test_provider_connection():
    config = _get_provider_config()
    try:
        key = _provider_api_key(config)
        return api_providers.test_connection(config["provider"], key, config["base_url"], config["model"])
    except (secure_store.SecretStoreError, api_providers.ProviderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/state")
def get_state(x_session_id: str = Header(..., alias="X-Session-ID"), x_conversation_id: str = Header(..., alias="X-Conversation-ID")):
    state = get_session(x_session_id, x_conversation_id)
    with state.lock:
        return {
            "model": state.model,
            "default_model": _get_default_model(state.session_id),
            "turns": state.turns,
            "requests": state.requests,
            "images": state.image_count,
            "history_count": len(state.history),
            "conversation_id": state.conversation_id,
            "conversation_title": state.conversation_title,
            "uptime": int(time.time() - state.created_at),
            "proxy_enabled": bool(state.proxy),
            "provider": _get_provider_config()["provider"],
            "provider_model": _get_provider_config()["model"],
            "api_configured": bool(_get_provider_config().get("secret_value")),
            "activity": list(state.activity),
        }


@app.get("/api/conversations")
def list_conversations(x_session_id: str = Header(..., alias="X-Session-ID")):
    owner = _valid_uuid(x_session_id)
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id,title,model,turns,created_at,updated_at FROM conversations WHERE owner_session=? ORDER BY updated_at DESC LIMIT 80",
            (owner,),
        ).fetchall()
    return {"conversations": [dict(row) for row in rows]}


@app.get("/api/conversation")
def get_conversation(x_session_id: str = Header(..., alias="X-Session-ID"), x_conversation_id: str = Header(..., alias="X-Conversation-ID")):
    state = get_session(x_session_id, x_conversation_id)
    with state.lock:
        return {"id": state.conversation_id, "title": state.conversation_title,
                "model": state.model, "default_model": _get_default_model(state.session_id),
                "messages": state.display_messages, "turns": state.turns}


@app.post("/api/conversations/new")
def new_conversation(x_session_id: str = Header(..., alias="X-Session-ID")):
    owner = _valid_uuid(x_session_id)
    new_id = str(uuid.uuid4())
    now = time.time()
    default_model = _get_default_model(owner)
    with DB_LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO conversations (id,owner_session,title,model,history_json,messages_json,turns,requests,images,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (new_id, owner, "New conversation", default_model, "[]", "[]", 0, 0, 0, now, now),
        )
        conn.commit()
    return {"ok": True, "conversation_id": new_id}


@app.post("/api/model")
def set_model(data: ModelUpdate, x_session_id: str = Header(..., alias="X-Session-ID"), x_conversation_id: str = Header(..., alias="X-Conversation-ID")):
    state = get_session(x_session_id, x_conversation_id)
    model = _normalise_panel_model(data.model)
    with state.lock:
        state.model = model
        _set_default_model(state.session_id, model)
        state.add_activity("model", f"Model changed to {model}")
        _save_conversation(state)
    return {"ok": True, "model": model, "default_model": model}


@app.post("/api/settings")
def update_settings(data: SettingsUpdate, x_session_id: str = Header(..., alias="X-Session-ID"), x_conversation_id: str = Header(..., alias="X-Conversation-ID")):
    state = get_session(x_session_id, x_conversation_id)
    proxy = (data.proxy or "").strip() or None
    if proxy and not proxy.startswith(("http://", "https://", "socks5://", "socks5h://")):
        raise HTTPException(status_code=400, detail="Proxy must start with http://, https://, socks5:// or socks5h://")
    with state.lock:
        # This proxy setting is retained only for the legacy CLI. Official API
        # chat intentionally connects to the provider URL directly.
        state.proxy = proxy
        state.client = None
        state.add_activity("settings", "Legacy CLI proxy setting updated")
    return {"ok": True, "proxy_enabled": bool(proxy)}


@app.post("/api/clear")
def clear_chat(x_session_id: str = Header(..., alias="X-Session-ID"), x_conversation_id: str = Header(..., alias="X-Conversation-ID")):
    state = get_session(x_session_id, x_conversation_id)
    with state.lock:
        state.history.clear()
        state.display_messages.clear()
        state.conversation_title = "New conversation"
        state.add_activity("clear", "Conversation cleared")
        _save_conversation(state)
    return {"ok": True}


@app.post("/api/chat")
async def chat(
    prompt: str = Form(...),
    model: Optional[str] = Form(default=None),
    reasoning_effort: Optional[str] = Form(default=None),
    attachments: list[UploadFile] = File(default=[]),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_conversation_id: str = Header(..., alias="X-Conversation-ID"),
):
    state = get_session(x_session_id, x_conversation_id)
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Write a message first")
    if len(prompt) > 30_000:
        raise HTTPException(status_code=413, detail="Message is too long")
    panel_model = _normalise_panel_model(model or state.model)
    is_duckai = panel_model.startswith("duckai:")
    if is_duckai:
        selected_model = _duckai_model_id(panel_model)
        provider_config = None
        provider_api_key = None
        duck_profile = duckai_catalog.get_reasoning_profile(selected_model)
        duck_options = duck_profile.get("options", [])
        if not duck_profile.get("supports"):
            # Ignore stale UI/localStorage values for models without reasoning.
            reasoning_effort = None
        else:
            reasoning_effort = reasoning_effort or duck_profile.get("default")
            if reasoning_effort not in duck_options:
                raise HTTPException(status_code=400, detail="Unsupported reasoning level for this Duck.ai model")
    else:
        provider_config = _get_provider_config()
        selected_model = provider_config["model"]
        try:
            provider_api_key = _provider_api_key(provider_config)
        except secure_store.SecretStoreError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not provider_api_key:
            raise HTTPException(status_code=400, detail="The optional official API model is not configured. Add its API key in Settings or select a Duck.ai Free model.")
        profile = _available_model_catalog()[0]["reasoning"]
        if profile.get("options"):
            reasoning_effort = reasoning_effort or profile["default"]
            if reasoning_effort not in profile["options"]:
                raise HTTPException(status_code=400, detail="Unsupported reasoning level for this API model")
            if reasoning_effort == "none":
                reasoning_effort = None
        else:
            reasoning_effort = None

    image_parts: list[dict] = []
    prompt_extra = ""
    temp_paths: list[str] = []
    attachment_names: list[str] = []
    total_upload_bytes = 0
    if len(attachments) > 8:
        raise HTTPException(status_code=413, detail="You can attach up to 8 files per message")
    try:
        for upload in attachments:
            raw = await upload.read()
            if not raw:
                raise HTTPException(status_code=400, detail=f"{upload.filename or 'File'} is empty")
            total_upload_bytes += len(raw)
            if len(raw) > 12 * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"{upload.filename or 'File'} exceeds 12 MB")
            if total_upload_bytes > 24 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Combined attachments exceed 24 MB")
            filename = Path(upload.filename or "attachment").name
            attachment_names.append(filename)
            suffix = Path(filename).suffix[:16]
            fd, tmp_path = tempfile.mkstemp(prefix="neo_upload_", suffix=suffix)
            os.close(fd)
            Path(tmp_path).write_bytes(raw)
            temp_paths.append(tmp_path)
            content_type = (upload.content_type or "").lower()
            is_image = content_type.startswith("image/") or suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
            if is_image:
                try:
                    image_parts.append(duck_cli.image_to_data_url(tmp_path))
                except Exception as exc:
                    raise HTTPException(status_code=400, detail=f"Could not read image '{filename}': {exc}") from exc
            else:
                prompt_extra += duck_cli.file_to_prompt_chunk(tmp_path)
    except Exception as exc:
        for path in temp_paths:
            try: os.remove(path)
            except OSError: pass
        if isinstance(exc, HTTPException): raise
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def generate():
        with state.lock:
            answer_parts: list[str] = []
            engine_name = "Duck.ai" if is_duckai else provider_config["provider"]
            yield ndjson({"type": "start", "model": panel_model, "provider": engine_name, "engine": "duckai" if is_duckai else "official_api"})
            try:
                if is_duckai:
                    stream = state.get_client().stream(
                        prompt, model=selected_model, history=state.history,
                        images=image_parts or None, prompt_extra=prompt_extra,
                        reasoning_effort=reasoning_effort,
                    )
                else:
                    stream = api_providers.stream_chat(
                        provider=provider_config["provider"], api_key=provider_api_key,
                        base_url=provider_config["base_url"], model=selected_model,
                        history=state.history, prompt=prompt, prompt_extra=prompt_extra,
                        images=image_parts or None, reasoning_effort=reasoning_effort,
                    )
                for delta in clean_stream_deltas(stream):
                    answer_parts.append(delta)
                    yield ndjson({"type": "delta", "text": delta})
                answer = clean_stop_tokens("".join(answer_parts))
                if not answer.strip():
                    raise RuntimeError("The selected engine returned an empty response.")
                user_content = [{"type": "text", "text": prompt + prompt_extra}]
                user_content.extend(image_parts)
                state.history.append({"role": "user", "content": user_content})
                state.history.append({"role": "assistant", "content": answer})
                state.display_messages.append({"role": "user", "text": prompt, "attachments": attachment_names, "timestamp": time.time(), "model": panel_model})
                state.display_messages.append({"role": "assistant", "text": answer, "timestamp": time.time(), "model": panel_model})
                if state.conversation_title == "New conversation":
                    compact_title = " ".join(prompt.split())
                    state.conversation_title = (compact_title[:52] + "…") if len(compact_title) > 52 else (compact_title or "New conversation")
                state.turns += 1
                state.requests += 1
                state.model = panel_model
                _set_default_model(state.session_id, panel_model)
                state.add_activity("chat", f"{engine_name}: {prompt}")
                _save_conversation(state)
                yield ndjson({"type": "done", "text": answer, "turns": state.turns})
            except Exception as exc:
                message = str(exc)
                lowered = message.lower()
                phase = getattr(exc, "phase", None)
                status = getattr(exc, "status", None)
                if status == 418 and phase == "challenge":
                    message = "Duck.ai returned HTTP 418 while issuing the handshake challenge. The chat request was not sent because no challenge token was received."
                elif status == 418 and phase == "chat_http":
                    message = "Duck.ai returned HTTP 418 to the chat request after the client's bounded fresh-handshake retries. The upstream service is still rejecting this session."
                elif status == 418 and phase == "chat_sse":
                    message = "Duck.ai accepted the connection but sent an HTTP 418 ERR_CHALLENGE event in the response stream."
                elif "err_challenge" in lowered or "duckchat" in lowered or ("418" in lowered and "challenge" in lowered):
                    message = "Duck.ai rejected the request with HTTP 418 (ERR_CHALLENGE). Check whether the failure happened during challenge issuance or chat streaming in the server log."
                elif "err_country_not_supported" in lowered or "451" in lowered:
                    message = "Duck.ai rejected this request with HTTP 451 (ERR_COUNTRY_NOT_SUPPORTED). The service is refusing this connection based on its regional access check."
                state.add_activity("error", message)
                yield ndjson({"type": "error", "message": message})
            finally:
                for path in temp_paths:
                    try: os.remove(path)
                    except OSError: pass

    return StreamingResponse(generate(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/draw")
def draw(
    prompt: str = Form(...),
    model: Optional[str] = Form(default=None),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_conversation_id: str = Header(..., alias="X-Conversation-ID"),
):
    state = get_session(x_session_id, x_conversation_id)
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Enter an image prompt")
    if len(prompt) > 8_000:
        raise HTTPException(status_code=413, detail="Prompt is too long")
    panel_model = _normalise_panel_model(model or state.model)
    model_id = _duckai_model_id(panel_model)
    try:
        with state.lock:
            path, assistant_text, info = state.get_client().generate_image(
                prompt, model=model_id, out_dir=str(GENERATED_DIR), history=state.history,
            )
            image_format = str(info.get("format", "jpeg")).lower()
            mime = "image/png" if image_format == "png" else "image/jpeg"
            image_url = f"/generated/{Path(path).name}"
            state.history.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
            state.history.append({"role": "assistant", "content": assistant_text or "Image generated."})
            state.display_messages.append({"role": "user", "text": prompt, "timestamp": time.time(), "model": panel_model})
            state.display_messages.append({"role": "assistant", "text": assistant_text or "", "image_url": image_url, "timestamp": time.time(), "model": panel_model})
            if state.conversation_title == "New conversation":
                title = " ".join(prompt.split())
                state.conversation_title = (title[:52] + "…") if len(title) > 52 else title
            state.model = panel_model
            state.turns += 1
            state.requests += 1
            state.image_count += 1
            _set_default_model(state.session_id, panel_model)
            state.add_activity("image", prompt)
            _save_conversation(state)
            return {"ok": True, "text": assistant_text, "image": f"data:{mime};base64,{info['b64']}",
                    "image_url": image_url, "width": info.get("width"), "height": info.get("height"),
                    "filename": Path(path).name, "model": panel_model, "turns": state.turns}
    except Exception as exc:
        state.add_activity("error", str(exc))
        lowered = str(exc).lower()
        phase = getattr(exc, "phase", None)
        status = getattr(exc, "status", None)
        if status == 418 and phase == "challenge":
            detail = "Duck.ai returned HTTP 418 during image-request handshake; no chat/image request was sent because no challenge token was issued."
        elif status == 418 and phase == "chat_http":
            detail = "Duck.ai returned HTTP 418 to the image-generation request after the client's bounded fresh-handshake retries."
        elif "err_challenge" in lowered or "418" in lowered:
            detail = "Duck.ai rejected image generation with HTTP 418 (ERR_CHALLENGE)."
        elif "err_country_not_supported" in lowered or "451" in lowered:
            detail = "Duck.ai refused image generation for this connection with HTTP 451 (country/region not supported)."
        else:
            detail = str(exc)
        raise HTTPException(status_code=502, detail=detail) from exc


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    model: Optional[str] = Form(default=None),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_conversation_id: str = Header(..., alias="X-Conversation-ID"),
):
    state = get_session(x_session_id, x_conversation_id)
    raw = await audio.read()
    if not raw or len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file is empty or larger than 25 MB")
    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"
    fd, tmp_path = tempfile.mkstemp(prefix="neo_audio_", suffix=suffix)
    os.close(fd)
    Path(tmp_path).write_bytes(raw)
    try:
        model_id = _duckai_model_id(_normalise_panel_model(model or state.model))
        transcript = await run_in_threadpool(duck_voice.transcribe_file, state.get_client(), tmp_path, model_id)
        state.requests += 1
        state.add_activity("voice", f"Audio transcribed: {audio.filename or 'recording'}")
        return {"ok": True, "text": transcript}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        try: os.remove(tmp_path)
        except OSError: pass


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the Neo AI Terminal dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    parser.add_argument("--reload", action="store_true", help="Enable development reload")
    args = parser.parse_args()
    uvicorn.run("web_app:app", host=args.host, port=args.port, reload=args.reload)
