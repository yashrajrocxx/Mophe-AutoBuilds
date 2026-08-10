import os
import unittest
from unittest.mock import patch, Mock

from src import playstore

class TestPlaystoreResolver(unittest.TestCase):

    def setUp(self):
        # Reset cache before each test
        playstore._exodus_cache = {}
        # Ensure API key is set for tests to pass auth check
        os.environ["EXODUS_API_KEY"] = "test_token"

    @patch('src.playstore.requests.get')
    def test_exact_match_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.canva.editor": {
                "reports": [
                    {"version": "2.371.0", "version_code": "29652157"},
                    {"version": "2.369.0", "version_code": "29633241"}
                ]
            }
        }
        mock_get.return_value = mock_response

        code = playstore.resolve_version_code("com.canva.editor", "2.371.0")
        self.assertEqual(code, 29652157)
        mock_get.assert_called_once()

    @patch('src.playstore.requests.get')
    def test_version_not_present(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.canva.editor": {
                "reports": [
                    {"version": "2.369.0", "version_code": "29633241"}
                ]
            }
        }
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.VersionNotFound):
            playstore.resolve_version_code("com.canva.editor", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_malformed_version_code(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.canva.editor": {
                "reports": [
                    {"version": "2.371.0", "version_code": "not_an_int"}
                ]
            }
        }
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            playstore.resolve_version_code("com.canva.editor", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_http_error(self, mock_get):
        import requests
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.RequestException("HTTP 401")
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.ExodusApiError):
            playstore.resolve_version_code("com.canva.editor", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_missing_package_key(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"different.package": {}}
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.ExodusApiError):
            playstore.resolve_version_code("com.canva.editor", "2.371.0")
            
    @patch('src.playstore.requests.get')
    def test_multiple_exact_matches(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.canva.editor": {
                "reports": [
                    {"version": "2.371.0", "version_code": "100"},
                    {"version": "2.371.0", "version_code": "200"}
                ]
            }
        }
        mock_get.return_value = mock_response

        # Should select max version code
        code = playstore.resolve_version_code("com.canva.editor", "2.371.0")
        self.assertEqual(code, 200)

if __name__ == '__main__':
    unittest.main()
