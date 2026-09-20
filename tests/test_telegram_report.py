import io
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import send_telegram_report as tgr


class _FakeResp:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestTelegramReport(unittest.TestCase):

    def test_skip_without_credentials(self):
        with patch.dict(os.environ, {}, clear=False):
            env = {k: v for k, v in os.environ.items()
                   if k not in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_CHATID")}
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(tgr.main(), 0)

    def test_http_error_falls_back_to_plain_text(self):
        """A 400 from Telegram must trigger the plain-text fallback, not crash."""
        err = HTTPError("http://x", 400, "Bad Request", {}, io.BytesIO(b'{"ok":false}'))
        with patch.object(tgr, "urlopen", side_effect=[err, _FakeResp(200)]):
            self.assertTrue(tgr.send_telegram_message("tok", "123", "<b>hi</b>"))

    def test_http_error_both_attempts_fail(self):
        err = HTTPError("http://x", 400, "Bad Request", {}, io.BytesIO(b'{"ok":false}'))
        with patch.object(tgr, "urlopen", side_effect=err):
            self.assertFalse(tgr.send_telegram_message("tok", "123", "<b>hi</b>"))

    def test_network_error_returns_false(self):
        with patch.object(tgr, "urlopen", side_effect=Exception("no route")):
            self.assertFalse(tgr.send_telegram_message("tok", "123", "hi"))

    def test_success(self):
        with patch.object(tgr, "urlopen", return_value=_FakeResp(200)):
            self.assertTrue(tgr.send_telegram_message("tok", "123", "hi"))

    def test_split_message(self):
        long_text = "\n".join(f"line-{i}" for i in range(1000))
        chunks = tgr.split_message(long_text, max_length=100)
        self.assertTrue(len(chunks) > 1)
        self.assertEqual("\n".join(chunks), long_text)

    def test_escape_html(self):
        self.assertEqual(tgr.escape_html("<b>&"), "&lt;b&gt;&amp;")

    def test_multiple_destinations(self):
        """Comma-separated chat IDs each receive the report."""
        env = {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "@chan, 12345"}
        with patch.dict(os.environ, env, clear=True):
            with patch.object(tgr, "send_telegram_message", return_value=True) as mock_send:
                with patch.object(tgr, "load_build_reports", return_value=[]):
                    self.assertEqual(tgr.main(), 0)
        self.assertEqual(mock_send.call_count, 2)
        targets = [c.args[1] for c in mock_send.call_args_list]
        self.assertEqual(targets, ["@chan", "12345"])


if __name__ == "__main__":
    unittest.main()
