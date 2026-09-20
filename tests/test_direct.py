import unittest
from unittest.mock import patch

from src import direct


class TestDirectSource(unittest.TestCase):

    def test_latest_returns_pinned_version(self):
        self.assertEqual(
            direct.get_latest_version("brave", {"package": "com.brave.browser", "version": "1.95.101", "url": "https://x/y.apk"}),
            "1.95.101",
        )

    def test_latest_none_when_unpinned(self):
        self.assertIsNone(direct.get_latest_version("brave", {"package": "com.brave.browser", "url": "https://x/y.apk"}))

    def test_link_returned_on_exact_match(self):
        url = "https://github.com/example/brave-1.95.101.apk"
        self.assertEqual(
            direct.get_download_link("1.95.101", "brave", {"package": "com.brave.browser", "version": "1.95.101", "url": url}),
            url,
        )

    def test_link_skipped_on_version_mismatch(self):
        self.assertIsNone(
            direct.get_download_link("1.90.0", "brave", {"package": "com.brave.browser", "version": "1.95.101", "url": "https://x/y.apk"}),
        )

    def test_link_skipped_when_url_empty(self):
        self.assertIsNone(
            direct.get_download_link("1.95.101", "brave", {"package": "com.brave.browser", "version": "1.95.101", "url": ""}),
        )

    def test_non_http_url_rejected(self):
        self.assertIsNone(
            direct.get_download_link("1.95.101", "brave", {"package": "com.brave.browser", "version": "1.95.101", "url": "ftp://x/y.apk"}),
        )

    # ─── Dynamic {version} templates (e.g. Brave GitHub mono APK) ────────────

    _TPL = "https://github.com/brave/brave-browser/releases/download/v{version}/Bravemonoarm64.apk"

    @patch("src.direct._url_exists", return_value=True)
    def test_template_substitutes_version(self, _mock):
        self.assertEqual(
            direct.get_download_link("1.95.101", "brave", {"package": "com.brave.browser", "url": self._TPL}),
            "https://github.com/brave/brave-browser/releases/download/v1.95.101/Bravemonoarm64.apk",
        )

    @patch("src.direct._url_exists", return_value=False)
    def test_template_404_falls_through(self, _mock):
        self.assertIsNone(
            direct.get_download_link("9.99.99", "brave", {"package": "com.brave.browser", "url": self._TPL}),
        )

    @patch("src.direct._url_exists", return_value=None)
    def test_template_unknown_returned_optimistically(self, _mock):
        self.assertEqual(
            direct.get_download_link("1.95.101", "brave", {"package": "com.brave.browser", "url": self._TPL}),
            "https://github.com/brave/brave-browser/releases/download/v1.95.101/Bravemonoarm64.apk",
        )

    def test_template_needs_a_version(self):
        self.assertIsNone(
            direct.get_download_link("", "brave", {"package": "com.brave.browser", "url": self._TPL}),
        )


if __name__ == "__main__":
    unittest.main()
