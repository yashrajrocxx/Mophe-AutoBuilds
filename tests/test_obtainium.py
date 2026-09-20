import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_obtainium import build_obtainium_app


def _entry(app, arch, apk):
    return {"app_name": app, "arch": arch, "apk": apk, "package": f"com.example.{app}"}


class TestObtainiumPatterns(unittest.TestCase):

    def test_source_rename_survives(self):
        """A dh6k→kveld9 rename must not break tracking (the reported bug)."""
        old = build_obtainium_app("k", _entry("brave", "arm64-v8a", "brave-arm64-v8a-dh6k-patches-v1.95.101.apk"), "u/r", "u", {})
        import json
        s = json.loads(old["additionalSettings"])
        for apk in ("brave-arm64-v8a-dh6k-patches-v1.95.101.apk",
                    "brave-arm64-v8a-kveld9-v1.95.104.apk"):
            self.assertRegex(apk, s["apkFilterRegEx"])
            m = re.match(s["versionExtractionRegEx"], apk)
            self.assertIsNotNone(m)
        self.assertEqual(re.match(s["versionExtractionRegEx"], "brave-arm64-v8a-kveld9-v1.95.104.apk").group(1), "1.95.104")

    def test_no_cross_app_match(self):
        app = build_obtainium_app("k", _entry("youtube", "arm64-v8a", "youtube-arm64-v8a-morphe-v1.0.apk"), "u/r", "u", {})
        import json
        filt = json.loads(app["additionalSettings"])["apkFilterRegEx"]
        self.assertRegex("youtube-arm64-v8a-morphe-v1.0.apk", filt)
        self.assertNotRegex("youtube-music-arm64-v8a-morphe-v1.0.apk", filt)

    def test_no_source_baked_in(self):
        app = build_obtainium_app("k", _entry("instagram", "arm64-v8a", "instagram-arm64-v8a-piko-patches-v1.0.apk"), "u/r", "u", {})
        import json
        s = json.loads(app["additionalSettings"])
        self.assertNotIn("piko", s["apkFilterRegEx"])
        self.assertNotIn("piko", s["versionExtractionRegEx"])

    def test_bad_filename_raises(self):
        with self.assertRaises(ValueError):
            build_obtainium_app("k", _entry("x", "arm64-v8a", "not-an-apk", ), "u/r", "u", {})


if __name__ == "__main__":
    unittest.main()
