"""Offline regression tests for parity with the upstream DuckAi retry loop."""
import unittest
from unittest.mock import Mock, patch

import duck_cli


class FakeResponse:
    def __init__(self, status_code, body="", lines=None):
        self.status_code = status_code
        self.text = body
        self._lines = lines or []
        self.closed = False

    def close(self):
        self.closed = True

    def iter_lines(self):
        yield from self._lines


class DuckAiRetryTests(unittest.TestCase):
    def setUp(self):
        self.client = duck_cli.DuckAI()
        # Skip initial handshake: the tests focus on retry behavior after a
        # prepared session, not on exercising Duck.ai's private endpoint.
        self.client.fe_version = "test-version"
        self.client.jsa = "test-proof"

    def test_http_418_chat_response_gets_fresh_handshake_and_retries(self):
        rejected = FakeResponse(418, '{"type":"ERR_CHALLENGE"}')
        accepted = FakeResponse(
            200,
            lines=[b'data: {"role":"assistant","message":"recovered"}'],
        )
        self.client.chat = Mock(side_effect=[rejected, accepted])
        self.client.rehandshake = Mock()

        with patch.object(duck_cli.time, "sleep", return_value=None):
            events = list(self.client.stream_events("hello", retries=4))

        self.assertEqual(events, [("message", "recovered")])
        self.assertEqual(self.client.chat.call_count, 2)
        self.client.rehandshake.assert_called_once_with()
        self.assertTrue(rejected.closed)

    def test_four_http_418_responses_raise_chat_http_phase(self):
        responses = [FakeResponse(418, '{"type":"ERR_CHALLENGE"}') for _ in range(4)]
        self.client.chat = Mock(side_effect=responses)
        self.client.rehandshake = Mock()

        with patch.object(duck_cli.time, "sleep", return_value=None):
            with self.assertRaises(duck_cli.DuckAIError) as ctx:
                list(self.client.stream_events("hello", retries=4))

        self.assertEqual(ctx.exception.status, 418)
        self.assertEqual(ctx.exception.phase, "chat_http")
        self.assertEqual(self.client.chat.call_count, 4)
        self.assertEqual(self.client.rehandshake.call_count, 3)
        self.assertTrue(all(item.closed for item in responses))

    def test_http_400_payload_error_fails_without_retries(self):
        rejected = FakeResponse(400, '{"action":"error","status":400,"type":"ERR_BAD_REQUEST"}')
        self.client.chat = Mock(return_value=rejected)
        self.client.rehandshake = Mock()

        with self.assertRaises(duck_cli.DuckAIError) as ctx:
            list(self.client.stream_events("hello", retries=4))

        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.phase, "chat_http")
        self.assertEqual(self.client.chat.call_count, 1)
        self.client.rehandshake.assert_not_called()
        self.assertTrue(rejected.closed)

    def test_http_451_fails_without_retries(self):
        rejected = FakeResponse(451, '{"type":"ERR_COUNTRY_NOT_SUPPORTED"}')
        self.client.chat = Mock(return_value=rejected)
        self.client.rehandshake = Mock()

        with self.assertRaises(duck_cli.DuckAIError) as ctx:
            list(self.client.stream_events("hello", retries=4))

        self.assertEqual(ctx.exception.status, 451)
        self.assertEqual(ctx.exception.phase, "chat_http")
        self.assertEqual(self.client.chat.call_count, 1)

    def test_challenge_fetch_failure_is_classified_separately(self):
        response = Mock()
        response.status_code = 418
        response.headers = {}
        response.text = '{"type":"ERR_CHALLENGE"}'
        self.client.s.get = Mock(return_value=response)

        with self.assertRaises(duck_cli.DuckAIError) as ctx:
            self.client.fetch_challenge()

        self.assertEqual(ctx.exception.status, 418)
        self.assertEqual(ctx.exception.phase, "challenge")

    def test_http_200_sse_challenge_event_is_classified(self):
        response = FakeResponse(
            200,
            lines=[b'data: {"action":"error","status":418,"type":"ERR_CHALLENGE"}'],
        )
        self.client.chat = Mock(return_value=response)

        with self.assertRaises(duck_cli.DuckAIError) as ctx:
            list(self.client.stream_events("hello", retries=1))

        self.assertEqual(ctx.exception.status, 418)
        self.assertEqual(ctx.exception.phase, "chat_sse")


if __name__ == "__main__":
    unittest.main()
