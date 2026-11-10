"""Regression tests for the 2.5.6 chat UI and output filtering."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import web_app


class ChatUIRegressionTests(unittest.TestCase):
    def test_stop_tokens_are_removed_from_plain_text(self):
        self.assertEqual(
            web_app.clean_stop_tokens("hello<|im_end|><|endoftext|> world"),
            "hello world",
        )

    def test_stop_tokens_are_removed_when_split_across_deltas(self):
        chunks = ["hello<|im_", "end|>world<|endof", "text|>!"]
        self.assertEqual("".join(web_app.clean_stream_deltas(chunks)), "helloworld!")

    def test_partial_stop_token_prefix_is_not_leaked(self):
        chunks = ["answer<|im_", "end|>"]
        self.assertEqual("".join(web_app.clean_stream_deltas(chunks)), "answer")

    def test_duckai_reasoning_options_are_model_capability_aware(self):
        models = {m["model_id"]: m for m in web_app._combined_model_catalog() if m.get("engine") == "duckai"}
        self.assertEqual(len(models), 6)
        self.assertEqual(models["mistral-small-2603"]["reasoning"]["options"], [])
        self.assertFalse(models["mistral-small-2603"]["reasoning"]["supports"])
        self.assertEqual(models["gpt-5.4-mini"]["reasoning"]["options"], ["none", "low", "medium", "high"])
        self.assertTrue(models["gpt-5.4-mini"]["reasoning"]["extended"])
        for model_id in ("claude-haiku-5-5", "gpt-6-luna", "tinfoil/gpt-oss-120b", "tinfoil/gemma4-31b"):
            self.assertTrue(models[model_id]["reasoning"]["supports"])
            self.assertNotIn("high", models[model_id]["reasoning"]["options"])

    def test_chat_composer_contains_only_attach_text_send_controls(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        start = html.index('<form class="composer" id="chatForm"')
        end = html.index('</form>', start) + len('</form>')
        composer = html[start:end]
        self.assertIn('id="attachBtn"', composer)
        self.assertIn('id="chatInput"', composer)
        self.assertIn('id="sendBtn"', composer)
        self.assertNotIn('composer-tools', composer)
        self.assertNotIn('send-hint-glass', composer)

    def test_new_conversation_button_has_non_wrapping_css(self):
        css = (ROOT / "web" / "assets" / "app.css").read_text(encoding="utf-8")
        self.assertIn("#page-chat.active .page-heading .heading-actions #clearChat", css)
        self.assertIn("white-space: nowrap !important", css)
        self.assertIn("direction: rtl !important", css)
        self.assertIn("unicode-bidi: isolate !important", css)

    def test_persian_prompt_is_right_aligned_and_shortcut_badge_is_readable(self):
        css = (ROOT / "web" / "assets" / "app.css").read_text(encoding="utf-8")
        self.assertIn('html[lang="fa"] #page-chat.active .chat-main > .composer > .composer-row > textarea', css)
        self.assertIn("text-align: right !important", css)
        self.assertIn("color: #cbd5e1 !important", css)
        self.assertIn("background: rgba(148, 163, 184, .12) !important", css)

    def test_new_chat_button_uses_isolated_icon_and_label(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="clear-chat-icon"', html)
        self.assertIn('class="clear-chat-label"', html)

    def test_dark_mode_model_cards_and_global_scrollbars_are_styled(self):
        css = (ROOT / "web" / "assets" / "app.css").read_text(encoding="utf-8")
        self.assertIn("rgba(19, 27, 46, .68)", css)
        self.assertIn("#f1f5f9", css)
        self.assertIn("#94a3b8", css)
        self.assertIn("#22d3ee", css)
        self.assertIn("::-webkit-scrollbar-track", css)
        self.assertIn("#0b0f19", css)
        self.assertIn("html:not([data-theme=\"light\"])::-webkit-scrollbar", css)
        self.assertIn("#1e293b", css)
        self.assertIn("#334155", css)

    def test_dropdowns_are_above_dashboard_layers(self):
        css = (ROOT / "web" / "assets" / "app.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.neo-select-menu\s*\{[^}]*z-index:\s*12000")
        self.assertRegex(css, r"\.neo-select-wrap\.is-open\s*\{[^}]*z-index:\s*12001")

    def test_served_html_uses_versioned_262_assets(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/assets/app.css?v=2.6.2", html)
        self.assertIn("/assets/app.js?v=2.6.2", html)
        self.assertIn("2.6.2", html)

    def test_root_and_served_frontend_assets_are_synchronised(self):
        self.assertEqual((ROOT / "app.css").read_bytes(), (ROOT / "web" / "assets" / "app.css").read_bytes())
        self.assertEqual((ROOT / "app.js").read_bytes(), (ROOT / "web" / "assets" / "app.js").read_bytes())
        self.assertEqual((ROOT / "index.html").read_bytes(), (ROOT / "web" / "index.html").read_bytes())

    def test_fastapi_serves_dark_mode_css_and_current_cache_key(self):
        from fastapi.testclient import TestClient
        client = TestClient(web_app.app)
        page = client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("/assets/app.css?v=2.6.2", page.text)
        css = client.get("/assets/app.css?v=2.6.2")
        self.assertEqual(css.status_code, 200)
        self.assertIn("#0b0f19", css.text)
        self.assertIn("html:not([data-theme=\"light\"])::-webkit-scrollbar", css.text)

    def test_browser_stop_token_filter_is_present(self):
        js = (ROOT / "web" / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("function stripStopTokens(value)", js)
        self.assertIn("im_end|endoftext", js)


if __name__ == "__main__":
    unittest.main()
