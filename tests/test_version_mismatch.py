import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from src import utils, apkmirror, apkpure, github, downloader


class TestVersionCompatibility(unittest.TestCase):

    def test_exact_match(self):
        self.assertTrue(utils.is_version_compatible("21.16.256", "21.16.256"))
        self.assertTrue(utils.is_version_compatible("1.0", "1.0"))

    def test_mismatched_minor_or_patch(self):
        # Critical regression: 21.16.249 must NOT match 21.16.256
        self.assertFalse(utils.is_version_compatible("21.16.249", "21.16.256"))
        self.assertFalse(utils.is_version_compatible("21.16.256", "21.16.249"))
        self.assertFalse(utils.is_version_compatible("21.16", "21.16.256"))
        self.assertFalse(utils.is_version_compatible("1.2.3", "1.2.4"))

    def test_variant_and_release_suffixes(self):
        # Release and store suffixes are compatible
        self.assertTrue(utils.is_version_compatible("4.9.49-googleplay", "4.9.49"))
        self.assertTrue(utils.is_version_compatible("1.0.0-RELEASE", "1.0.0"))
        self.assertTrue(utils.is_version_compatible("2.0.1_beta", "2.0.1"))
        self.assertTrue(utils.is_version_compatible("2.0.1+hotfix", "2.0.1"))

    def test_v_prefix_and_parentheses(self):
        self.assertTrue(utils.is_version_compatible("v1.95.104", "1.95.104"))
        self.assertTrue(utils.is_version_compatible("1.95.104", "v1.95.104"))
        self.assertTrue(utils.is_version_compatible("32.30.0", "32.30.0(1575420)"))
        self.assertTrue(utils.is_version_compatible("32.30.0(1575420)", "32.30.0"))

    def test_arch_suffixes(self):
        self.assertTrue(utils.is_version_compatible("18.2.4-arm64-v8a", "18.2.4"))
        self.assertTrue(utils.is_version_compatible("18.2.4", "18.2.4-arm64-v8a"))

    def test_empty_or_latest(self):
        self.assertTrue(utils.is_version_compatible("1.2.3", None))
        self.assertTrue(utils.is_version_compatible("1.2.3", ""))
        self.assertTrue(utils.is_version_compatible("1.2.3", "latest"))
        self.assertFalse(utils.is_version_compatible("", "1.2.3"))


