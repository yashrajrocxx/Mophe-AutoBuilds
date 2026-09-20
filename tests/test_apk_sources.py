import unittest
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from src import apkcombo
from src import apkmirror
from src import apkpure


def _resp(status=200, html=""):
    m = Mock()
    m.status_code = status
    m.content = html.encode()
    return m


class TestApkComboSlugDiscovery(unittest.TestCase):

    SEARCH_HTML = """
    <html><body>
      <a href="/pt/search/in.startv.hotstar">PT</a>
      <a href="/search/in.startv.hotstar">EN</a>
      <a href="/jiohotstar/in.startv.hotstar/">JioHotstar</a>
      <a href="/pt/jiohotstar/in.startv.hotstar/download/phone-26.06.22.3-apk">DL</a>
    </body></html>
    """

    @patch("src.apkcombo._get")
    def test_locale_prefix_never_returned(self, mock_get):
        mock_get.return_value = _resp(200, self.SEARCH_HTML)
        self.assertEqual(apkcombo._discover_slug("in.startv.hotstar"), "jiohotstar")

    @patch("src.apkcombo._get")
    def test_locale_only_page_returns_none(self, mock_get):
        mock_get.return_value = _resp(200, '<a href="/pt/search/in.startv.hotstar">x</a>')
        self.assertIsNone(apkcombo._discover_slug("in.startv.hotstar"))

    @patch("src.apkcombo._get")
    def test_http_failure_returns_none(self, mock_get):
        mock_get.return_value = _resp(410, "")
        self.assertIsNone(apkcombo._discover_slug("in.startv.hotstar"))


class TestApkPureCdnGating(unittest.TestCase):

    @patch("src.apkpure.get_version_code_from_api", return_value=None)
    @patch("src.apkpure.std_requests.head")
    def test_403_falls_through_to_none(self, mock_head, _mock_vc):
        mock_head.return_value = Mock(status_code=403, url="https://d.apkpure.net/x")
        self.assertIsNone(apkpure._cdn_download_url("in.startv.hotstar", "26.06.22.3"))

    @patch("src.apkpure.get_version_code_from_api", return_value=None)
    @patch("src.apkpure.std_requests.head")
    def test_200_returns_resolved_url(self, mock_head, _mock_vc):
        mock_head.return_value = Mock(status_code=200, url="https://d.apkpure.net/final.apk")
        self.assertEqual(
            apkpure._cdn_download_url("com.example.app", "1.0"),
            "https://d.apkpure.net/final.apk",
        )

    @patch("src.apkpure.get_version_code_from_api", return_value=None)
    @patch("src.apkpure.std_requests.head", side_effect=Exception("blocked"))
    def test_probe_error_returns_optimistic_url(self, _mock_head, _mock_vc):
        url = apkpure._cdn_download_url("com.example.app", "1.0")
        self.assertTrue(url.startswith("https://d.apkpure.net/b/APK/com.example.app?version=1.0"))


class TestApkMirrorBundleButton(unittest.TestCase):

    VARIANT_HTML = """
    <html><body>
      <a class="downloadButton" href="/apk/x/y-2-android-apk-download/download/?key=ABC&forcebaseapk=true">APK</a>
      <a class="downloadButton" href="/apk/x/y-2-android-apk-download/download/?key=ABC">Bundle</a>
    </body></html>
    """

    def test_bundle_request_skips_forcebaseapk(self):
        soup = BeautifulSoup(self.VARIANT_HTML, "html.parser")
        url = apkmirror._pick_download_button(soup, want_bundle=True)
        self.assertTrue(url.endswith("/download/?key=ABC"))

    def test_apk_request_prefers_forcebaseapk(self):
        soup = BeautifulSoup(self.VARIANT_HTML, "html.parser")
        url = apkmirror._pick_download_button(soup, want_bundle=False)
        self.assertIn("forcebaseapk=true", url)

    def test_no_buttons_returns_none(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        self.assertIsNone(apkmirror._pick_download_button(soup, want_bundle=True))

    def test_bare_number_version_code(self):
        row = "8.2.4147.77 BUNDLE 1 S 541470077 September 14, 2026 arm64-v8a Android 10+ nodpi"
        self.assertEqual(apkmirror._extract_version_code_from_text(row, "8.2.4147.77"), 541470077)

    def test_year_not_mistaken_for_code(self):
        self.assertIsNone(apkmirror._extract_version_code_from_text("Released September 14, 2026", "9.9.9"))


if __name__ == "__main__":
    unittest.main()
