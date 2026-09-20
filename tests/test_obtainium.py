import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_obtainium import build_obtainium_app


def _entry(app, arch, apk):
    return {"app_name": app, "arch": arch, "apk": apk, "package": f"com.example.{app}"}


def _settings(app_obj):
    return json.loads(app_obj["additionalSettings"])


BRAVE_URL = "https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/download/latest/brave-arm64-v8a-kveld9-v1.95.101.apk"
PAGES_URL = "https://yashrajrocxx.github.io/Mophe-AutoBuilds/downloads.html"


class TestObtainiumHtmlEntries(unittest.TestCase):
    """Entries target the downloads page (HTML source), never the repo releases.

    Background: current Obtainium applies versionExtractionRegEx to the
    release *tag* for GitHub sources. Our rolling release is tagged
    "latest", so any filename-shaped regex throws NoVersionError and every
    install fails version detection. The HTML source applies the regex to
    the matched download link instead — which is what these tests pin.
    """

    def _brave(self):
        return build_obtainium_app(
            "k", _entry("brave", "arm64-v8a", "brave-arm64-v8a-kveld9-v1.95.101.apk"),
            "u/r", "u", {}, PAGES_URL,
        )

    def test_points_at_downloads_page(self):
        self.assertEqual(self._brave()["url"], PAGES_URL)

    def test_new_pattern_resolves_live_link(self):
        s = _settings(self._brave())
        self.assertRegex(BRAVE_URL, s["apkFilterRegEx"])
        m = re.search(s["versionExtractionRegEx"], BRAVE_URL)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(int(s["matchGroupToUse"])), "1.95.101")

    def test_source_rename_survives(self):
        """A dh6k→kveld9 rename must not break tracking."""
        s = _settings(self._brave())
        old = BRAVE_URL.replace("-kveld9-", "-dh6k-patches-")
        self.assertRegex(old, s["apkFilterRegEx"])
        self.assertEqual(re.search(s["versionExtractionRegEx"], old).group(1), "1.95.101")

    def test_no_cross_app_match(self):
        yt = build_obtainium_app(
            "k", _entry("youtube", "arm64-v8a", "youtube-arm64-v8a-morphe-v1.0.apk"),
            "u/r", "u", {}, PAGES_URL,
        )
        filt = _settings(yt)["apkFilterRegEx"]
        self.assertRegex(
            "https://github.com/u/r/releases/download/latest/youtube-arm64-v8a-morphe-v1.0.apk", filt)
        self.assertNotRegex(
            "https://github.com/u/r/releases/download/latest/youtube-music-arm64-v8a-morphe-v1.0.apk", filt)

    def test_no_source_baked_in(self):
        s = _settings(self._brave())
        self.assertNotIn("kveld9", s["apkFilterRegEx"])
        self.assertNotIn("kveld9", s["versionExtractionRegEx"])

    def test_tag_latest_never_matches(self):
        """Guard: the patterns must be link-shaped. Applied to a bare release
        tag they must fail — silently matching tags is what broke installs."""
        s = _settings(self._brave())
        self.assertIsNone(re.search(s["versionExtractionRegEx"], "latest"))

    def test_bad_filename_raises(self):
        with self.assertRaises(ValueError):
            build_obtainium_app("k", _entry("x", "arm64-v8a", "not-an-apk"), "u/r", "u", {}, PAGES_URL)


if __name__ == "__main__":
    unittest.main()
