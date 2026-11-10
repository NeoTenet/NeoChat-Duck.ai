"""Official API adapters used by Neo AI Terminal's hybrid mode.

Supported: OpenAI Chat Completions, Anthropic Messages, Gemini streamGenerateContent,
and custom OpenAI-compatible endpoints. Uses `requests` only; API keys stay server-side.
"""
from __future__ import annotations

import base64
import json
import re
from typing import Iterable, Iterator
from urllib.parse import quote, urlparse

import requests

PROVIDER_INFO = {
    "openai": {
        "label": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
        "kind": "openai",
    },
    "anthropic": {
        "label": "Anthropic API",
        "base_url": "https://api.anthropic.com",
        "model": "claude-haiku-5-5",
        "kind": "anthropic",
    },
    "gemini": {
        "label": "Google Gemini API",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-3.8-flash",
        "kind": "gemini",
    },
    "openai_compatible": {
        "label": "OpenAI-compatible API",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "enter-model-id",
        "kind": "openai",
    },
}


class ProviderError(RuntimeError):
    pass


MODEL_ALIASES = {
    "anthropic": {
        # 2.1.3 mistakenly downgraded the current Haiku 5.5 selection to this
        # pinned 4.5 snapshot. Auto-upgrade that exact stored value so users
        # regain Haiku 5.5's documented effort selector without reconfiguring.
        "claude-haiku-4-5-20251001": "claude-haiku-5-5",
    }
}


def anthropic_effort_options(model: str) -> list[str]:
    """Return only effort levels documented for this Anthropic model family."""
    value = (model or "").lower().strip()
    all_levels = ["low", "medium", "high", "xhigh", "max"]
    # Current fifth-generation models expose the effort parameter. Haiku 5.5
    # supports all five levels; adaptive thinking is enabled by default.
    if value in {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5",
                 "claude-sonnet-5", "claude-opus-5"}:
        return all_levels
    if any(value == name or value.startswith(name + "-") for name in (
        "claude-opus-4-8", "claude-opus-4-7"
    )):
        return all_levels
    # Opus 4.6 and Sonnet 4.6 support max, but not xhigh.
    if any(value == name or value.startswith(name + "-") for name in (
        "claude-opus-4-6", "claude-sonnet-4-6"
    )):
        return ["low", "medium", "high", "max"]
    # Haiku 4.5 and Sonnet 4.5 do not expose the effort parameter.
    return []

def normalize_model_id(provider: str, model: str) -> str:
    value = (model or "").strip()
    aliases = MODEL_ALIASES.get(provider, {})
    return aliases.get(value.lower(), value)