class TestApkMirrorVariantRejection(unittest.TestCase):

    HTML_WITH_MISMATCHED_VARIANT = """
    <html>
      <head><title>YouTube 21.16.256 APK Download by Google LLC - APKMirror</title></head>
      <body>
        <div class="table-row headerFont">
          <span class="apkm-badge">APK</span>
          <div class="table-cell">21.16.249</div>
          <div class="table-cell">arm64-v8a</div>
          <div class="table-cell">nodpi</div>
          <a class="accent_color" href="/apk/google-inc/youtube/youtube-21-16-249-release/variant-download/">Download</a>
        </div>
      </body>
    </html>
    """

    HTML_WITH_MATCHING_VARIANT = """
    <html>
      <head><title>YouTube 21.16.256 APK Download by Google LLC - APKMirror</title></head>
      <body>
        <div class="table-row headerFont">
          <span class="apkm-badge">APK</span>
          <div class="table-cell">21.16.256</div>
          <div class="table-cell">arm64-v8a</div>
          <div class="table-cell">nodpi</div>
          <a class="accent_color" href="/apk/google-inc/youtube/youtube-21-16-256-release/variant-download/">Download</a>
        </div>
      </body>
    </html>
    """

    def setUp(self):
        self._sleep_patch = patch("src.apkmirror.time.sleep", return_value=None)
        self._sleep_patch.start()
        self.addCleanup(self._sleep_patch.stop)
        self._build_patch = patch("src.apkmirror.get_build_number_for_version", return_value=(None, None))
        self._build_patch.start()
        self.addCleanup(self._build_patch.stop)
        self._find_patch = patch("src.apkmirror.find_release_page_from_main", return_value="https://www.apkmirror.com/apk/google-inc/youtube/youtube-21-16-256-release/")
        self._find_patch.start()
        self.addCleanup(self._find_patch.stop)

    @patch("src.apkmirror._cf_get")
    def test_rejects_mismatched_minor_version_row(self, mock_cf_get):
        """When 21.16.256 is targeted, APKMirror must NOT download a 21.16.249 variant."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = self.HTML_WITH_MISMATCHED_VARIANT.encode("utf-8")
        mock_resp.url = "https://www.apkmirror.com/apk/google-inc/youtube/youtube-21-16-256-release/"
        mock_cf_get.return_value = mock_resp

        config = {
            "name": "youtube",
            "org": "google-inc",
            "type": "APK",
            "arch": "arm64-v8a",
            "dpi": "nodpi",
        }
        url = apkmirror.get_download_link("21.16.256", "youtube", config)
        self.assertIsNone(url)

    @patch("src.apkmirror._pick_download_button", return_value="https://apkmirror.com/step2/")
    @patch("src.apkmirror._cf_get")
    def test_accepts_matching_version_row(self, mock_cf_get, _mock_pick):
        """When 21.16.256 is targeted and matching row is present, download link is returned."""
        resp1 = Mock(status_code=200, content=self.HTML_WITH_MATCHING_VARIANT.encode("utf-8"), url="https://apkmirror.com/step1/")
        resp2 = Mock(status_code=200, content=b'<a id="download-link" href="/final.apk">DL</a>', url="https://apkmirror.com/step2/")
        mock_cf_get.side_effect = [resp1, resp1, resp2]

        config = {
            "name": "youtube",
            "org": "google-inc",
            "type": "APK",
            "arch": "arm64-v8a",
            "dpi": "nodpi",
        }
        url = apkmirror.get_download_link("21.16.256", "youtube", config)
        self.assertIsNotNone(url)
        self.assertTrue(url.endswith("/final.apk"))


class TestApkPureVersionRejection(unittest.TestCase):

    @patch("src.apkpure._cdn_download_url", return_value=None)
    @patch("src.apkpure._discover_slug", return_value="some-slug")
    @patch("src.apkpure._get_direct_download", return_value=None)
    @patch("src.apkpure._try_get_version_list")
    def test_does_not_fall_back_to_closest_when_version_specified(self, mock_versions, _mock_direct, _mock_slug, _mock_cdn):
        """APKPure must return None when requested version is not in version list."""
        mock_versions.return_value = [
            {"version": "21.16.249", "href": "/download/21.16.249"},
            {"version": "21.15.100", "href": "/download/21.15.100"},
        ]
        config = {"name": "youtube", "package": "com.google.android.youtube"}
        url = apkpure.get_download_link("21.16.256", "youtube", config)
        self.assertIsNone(url)


class TestGithubVersionBoundaryMatching(unittest.TestCase):

    @patch("src.github.session.get")
    def test_github_does_not_substring_match_different_version(self, mock_get):
        """GitHub releases: version 21.16.2 must not match an asset for 21.16.256."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "assets": [
                {
                    "name": "youtube-21.16.256-arm64-v8a.apk",
                    "browser_download_url": "https://github.com/releases/youtube-21.16.256-arm64-v8a.apk"
                }
            ]
        }
        mock_get.return_value = mock_resp

        config = {"repo": "owner/repo", "tag": "v1.0", "arch": "arm64-v8a"}
        # Target 21.16.2 should NOT match 21.16.256
        url = github.get_download_link("21.16.2", "youtube", config)
        self.assertIsNone(url)

        # Target 21.16.256 MUST match
        url_match = github.get_download_link("21.16.256", "youtube", config)
        self.assertEqual(url_match, "https://github.com/releases/youtube-21.16.256-arm64-v8a.apk")


class TestDownloaderManifestGuard(unittest.TestCase):

    @patch("src.utils.get_apk_manifest_info")
    @patch("src.downloader.download_resource")
    @patch("src.downloader.apkmirror.get_download_link", return_value="https://apkmirror.com/download/fake.apk")
    @patch("pathlib.Path.unlink")
    def test_downloader_rejects_mismatched_apk_file(self, mock_unlink, _mock_link, mock_dl, mock_manifest):
        """downloader.download_platform must reject downloaded APK if manifest version differs."""
        fake_apk = Path("fake_downloaded.apk")
        mock_dl.return_value = fake_apk
        mock_manifest.return_value = {"versionName": "21.16.249", "package": "com.google.android.youtube"}

        apk, ver, _ = downloader.download_platform("youtube", "apkmirror", "cli", [], "arm64-v8a", override_version="21.16.256")
        self.assertIsNone(apk)
        self.assertIsNone(ver)
        mock_unlink.assert_called()


class TestApkManifestReader(unittest.TestCase):

    def test_reads_existing_apk_manifest(self):
        """If an APK exists on disk, test reading its manifest info."""
        chess_apk = Path("/home/dexy/.local/share/Trash/files/com.chess_4.9.49-googleplay-268211_minAPI26(arm64-v8a)(nodpi)_apkmirror.com.apk")
        if chess_apk.exists():
            info = utils.get_apk_manifest_info(chess_apk)
            self.assertEqual(info.get("package"), "com.chess")
            self.assertEqual(info.get("versionName"), "4.9.49-googleplay")
            self.assertEqual(info.get("versionCode"), 268211)

    def test_handles_non_existent_file(self):
        self.assertEqual(utils.get_apk_manifest_info("/non/existent/file.apk"), {})

    def test_handles_invalid_zip(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".apk") as f:
            f.write(b"not a zip file")
            f.flush()
            self.assertEqual(utils.get_apk_manifest_info(f.name), {})


if __name__ == "__main__":
    unittest.main()
