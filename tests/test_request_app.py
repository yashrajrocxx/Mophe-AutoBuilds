import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import request_app  # noqa: E402


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8", newline="\n")
    else:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def make_repo(root: Path) -> None:
    write(root / "patch-config.json", {
        "patch_list": [
            {"app_name": "youtube", "source": "morphe"},
            {"app_name": "twitter", "source": "piko-newx"},
        ]
    })
    write(root / "arch-config.json", [
        {"app_name": "youtube", "source": "morphe", "arches": ["arm64-v8a"]},
    ])
    write(root / "sources" / "morphe.json", [
        {"name": "morphe"},
        {"provider": "github", "user": "MorpheApp", "repo": "morphe-patches", "tag": "latest"},
    ])
    write(root / "sources" / "piko-newx.json", [
        {"name": "piko-newx-patches"},
        {"provider": "github", "user": "crimera", "repo": "piko-newx", "tag": "latest"},
    ])
    write(root / "sources" / "demo-patches.json", [
        {"name": "demo-patches"},
        {"provider": "github", "user": "someone", "repo": "other-patches", "tag": "latest"},
    ])
    write(root / "apps" / "playstore" / "youtube.json", {"package": "com.google.android.youtube"})
    write(root / "apps" / "apkmirror" / "youtube.json", {"package": "com.google.android.youtube"})


class TestNormalize(unittest.TestCase):
    def test_valid_known_source(self):
        request, error = request_app.normalize_request({
            "app_name": "Firefox", "package": "org.mozilla.firefox",
            "source": "morphe", "arch": "arm64-v8a", "code": "abc123",
        })
        self.assertIsNone(error)
        self.assertEqual(request["app_name"], "firefox")
        self.assertEqual(request["source"], "morphe")
        self.assertIsNone(request["repo_name"])
        self.assertEqual(request["code"], "abc123")

    def test_valid_universal_arch(self):
        request, error = request_app.normalize_request({
            "app_name": "Firefox", "package": "org.mozilla.firefox",
            "source": "morphe", "arch": "universal", "code": "abc123",
        })
        self.assertIsNone(error)
        self.assertEqual(request["arch"], "universal")

    def test_custom_repo_variants(self):
        for value in (
            "https://github.com/hoo-dles/morphe-patches",
            "github.com/hoo-dles/morphe-patches",
            "hoo-dles/morphe-patches",
            "https://github.com/hoo-dles/morphe-patches.git",
        ):
            request, error = request_app.normalize_request({
                "app_name": "demo", "package": "com.demo.app", "repo_url": value,
            })
            self.assertIsNone(error, value)
            self.assertEqual((request["repo_owner"], request["repo_name"]), ("hoo-dles", "morphe-patches"))

    def test_rejects_non_github_host(self):
        _, error = request_app.normalize_request({
            "app_name": "demo", "package": "com.demo.app", "repo_url": "example.com/morphe-patches",
        })
        self.assertEqual(error["code"], "invalid-repo")

    def test_rejects_bad_fields(self):
        cases = [
            ({"app_name": "Bad App", "package": "com.demo.app", "source": "morphe"}, "invalid-app"),
            ({"app_name": "demo", "package": "not-a-package", "source": "morphe"}, "invalid-package"),
            ({"app_name": "demo", "package": "com.demo.app", "source": "morphe", "arch": "mips"}, "invalid-arch"),
            ({"app_name": "demo", "package": "com.demo.app"}, "invalid-source"),
        ]
        for payload, expected in cases:
            _, error = request_app.normalize_request(payload)
            self.assertEqual(error["code"], expected, payload)

    def test_drops_unsafe_code(self):
        request, _ = request_app.normalize_request({
            "app_name": "demo", "package": "com.demo.app", "source": "morphe", "code": "bad code!",
        })
        self.assertEqual(request["code"], "")