def _safe_error(response: requests.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            serialized = json.dumps(body, ensure_ascii=False).lower()
            if "duckchat" in serialized or "err_challenge" in serialized:
                return (
                    "The configured endpoint returned Duck.ai's private challenge response, not a standard provider API response. "
                    "Use the official Anthropic Base URL https://api.anthropic.com for Claude, or the official URL for your selected provider."
                )
            error = body.get("error", body)
            if isinstance(error, dict):
                message = error.get("message") or error.get("detail") or error.get("type")
                if message:
                    return str(message)[:700]
            if isinstance(error, str):
                return error[:700]
    except Exception:
        pass
    return (response.text or f"HTTP {response.status_code}")[:700]


def _messages_from_history(history: list, prompt: str, prompt_extra: str, images: list, kind: str):
    records = []
    for entry in history or []:
        role = entry.get("role", "user")
        content = entry.get("content", "")
        text_parts = []
        image_parts = []
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
                elif part.get("type") in {"image", "image_url"}:
                    url = part.get("image") or part.get("url")
                    if not url and isinstance(part.get("image_url"), dict):
                        url = part["image_url"].get("url")
                    if url:
                        image_parts.append(str(url))
        elif content is not None:
            text_parts.append(str(content))
        text = "\n".join(part for part in text_parts if part)
        if role == "assistant":
            records.append({"role": "assistant", "text": text})
        else:
            records.append({"role": "user", "text": text, "images": image_parts})
    current_images = []
    for image in images or []:
        if isinstance(image, dict):
            value = image.get("image") or image.get("url")
            if value:
                current_images.append(str(value))
    records.append({"role": "user", "text": (prompt + (prompt_extra or "")).strip(), "images": current_images})
    return records


def _image_url_to_parts(data_url: str):
    match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", data_url, re.S)
    if not match:
        raise ProviderError("Image attachment format is not supported. Please use PNG, JPEG or WEBP.")
    return match.group(1), match.group(2)


def _openai_messages(records: list):
    messages = []
    for row in records:
        images = row.get("images") or []
        if not images:
            messages.append({"role": row["role"], "content": row.get("text", "")})
            continue
        content = [{"type": "text", "text": row.get("text", "") or " "}]
        for data_url in images:
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        messages.append({"role": row["role"], "content": content})
    return messages


def _anthropic_messages(records: list):
    messages = []
    for row in records:
        content = []
        if row.get("text"):
            content.append({"type": "text", "text": row["text"]})
        for data_url in row.get("images", []):
            media_type, data = _image_url_to_parts(data_url)
            content.append({"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}})
        if not content:
            content = [{"type": "text", "text": " "}]
        messages.append({"role": "assistant" if row["role"] == "assistant" else "user", "content": content})
    # Anthropic expects user/assistant turns to alternate. Existing saved histories are alternating.
    return messages


def _gemini_contents(records: list):
    contents = []
    for row in records:
        parts = []
        if row.get("text"):
            parts.append({"text": row["text"]})
        for data_url in row.get("images", []):
            media_type, data = _image_url_to_parts(data_url)
            parts.append({"inlineData": {"mimeType": media_type, "data": data}})
        if not parts:
            parts = [{"text": " "}]
        contents.append({"role": "model" if row["role"] == "assistant" else "user", "parts": parts})
    return contents


def is_duckai_url(base_url: str) -> bool:
    """Return True for Duck.ai/DuckDuckGo web endpoints, never valid API bases."""
    try:
        parsed = urlparse((base_url or "").strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            host == "duck.ai" or host.endswith(".duck.ai")
            or host == "duckduckgo.com" or host.endswith(".duckduckgo.com")
            or host == "duck.com" or host.endswith(".duck.com")
            or "/duckchat" in (parsed.path or "").lower()
        )
    except Exception:
        return False


def validate_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip().rstrip("/")
    parsed = urlparse(base_url)
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if not parsed.hostname or parsed.username or parsed.password:
        raise ProviderError("API Base URL is invalid.")
    if is_duckai_url(base_url):
        raise ProviderError(
            "This address belongs to Duck.ai's private web interface, not an official API. "
            "Choose the official provider URL in Settings. Duck.ai is opened separately for manual use."
        )
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in local_hosts):
        raise ProviderError("API Base URL must use HTTPS (HTTP is allowed only for localhost).")
    return base_url


def _validate_base_url(base_url: str) -> str:
    return validate_base_url(base_url)


def _endpoint(base_url: str, suffix: str) -> str:
    base_url = _validate_base_url(base_url)
    path = urlparse(base_url).path.rstrip("/")
    # Accept either provider root or a base URL that already includes /v1.
    if path.endswith(suffix):
        return base_url
    if suffix.startswith("/v1/") and path.endswith("/v1"):
        return base_url + suffix[3:]
    return base_url + suffix


def _sse_lines(response: requests.Response) -> Iterator[str]:
    for raw in response.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", "replace")
        line = raw.strip()
        if line.startswith("data:"):
            yield line[5:].strip()


def stream_chat(provider: str, api_key: str, base_url: str, model: str,
                history: list, prompt: str, prompt_extra: str = "", images: list | None = None,
                reasoning_effort: str | None = None) -> Iterator[str]:
    if provider not in PROVIDER_INFO:
        raise ProviderError("Unknown API provider")
    if not api_key:
        raise ProviderError("API key is not configured. Open Settings → API provider and save your key.")
    model = (model or "").strip()
    if not model:
        raise ProviderError("Enter a model ID in Settings before sending a message.")
    kind = PROVIDER_INFO[provider]["kind"]
    records = _messages_from_history(history, prompt, prompt_extra, images or [], kind)

    try:
        if kind == "openai":
            url = _endpoint(base_url, "/chat/completions")
            payload = {"model": model, "messages": _openai_messages(records), "stream": True}
            # Reasoning effort is only attached to recognizable reasoning-model families.
            if provider == "openai" and re.match(r"^(gpt-(5|6)|o[134])", model, re.I) and reasoning_effort in {"low", "medium", "high"}:
                payload["reasoning_effort"] = reasoning_effort
            with requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, stream=True, timeout=(20, 180)) as response:
                if response.status_code >= 400:
                    raise ProviderError(f"{PROVIDER_INFO[provider]['label']} returned HTTP {response.status_code}: {_safe_error(response)}")
                for data in _sse_lines(response):
                    if data == "[DONE]":
                        break
                    try:
                        packet = json.loads(data)
                        delta = packet.get("choices", [{}])[0].get("delta", {}).get("content")
                        if isinstance(delta, str) and delta:
                            yield delta
                        elif isinstance(delta, list):
                            for part in delta:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    yield part.get("text", "")
                    except json.JSONDecodeError:
                        continue
            return

        if kind == "anthropic":
            url = _endpoint(base_url, "/v1/messages")
            normalized_model = model.lower()
            supported_efforts = anthropic_effort_options(normalized_model)
            effort = reasoning_effort if reasoning_effort in supported_efforts else None
            if reasoning_effort and not effort:
                if not supported_efforts:
                    raise ProviderError(
                        f"The selected Anthropic model ({model}) does not support the effort parameter. "
                        "Choose Claude Haiku 5.5, a supported Sonnet/Opus model, or use model-managed reasoning."
                    )
                raise ProviderError(
                    f"The selected Claude model ({model}) does not support '{reasoning_effort}'. "
                    f"Available levels: {', '.join(supported_efforts)}."
                )
            # Claude 5.5 models support up to 128K output tokens. Legacy models
            # use conservative limits to avoid rejecting requests unnecessarily.
            if normalized_model in {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"}:
                max_tokens = 128000 if effort in {"xhigh", "max"} else 32768
            else:
                max_tokens = {None: 8192, "low": 8192, "medium": 16384, "high": 32768,
                              "xhigh": 65536, "max": 65536}[effort]
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": _anthropic_messages(records),
                "stream": True,
            }
            if effort:
                # Claude 4.6-4.8 uses adaptive thinking when explicitly enabled.
                # Claude 5+ (including Haiku/Sonnet/Opus 5.5) has adaptive
                # thinking on by default; omit the thinking field and steer it
                # through output_config.effort only.
                if normalized_model.startswith(("claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8", "claude-sonnet-4-6")):
                    payload["thinking"] = {"type": "adaptive"}
                payload["output_config"] = {"effort": effort}
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=(20, 180)) as response:
                if response.status_code >= 400:
                    raise ProviderError(f"Anthropic returned HTTP {response.status_code}: {_safe_error(response)}")
                for data in _sse_lines(response):
                    try:
                        packet = json.loads(data)
                        if packet.get("type") == "content_block_delta":
                            delta = packet.get("delta", {}).get("text")
                            if delta:
                                yield delta
                        elif packet.get("type") == "error":
                            raise ProviderError(str(packet.get("error", {}).get("message", "Anthropic stream error")))
                    except json.JSONDecodeError:
                        continue
            return

        # Google Gemini REST streaming API.
        base = _validate_base_url(base_url or PROVIDER_INFO[provider]["base_url"])
        safe_model = quote(model.removeprefix("models/"), safe="-_.")
        url = f"{base}/models/{safe_model}:streamGenerateContent?alt=sse"
        payload = {"contents": _gemini_contents(records)}
        if reasoning_effort in {"low", "medium", "high"}:
            payload["generationConfig"] = {"thinkingConfig": {"thinkingLevel": reasoning_effort}}
        with requests.post(url, headers={"x-goog-api-key": api_key, "content-type": "application/json"}, json=payload, stream=True, timeout=(20, 180)) as response:
            if response.status_code >= 400:
                raise ProviderError(f"Gemini returned HTTP {response.status_code}: {_safe_error(response)}")
            for data in _sse_lines(response):
                try:
                    packet = json.loads(data)
                    for candidate in packet.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            text = part.get("text")
                            if text:
                                yield text
                except json.JSONDecodeError:
                    continue
    except requests.Timeout as exc:
        raise ProviderError("The provider request timed out. Check your connection and try again.") from exc
    except requests.RequestException as exc:
        raise ProviderError(f"Could not connect to the selected API provider: {exc}") from exc


