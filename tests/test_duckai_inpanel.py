"""Offline tests for Duck.ai model selection and in-panel generation routes."""
import base64
import uuid
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import duckai_catalog
import duck_cli
import web_app


class FakeDuckClient:
    def __init__(self):
        self.last_model = None
        self.last_prompt = None
        self.image_calls = []
        self.last_images = None
        self.last_prompt_extra = ""
        self.last_reasoning_effort = None

    def stream(self, prompt, model="gpt-6-luna", history=None, images=None, prompt_extra="", reasoning_effort=None):
        self.last_model = model
        self.last_prompt = prompt
        self.last_images = images
        self.last_prompt_extra = prompt_extra
        self.last_reasoning_effort = reasoning_effort
        yield "Mock answer from "
        yield model

    def generate_image(self, prompt, model="gpt-6-luna", out_dir=None, on_progress=None, retries=4, history=None):
        self.image_calls.append((prompt, model))
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        path = Path(out_dir) / f"test-{uuid.uuid4().hex}.png"
        path.write_bytes(b"mock-image")
        return str(path), "Mock image generated", {
            "format": "png",
            "b64": base64.b64encode(b"mock-image").decode("ascii"),
            "width": 2,
            "height": 2,
        }


class DuckAiInPanelTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(web_app.app)
        self.session = str(uuid.uuid4())
        self.conversation = str(uuid.uuid4())
        self.headers = {
            "X-Session-ID": self.session,
            "X-Conversation-ID": self.conversation,
        }
        self.fake = FakeDuckClient()

    def test_api_models_contains_six_duck_free_entries_plus_api_slot(self):
        response = self.client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        models = response.json()["models"]
        free = [model for model in models if model.get("engine") == "duckai"]
        self.assertEqual(len(free), 6)
        self.assertTrue(all(item["id"].startswith("duckai:") for item in free))
        self.assertEqual(models[-1]["id"], "api:configured")

    def test_selecting_duckai_model_persists_inside_panel(self):
        response = self.client.post(
            "/api/model", headers=self.headers,
            json={"model": "duckai:claude-haiku-5-5"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        state = self.client.get("/api/state", headers=self.headers).json()
        self.assertEqual(state["model"], "duckai:claude-haiku-5-5")
        self.assertEqual(state["default_model"], "duckai:claude-haiku-5-5")

    def test_chat_runs_through_original_duckai_client_for_selected_model(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "hello", "model": "duckai:claude-haiku-5-5"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('"engine":"duckai"', response.text)
        self.assertIn("Mock answer from claude-haiku-5-5", response.text)
        self.assertEqual(self.fake.last_model, "claude-haiku-5-5")

    def test_chat_accepts_legacy_alias_and_forwards_canonical_duck_id(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "hello", "model": "duckai:gpt-4o-mini"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.fake.last_model, "gpt-5.4-mini")

    def test_chat_forwards_selected_reasoning_effort_to_duckai_client(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "think carefully", "model": "duckai:gpt-5.4-mini", "reasoning_effort": "high"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.fake.last_model, "gpt-5.4-mini")
        self.assertEqual(self.fake.last_reasoning_effort, "high")

    def test_non_reasoning_model_discards_stale_reasoning_choice(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "hello", "model": "duckai:mistral-small-2603", "reasoning_effort": "high"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(self.fake.last_reasoning_effort)

    def test_duckai_catalog_ids_are_supported_by_original_client(self):
        known_ids = set(duck_cli.MODELS.values())
        self.assertTrue(all(item["model_id"] in known_ids for item in duckai_catalog.get_free_models()))

    def test_legacy_openai_and_anthropic_names_resolve_to_current_duck_ids(self):
        self.assertEqual(duckai_catalog.resolve_free_model("gpt-4o-mini"), "gpt-5.4-mini")
        self.assertEqual(duckai_catalog.resolve_free_model("duckai:gpt-4o-mini"), "gpt-5.4-mini")
        self.assertEqual(duckai_catalog.resolve_free_model("claude-3-haiku"), "claude-haiku-5-5")
        self.assertEqual(duckai_catalog.resolve_free_model("duckai:claude-3-haiku"), "claude-haiku-5-5")
        self.assertEqual(web_app._normalise_panel_model("gpt-4o-mini"), "duckai:gpt-5.4-mini")

    def test_duck_client_sends_canonical_id_for_compatibility_alias(self):
        client = duck_cli.DuckAI()
        response = Mock()
        with patch.object(client.s, "post", return_value=response) as post:
            client.chat("hello", model="gpt-4o-mini")
        payload = __import__("json").loads(post.call_args.kwargs["data"])
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertEqual(set(payload), {
            "model", "messages", "canUseTools", "canUseApproxLocation",
            "canDelegateImageGeneration", "canShowGreeting", "reasoningEffort",
        })

    def test_duck_client_rejects_unknown_model_id_before_network_call(self):
        client = duck_cli.DuckAI()
        with patch.object(client.s, "post") as post:
            with self.assertRaisesRegex(duck_cli.DuckAIError, "Unsupported Duck.ai model ID"):
                client.chat("hello", model="not-a-real-model")
        post.assert_not_called()

    def test_chat_off_reasoning_is_forwarded_as_none(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "hello", "model": "duckai:claude-haiku-5-5", "reasoning_effort": "none"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.fake.last_reasoning_effort, "none")

    def test_chat_image_attachment_is_forwarded_to_duckai_engine(self):
        marker = {"type": "image", "mimeType": "image/webp", "image": "data:image/webp;base64,AA=="}
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake), \
             patch.object(web_app.duck_cli, "image_to_data_url", lambda _path: marker):
            response = self.client.post(
                "/api/chat", headers=self.headers,
                data={"prompt": "Please describe this picture", "model": "duckai:gpt-6-luna"},
                files={"attachments": ("memory-photo.png", b"fake-png-bytes", "image/png")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('"engine":"duckai"', response.text)
        self.assertEqual(self.fake.last_images, [marker])

    def test_image_generation_runs_inside_panel_with_selected_free_model(self):
        with patch.object(web_app.WebSession, "get_client", lambda _self: self.fake):
            response = self.client.post(
                "/api/draw", headers=self.headers,
                data={"prompt": "a purple cyberpunk city", "model": "duckai:gpt-6-luna"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["model"], "duckai:gpt-6-luna")
        self.assertTrue(payload["image_url"].startswith("/generated/"))
        self.assertEqual(self.fake.image_calls, [("a purple cyberpunk city", "gpt-6-luna")])

    def test_duck_client_omits_reasoning_effort_for_mistral_payload(self):
        client = duck_cli.DuckAI()
        response = Mock()
        with patch.object(client.s, "post", return_value=response) as post:
            client.chat("hello", model="mistral-small-2603", reasoning_effort="high")
        payload = __import__("json").loads(post.call_args.kwargs["data"])
        self.assertEqual(payload["model"], "mistral-small-2603")
        self.assertNotIn("reasoningEffort", payload)

    def test_duck_client_includes_reasoning_effort_only_for_supported_model(self):
        client = duck_cli.DuckAI()
        response = Mock()
        with patch.object(client.s, "post", return_value=response) as post:
            client.chat("think", model="gpt-5.4-mini", reasoning_effort="high")
        payload = __import__("json").loads(post.call_args.kwargs["data"])
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertEqual(payload["reasoningEffort"], "high")

    def test_paid_model_is_not_accepted_as_free_model(self):
        with self.assertRaises(ValueError):
            duckai_catalog.resolve_free_model("duckai:gpt-5.6-terra")


if __name__ == "__main__":
    unittest.main()
