import unittest

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


if __name__ == "__main__":
    unittest.main()