def test_connection(provider: str, api_key: str, base_url: str, model: str) -> dict:
    if provider not in PROVIDER_INFO:
        raise ProviderError("Unknown API provider")
    if not api_key or not model:
        raise ProviderError("Save an API key and model ID first")
    kind = PROVIDER_INFO[provider]["kind"]
    try:
        if kind == "openai":
            url = _endpoint(base_url, "/chat/completions")
            payload = {"model": model, "messages": [{"role": "user", "content": "Reply with OK."}], "max_completion_tokens": 8, "stream": False}
            response = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=(15, 45))
        elif kind == "anthropic":
            url = _endpoint(base_url, "/v1/messages")
            payload = {"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": "Reply with OK."}]}
            response = requests.post(url, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}, json=payload, timeout=(15, 45))
        else:
            base = _validate_base_url(base_url or PROVIDER_INFO[provider]["base_url"])
            safe_model = quote(model.removeprefix("models/"), safe="-_.")
            url = f"{base}/models/{safe_model}:generateContent"
            payload = {"contents": [{"role": "user", "parts": [{"text": "Reply with OK."}]}], "generationConfig": {"maxOutputTokens": 8}}
            response = requests.post(url, headers={"x-goog-api-key": api_key}, json=payload, timeout=(15, 45))
        if response.status_code >= 400:
            raise ProviderError(f"HTTP {response.status_code}: {_safe_error(response)}")
        return {"ok": True, "provider": PROVIDER_INFO[provider]["label"], "model": model}
    except requests.Timeout as exc:
        raise ProviderError("Connection test timed out") from exc
    except requests.RequestException as exc:
        raise ProviderError(f"Connection test failed: {exc}") from exc
