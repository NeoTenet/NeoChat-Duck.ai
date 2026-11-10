"""Duck.ai catalogue used by the Neo AI Terminal in-panel engine.

The six free text models are mapped to the original unofficial DuckAI client.
Duck.ai does not offer a supported public API; this integration uses its
undocumented web interface and can be affected by upstream challenges.
"""
from __future__ import annotations

DUCKAI_MODELS = [
    {"id":"duckai:claude-haiku-5-5", "model_id":"claude-haiku-5-5", "key":"haiku", "name":"Claude Haiku 5.5", "provider":"Anthropic", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    {"id":"duckai:mistral-small-2603", "model_id":"mistral-small-2603", "key":"mistral", "name":"Mistral Small 4", "provider":"Mistral AI", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    {"id":"duckai:gpt-6-luna", "model_id":"gpt-6-luna", "key":"luna", "name":"GPT-6 Luna", "provider":"OpenAI", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    {"id":"duckai:gpt-5.4-mini", "model_id":"gpt-5.4-mini", "key":"mini", "name":"GPT-5.4 mini", "provider":"OpenAI", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    {"id":"duckai:tinfoil/gpt-oss-120b", "model_id":"tinfoil/gpt-oss-120b", "key":"oss", "name":"gpt-oss-120b", "provider":"Tinfoil.sh", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    {"id":"duckai:tinfoil/gemma4-31b", "model_id":"tinfoil/gemma4-31b", "key":"gemma", "name":"Gemma 4 31B", "provider":"Tinfoil.sh", "plan":"Free", "tier":"free", "engine":"duckai", "reasoning":False},
    # These are catalogued for information, but never presented as Free models.
    {"id":"duckai:gpt-5.6-terra", "model_id":"gpt-5.6-terra", "key":"terra", "name":"GPT-5.6 Terra", "provider":"OpenAI", "plan":"Plus", "tier":"plus", "engine":"duckai", "reasoning":False},
    {"id":"duckai:claude-sonnet-5-5", "model_id":"claude-sonnet-5-5", "key":"sonnet", "name":"Claude Sonnet 5.5", "provider":"Anthropic", "plan":"Plus", "tier":"plus", "engine":"duckai", "reasoning":False},
    {"id":"duckai:claude-opus-5-5", "model_id":"claude-opus-5-5", "key":"opus", "name":"Claude Opus 5.5", "provider":"Anthropic", "plan":"Pro", "tier":"pro", "engine":"duckai", "reasoning":False},
    {"id":"duckai:gpt-5.6-sol", "model_id":"gpt-5.6-sol", "key":"sol", "name":"GPT-5.6 Sol", "provider":"OpenAI", "plan":"Pro", "tier":"pro", "engine":"duckai", "reasoning":False},
]

DUCKAI_TOOLS = [
    {"key":"image-creation", "name":"AI Image Creation", "provider":"Duck.ai", "kind":"image", "availability":"Image generation from the dashboard"},
    {"key":"dictation", "name":"Voice Dictation / Transcription", "provider":"Duck.ai", "kind":"audio", "availability":"Audio transcription from the dashboard"},
]

# DuckDuckGo's public model guide marks which Free models have a reasoning
# mode and which additionally expose Extended Reasoning. The private web client
# accepts `reasoningEffort` only for models listed in this capability map.
# Mistral Small 4 is intentionally omitted: it does not advertise reasoning.
DUCKAI_REASONING = {
    "claude-haiku-5-5": {"supports": True, "options": ["none", "low", "medium"], "default": "medium", "extended": False},
    "gpt-6-luna": {"supports": True, "options": ["none", "low", "medium"], "default": "medium", "extended": False},
    "gpt-5.4-mini": {"supports": True, "options": ["none", "low", "medium", "high"], "default": "medium", "extended": True},
    "tinfoil/gpt-oss-120b": {"supports": True, "options": ["none", "low", "medium"], "default": "low", "extended": False},
    "tinfoil/gemma4-31b": {"supports": True, "options": ["none", "low", "medium"], "default": "medium", "extended": False},
}

FREE_MODELS = [dict(item) for item in DUCKAI_MODELS if item["tier"] == "free"]
FREE_MODEL_IDS = {item["model_id"] for item in FREE_MODELS}
_FREE_BY_ID = {item["id"]: item for item in FREE_MODELS}
_FREE_BY_MODEL = {item["model_id"]: item for item in FREE_MODELS}

# Compatibility aliases accepted by the panel/CLI. These are NOT sent upstream;
# they are normalized to the current canonical Duck.ai model IDs above.
DUCKAI_MODEL_ALIASES = {
    "gpt-4o-mini": "gpt-5.4-mini",
    "gpt-4o": "gpt-5.4-mini",
    "claude-3-haiku": "claude-haiku-5-5",
    "claude-3-5-haiku": "claude-haiku-5-5",
    "mistral-small-4": "mistral-small-2603",
    "gpt-oss-120b": "tinfoil/gpt-oss-120b",
    "gemma-4-31b": "tinfoil/gemma4-31b",
}

def normalize_model_alias(value: str | None) -> str:
    """Normalize a common/legacy model name to its current Duck.ai model ID."""
    raw = (value or "").strip()
    if raw.startswith("duckai:"):
        raw = raw[7:]
    return DUCKAI_MODEL_ALIASES.get(raw.lower(), raw)


def get_reasoning_profile(model_id: str | None) -> dict:
    """Return a defensive copy of the Duck.ai reasoning capability profile."""
    profile = DUCKAI_REASONING.get((model_id or "").strip())
    if not profile:
        return {"supports": False, "options": [], "default": None, "extended": False}
    return {
        "supports": bool(profile["supports"]),
        "options": list(profile["options"]),
        "default": profile["default"],
        "extended": bool(profile.get("extended", False)),
    }


def get_free_models() -> list[dict]:
    return [dict(item) for item in FREE_MODELS]


def resolve_free_model(value: str | None) -> str:
    raw = normalize_model_alias(value)
    item = _FREE_BY_MODEL.get(raw)
    if not item:
        raise ValueError("This model is not in the six-model Duck.ai Free catalogue.")
    return item["model_id"]


def get_catalog() -> dict:
    return {
        "models": [
            {**dict(item), "reasoning": get_reasoning_profile(item["model_id"])}
            for item in DUCKAI_MODELS
        ],
        "free_models": get_free_models(),
        "tools": [dict(item) for item in DUCKAI_TOOLS],
        "access_note": "Free Duck.ai models are selected and used inside Neo AI Terminal through the retained unofficial DuckAi client. Duck.ai does not publish a supported public API; upstream challenges, service changes and daily limits may affect availability.",
    }
