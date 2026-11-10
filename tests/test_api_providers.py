"""Offline unit tests for provider request payloads; no real API key is needed."""
import unittest
from unittest.mock import patch

import api_providers


class FakeResponse:
    status_code = 200
    text = ""

    def __init__(self, lines):
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_lines(self, decode_unicode=True):
        yield from self.lines


class ProviderPayloadTests(unittest.TestCase):
    def _capture_payload(self, provider, base_url, model, effort, lines):
        with patch.object(api_providers.requests, "post", return_value=FakeResponse(lines)) as mocked:
            output = "".join(api_providers.stream_chat(
                provider=provider,
                api_key="unit-test-key",
                base_url=base_url,
                model=model,
                history=[],
                prompt="Say hello",
                reasoning_effort=effort,
            ))
        self.assertTrue(output)
        if provider == "anthropic":
            self.assertEqual(mocked.call_args.args[0], "https://api.anthropic.com/v1/messages")
        return mocked.call_args.kwargs["json"]

    def test_openai_reasoning_effort(self):
        payload = self._capture_payload(
            "openai", "https://api.openai.com/v1", "gpt-6-test", "high",
            ['data: {"choices":[{"delta":{"content":"hello"}}]}', "data: [DONE]"],
        )
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertTrue(payload["stream"])

    def test_anthropic_sonnet5_effort_max(self):
        payload = self._capture_payload(
            "anthropic", "https://api.anthropic.com", "claude-sonnet-5", "max",
            ['data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"hello"}}'],
        )
        # Sonnet 5 manages adaptive thinking by default; effort controls depth.
        self.assertNotIn("thinking", payload)
        self.assertEqual(payload["output_config"], {"effort": "max"})
        self.assertEqual(payload["max_tokens"], 65536)

    def test_anthropic_opus48_enables_adaptive_thinking(self):
        payload = self._capture_payload(
            "anthropic", "https://api.anthropic.com", "claude-opus-4-8", "high",
            ['data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"hello"}}'],
        )
        self.assertEqual(payload["thinking"], {"type": "adaptive"})
        self.assertEqual(payload["output_config"], {"effort": "high"})

    def test_haiku55_exposes_all_effort_levels_but_legacy_haiku45_does_not(self):
        self.assertEqual(
            api_providers.anthropic_effort_options("claude-haiku-5-5"),
            ["low", "medium", "high", "xhigh", "max"],
        )
        self.assertEqual(
            api_providers.anthropic_effort_options("claude-haiku-4-5-20251001"),
            [],
        )

    def test_anthropic_haiku55_accepts_high_xhigh_and_max(self):
        for level in ("high", "xhigh", "max"):
            with self.subTest(level=level):
                payload = self._capture_payload(
                    "anthropic", "https://api.anthropic.com", "claude-haiku-5-5", level,
                    ['data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"hello"}}'],
                )
                self.assertEqual(payload["output_config"], {"effort": level})
                self.assertNotIn("thinking", payload)  # Adaptive thinking is on by default.
                self.assertGreaterEqual(payload["max_tokens"], 32768)

    def test_anthropic_haiku45_does_not_accept_effort(self):
        with self.assertRaisesRegex(api_providers.ProviderError, "does not support the effort parameter"):
            list(api_providers.stream_chat(
                provider="anthropic", api_key="unit-test-key", base_url="https://api.anthropic.com",
                model="claude-haiku-4-5-20251001", history=[], prompt="Say hello", reasoning_effort="high",
            ))

    def test_gemini_thinking_level(self):
        payload = self._capture_payload(
            "gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-3.8-flash", "high",
            ['data: {"candidates":[{"content":{"parts":[{"text":"hello"}]}}]}'],
        )
        self.assertEqual(
            payload["generationConfig"]["thinkingConfig"]["thinkingLevel"], "high"
        )

    def test_openai_compatible_model_id(self):
        payload = self._capture_payload(
            "openai_compatible", "https://openrouter.ai/api/v1", "provider/model", None,
            ['data: {"choices":[{"delta":{"content":"hello"}}]}', "data: [DONE]"],
        )
        self.assertEqual(payload["model"], "provider/model")

    def test_rejects_lookalike_localhost_hosts(self):
        for base_url in ("http://localhost.evil.example/v1", "http://127.0.0.1.evil.example/v1"):
            with self.subTest(base_url=base_url):
                with self.assertRaises(api_providers.ProviderError):
                    api_providers._endpoint(base_url, "/chat/completions")

    def test_rejects_duck_private_chat_endpoints(self):
        for base_url in (
            "https://duck.ai/duckchat/v1",
            "https://duckduckgo.com/duckchat/v1",
            "https://api.duck.ai/v1",
        ):
            with self.subTest(base_url=base_url):
                with self.assertRaisesRegex(api_providers.ProviderError, "private web interface"):
                    api_providers.validate_base_url(base_url)

    def test_anthropic_v1_base_url_does_not_duplicate_v1(self):
        endpoint = api_providers._endpoint("https://api.anthropic.com/v1", "/v1/messages")
        self.assertEqual(endpoint, "https://api.anthropic.com/v1/messages")

    def test_current_claude_model_ids_are_preserved(self):
        self.assertEqual(
            api_providers.normalize_model_id("anthropic", "claude-haiku-4-5-20251001"),
            "claude-haiku-5-5",
        )
        self.assertEqual(
            api_providers.normalize_model_id("anthropic", "claude-haiku-5-5"),
            "claude-haiku-5-5",
        )
        self.assertEqual(
            api_providers.normalize_model_id("anthropic", "claude-sonnet-5-5"),
            "claude-sonnet-5-5",
        )

    def test_duck_challenge_response_is_explained(self):
        class ChallengeResponse:
            status_code = 418
            text = '{"type":"ERR_CHALLENGE","cc":"duckchat"}'
            def json(self):
                return {"type": "ERR_CHALLENGE", "cc": "duckchat"}
        message = api_providers._safe_error(ChallengeResponse())
        self.assertIn("Duck.ai's private challenge response", message)
        self.assertIn("https://api.anthropic.com", message)


if __name__ == "__main__":
    unittest.main()


class DuckAICatalogTests(unittest.TestCase):
    def test_catalog_contains_all_current_text_models_and_tools(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import duckai_catalog
        catalog = duckai_catalog.get_catalog()
        names = {item["name"] for item in catalog["models"]}
        self.assertEqual(len(names), 10)
        self.assertTrue({"GPT-6 Luna", "Claude Haiku 5.5", "Mistral Small 4", "Gemma 4 31B", "GPT-5.6 Terra", "Claude Opus 5.5"}.issubset(names))
        kinds = {item["kind"] for item in catalog["tools"]}
        self.assertEqual(kinds, {"image", "audio"})
        self.assertEqual(len(catalog["free_models"]), 6)
