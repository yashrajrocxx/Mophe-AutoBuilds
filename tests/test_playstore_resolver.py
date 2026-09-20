import os
import unittest
from unittest.mock import patch, Mock

from src import playstore


class TestPlaystoreResolver(unittest.TestCase):

    def setUp(self):
        # Reset cache before each test
        playstore._exodus_cache = {}
        # Remove any stale env vars that might interfere
        os.environ.pop("EXODUS_API_KEY", None)
        # Never hit the network via APKMirror during unit tests by default
        self._apkmirror_patcher = patch('src.apkmirror.get_version_code', return_value=None)
        self._mock_apkmirror_vc = self._apkmirror_patcher.start()
        self.addCleanup(self._apkmirror_patcher.stop)

    def tearDown(self):
        # Clear CLI cache entries created by precedence test
        from src import utils
        utils.cli_version_codes.pop(("au.com.shiftyjelly.pocketcasts", "8.16"), None)

    # ─── CLI-provided versionCode (highest priority) ───────────────────────────

    def test_cli_version_code_precedence(self):
        """CLI-provided versionCode must be returned without any HTTP calls."""
        from src import utils
        utils.cli_version_codes[("au.com.shiftyjelly.pocketcasts", "8.16")] = {
            "arm64_v8a": 9441,
            "universal": 9441
        }
        with patch('src.apkpure.std_requests.get') as mock_api, \
             patch('src.playstore.scrape_exodus_version_code') as mock_exodus:
            code = playstore.resolve_version_code("au.com.shiftyjelly.pocketcasts", "8.16", "arm64-v8a")
            self.assertEqual(code, 9441)
            mock_api.assert_not_called()
            mock_exodus.assert_not_called()

    # ─── APKPure mobile API (step 3) ──────────────────────────────────────────

    @patch('src.apkpure.std_requests.get')
    def test_apkpure_api_exact_match(self, mock_api_get):
        """APKPure API returning a matching version_code must resolve correctly."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "list": [
                    {"version_name": "2.371.0", "version_code": "29652157"},
                    {"version_name": "2.369.0", "version_code": "29633241"},
                ]
            }
        }
        mock_api_get.return_value = mock_resp

        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 29652157)

    @patch('src.apkpure.std_requests.get')
    def test_apkpure_api_multiple_abi_variants_returns_max(self, mock_api_get):
        """When multiple entries match the same version_name, the highest code wins."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "list": [
                    {"version_name": "2.371.0", "version_code": "100"},
                    {"version_name": "2.371.0", "version_code": "200"},
                ]
            }
        }
        mock_api_get.return_value = mock_resp

        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 200)

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_apkpure_api_version_not_present_falls_to_exodus(self, mock_exodus, mock_api_get):
        """If APKPure API has no matching version, fallback to Exodus web scraper."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {"list": [{"version_name": "2.369.0", "version_code": "29633241"}]}
        }
        mock_api_get.return_value = mock_resp
        mock_exodus.return_value = 14348020

        code = playstore.resolve_version_code("com.pinterest", "14.34.0")
        self.assertEqual(code, 14348020)
        mock_exodus.assert_called_once_with("com.pinterest", "14.34.0")

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_version_not_found_raises(self, mock_exodus, mock_api_get):
        """If all resolvers fail, VersionNotFound must be raised."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"list": []}}
        mock_api_get.return_value = mock_resp
        mock_exodus.return_value = None

        with self.assertRaises(playstore.VersionNotFound):
            playstore.resolve_version_code("com.instagram.android", "9.99.99")

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_apkpure_api_failure_falls_to_exodus(self, mock_exodus, mock_api_get):
        """If APKPure API returns non-200, fallback to Exodus web scraper."""
        mock_resp = Mock()
        mock_resp.status_code = 503
        mock_api_get.return_value = mock_resp
        mock_exodus.return_value = 29652157

        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 29652157)

    # ─── Exodus web scraper fallback (step 4) ─────────────────────────────────

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_exodus_web_fallback_success(self, mock_scrape, mock_api_get):
        """When APKPure API finds nothing, Exodus web scraper resolves the code."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"list": []}}
        mock_api_get.return_value = mock_resp
        mock_scrape.return_value = 14348020

        code = playstore.resolve_version_code("com.pinterest", "14.34.0")
        self.assertEqual(code, 14348020)
        mock_scrape.assert_called_once_with("com.pinterest", "14.34.0")

    # ─── Caching ──────────────────────────────────────────────────────────────

    @patch('src.apkpure.std_requests.get')
    def test_result_is_cached(self, mock_api_get):
        """Resolved versionCode must be cached — second call must not hit the API."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {"list": [{"version_name": "2.371.0", "version_code": "29652157"}]}
        }
        mock_api_get.return_value = mock_resp

        playstore.resolve_version_code("com.instagram.android", "2.371.0")
        playstore.resolve_version_code("com.instagram.android", "2.371.0")
        # API should only be called once (second call served from cache)
        self.assertEqual(mock_api_get.call_count, 1)

    # ─── APKMirror scrape fallback (step 4) ─────────────────────────────────

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_apkmirror_fallback_success(self, mock_exodus, mock_api_get):
        """When APKPure API finds nothing, APKMirror resolves before Exodus."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"list": []}}
        mock_api_get.return_value = mock_resp
        self._mock_apkmirror_vc.return_value = 29652157

        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 29652157)
        mock_exodus.assert_not_called()

    @patch('src.apkpure.std_requests.get')
    @patch('src.playstore.scrape_exodus_version_code')
    def test_apkmirror_miss_falls_to_exodus(self, mock_exodus, mock_api_get):
        """APKMirror returning None must fall through to Exodus web scraper."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"list": []}}
        mock_api_get.return_value = mock_resp
        self._mock_apkmirror_vc.return_value = None
        mock_exodus.return_value = 14348020

        code = playstore.resolve_version_code("com.pinterest", "14.34.0")
        self.assertEqual(code, 14348020)
        mock_exodus.assert_called_once_with("com.pinterest", "14.34.0")

    # ─── gplaydl info parsing (step 2, incl. --json) ─────────────────────────

    def test_parse_info_output_json(self):
        ver, code = playstore._parse_info_output(
            '{"versionName": "2.372.0", "versionCode": 29663417}'
        )
        self.assertEqual(ver, "2.372.0")
        self.assertEqual(code, "29663417")

    def test_parse_info_output_table(self):
        ver, code = playstore._parse_info_output(
            "│ Version │ 2.372.0 (29663417) │"
        )
        self.assertEqual(ver, "2.372.0")
        self.assertEqual(code, "29663417")

    @patch('src.playstore.subprocess.run')
    def test_gplaydl_supports_json_detection(self, mock_run):
        playstore._JSON_SUPPORTED = None
        mock_run.return_value = Mock(stdout="--json --arch", stderr="")
        self.assertTrue(playstore._gplaydl_supports_json())
        playstore._JSON_SUPPORTED = None
        mock_run.return_value = Mock(stdout="--arch only", stderr="")
        self.assertFalse(playstore._gplaydl_supports_json())
        playstore._JSON_SUPPORTED = None


if __name__ == '__main__':
    unittest.main()