class TestParsing(unittest.TestCase):
    BODY = """### Request

Some description here.

```json
{"app_name": "demo", "package": "com.demo.app", "source": "morphe", "arch": "arm64-v8a", "code": "k3f9q2"}
```

Thanks!
"""

    def test_parse_issue_body(self):
        payload = request_app.parse_json_payload(self.BODY)
        self.assertEqual(payload["app_name"], "demo")
        self.assertEqual(payload["code"], "k3f9q2")

    def test_parse_issue_body_without_fence(self):
        self.assertIsNone(request_app.parse_json_payload("no payload here"))

    def test_extract_marker(self):
        text = (
            "Request received.\n\n"
            '<!-- morphe-build-request {"app_name": "demo", "package": "com.demo.app", "source": "morphe"} -->\n'
        )
        payload = request_app.find_marker_payload(text)
        self.assertEqual(payload["package"], "com.demo.app")


class TestValidate(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def normalize(self, **overrides):
        payload = {"app_name": "demo", "package": "com.demo.app", "source": "morphe", "arch": "arm64-v8a"}
        payload.update(overrides)
        request, error = request_app.normalize_request(payload)
        self.assertIsNone(error)
        return request

    def test_accepts_and_writes_build_inputs(self):
        result = request_app.validate_and_write(self.normalize(), self.root)
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["register_catalog"])
        for relative in (
            "apps/playstore/demo.json",
            "apps/apkpure/demo.json",
            "apps/apkcombo/demo.json",
            "apps/uptodown/demo.json",
            "apps/aptoide/demo.json",
            "patches/demo-morphe.txt",
        ):
            self.assertIn(relative, result["files"])
            self.assertTrue((self.root / relative).exists(), relative)

        # A one-off request is not a catalog app until a maintainer keeps it.
        self.assertNotIn("patch-config.json", result["files"])
        self.assertNotIn("arch-config.json", result["files"])
        patch_config = json.loads((self.root / "patch-config.json").read_text(encoding="utf-8"))
        self.assertEqual(patch_config["patch_list"], [
            {"app_name": "youtube", "source": "morphe"},
            {"app_name": "twitter", "source": "piko-newx"},
        ])

        # Files stay LF-only with a trailing newline.
        for relative in result["files"]:
            raw = (self.root / relative).read_bytes()
            self.assertTrue(raw.endswith(b"\n"), relative)
            self.assertNotIn(b"\r\n", raw, relative)

    def test_register_catalog_writes_catalog_entries(self):
        result = request_app.validate_and_write(self.normalize(), self.root, register_catalog=True)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["register_catalog"])
        for relative in ("patch-config.json", "arch-config.json"):
            self.assertIn(relative, result["files"])
            self.assertTrue((self.root / relative).exists(), relative)

        patch_config = json.loads((self.root / "patch-config.json").read_text(encoding="utf-8"))
        self.assertIn({"app_name": "demo", "source": "morphe"}, patch_config["patch_list"])
        # Existing entries are preserved.
        self.assertEqual(patch_config["patch_list"][0], {"app_name": "youtube", "source": "morphe"})

        arch_config = json.loads((self.root / "arch-config.json").read_text(encoding="utf-8"))
        self.assertEqual(arch_config[-1], {"app_name": "demo", "source": "morphe", "arches": ["arm64-v8a"]})

    def test_rejects_existing_app(self):
        result = request_app.validate_and_write(self.normalize(app_name="youtube"), self.root)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["code"], "app-exists")
        self.assertEqual(result["existing_source"], "morphe")

    def test_rejects_existing_app_with_other_source(self):
        result = request_app.validate_and_write(
            self.normalize(app_name="twitter", repo_url="https://github.com/crimera/piko-newx"), self.root)
        self.assertEqual(result["code"], "app-exists")
        self.assertIn("different configuration", result["reason"])

    def test_rejects_package_in_use(self):
        result = request_app.validate_and_write(
            self.normalize(package="com.google.android.youtube"), self.root)
        self.assertEqual(result["code"], "package-in-use")
        self.assertIn("youtube", result["reason"])

    def test_rejects_unknown_source(self):
        result = request_app.validate_and_write(self.normalize(source="nope"), self.root)
        self.assertEqual(result["code"], "unknown-source")

    def test_custom_source_creates_source_file(self):
        result = request_app.validate_and_write(
            self.normalize(source="", repo_url="https://github.com/newowner/firefox-patches"), self.root)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["source"], "firefox-patches")
        self.assertEqual(result["source_kind"], "custom")
        source = json.loads((self.root / "sources" / "firefox-patches.json").read_text(encoding="utf-8"))
        self.assertEqual(source[1]["repo"], "firefox-patches")
        self.assertEqual(source[1]["user"], "newowner")
        self.assertEqual(source[2]["repo"], "morphe-cli")

    def test_custom_source_reuses_existing_source_for_same_repo(self):
        first = request_app.validate_and_write(
            self.normalize(source="", repo_url="hoo-dles/morphe-patches"), self.root)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["source"], "morphe-patches")

        second = request_app.validate_and_write(
            self.normalize(app_name="demo2", package="com.demo.two", source="", repo_url="hoo-dles/morphe-patches"),
            self.root,
        )
        self.assertEqual(second["status"], "ok")
        self.assertEqual(second["source"], "morphe-patches")
        # The existing source file is reused, not rewritten.
        self.assertNotIn("sources/morphe-patches.json", second["files"])

    def test_custom_source_name_taken(self):
        result = request_app.validate_and_write(
            self.normalize(source="", repo_url="https://github.com/other/demo-patches"), self.root)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["code"], "source-name-taken")

    def test_check_only_writes_nothing(self):
        result = request_app.validate_and_write(self.normalize(), self.root, check_only=True)
        self.assertEqual(result["status"], "ok")
        self.assertFalse((self.root / "apps" / "playstore" / "demo.json").exists())

        result = request_app.validate_and_write(
            self.normalize(), self.root, check_only=True, register_catalog=True)
        self.assertEqual(result["status"], "ok")
        patch_config = json.loads((self.root / "patch-config.json").read_text(encoding="utf-8"))
        self.assertNotIn({"app_name": "demo", "source": "morphe"}, patch_config["patch_list"])
        arch_config = json.loads((self.root / "arch-config.json").read_text(encoding="utf-8"))
        self.assertNotIn("demo", [entry["app_name"] for entry in arch_config])

    def test_known_source_reuse_writes_no_source_file(self):
        result = request_app.validate_and_write(self.normalize(), self.root)
        self.assertNotIn("sources/morphe.json", result["files"])


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        return request_app.main([str(a) for a in argv])

    def test_validate_cli_accepted(self):
        body = self.root / "payload.json"
        write(body, {"app_name": "demo", "package": "com.demo.app", "source": "morphe"})
        result = self.root / "result.json"
        code = self.run_cli("validate", "--payload-file", body, "--result-file", result, "--root", self.root)
        self.assertEqual(code, 0)
        data = json.loads(result.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "ok")

    def test_validate_cli_rejected(self):
        body = self.root / "payload.json"
        write(body, {"app_name": "youtube", "package": "com.demo.app", "source": "morphe"})
        result = self.root / "result.json"
        code = self.run_cli("validate", "--payload-file", body, "--result-file", result, "--root", self.root)
        self.assertEqual(code, 2)
        data = json.loads(result.read_text(encoding="utf-8"))
        self.assertEqual(data["code"], "app-exists")

    def test_validate_cli_register_catalog(self):
        body = self.root / "payload.json"
        write(body, {"app_name": "demo", "package": "com.demo.app", "source": "morphe"})
        result = self.root / "result.json"
        code = self.run_cli(
            "validate", "--register-catalog",
            "--payload-file", body, "--result-file", result, "--root", self.root)
        self.assertEqual(code, 0)
        patch_config = json.loads((self.root / "patch-config.json").read_text(encoding="utf-8"))
        self.assertIn({"app_name": "demo", "source": "morphe"}, patch_config["patch_list"])

    def test_parse_issue_cli(self):
        body = self.root / "body.md"
        write(body, TestParsing.BODY)
        result = self.root / "payload.json"
        code = self.run_cli("parse-issue", "--body-file", body, "--result-file", result)
        self.assertEqual(code, 0)
        data = json.loads(result.read_text(encoding="utf-8"))
        self.assertEqual(data["payload"]["app_name"], "demo")

    def test_parse_issue_cli_unparseable(self):
        body = self.root / "body.md"
        write(body, "nothing to see")
        result = self.root / "payload.json"
        code = self.run_cli("parse-issue", "--body-file", body, "--result-file", result)
        self.assertEqual(code, 2)
        data = json.loads(result.read_text(encoding="utf-8"))
        self.assertEqual(data["code"], "unparseable")


if __name__ == "__main__":
    unittest.main()
