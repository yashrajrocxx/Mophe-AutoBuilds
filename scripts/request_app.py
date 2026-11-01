#!/usr/bin/env python3
"""Build-request handling for the Pages "Request a build" flow.

The GitHub Pages site is static, so it cannot run a build by itself. It submits
a structured GitHub issue instead, and ``.github/workflows/request-app.yml``
picks that issue up and calls this module to:

1. parse the request payload out of the issue body (``parse-issue``) or out of
   the bot's stored payload comment (``extract-marker``),
2. validate the payload against the current repository state and, when it is
   accepted, write the files the build needs (``validate``).

A request builds immediately - no approval label is involved. ``validate``
therefore only writes the build inputs (``apps/*``, ``patches/*`` and, for
custom patch repositories, ``sources/*``). The app joins the recurring build
catalog only when a maintainer adds the ``keep`` label to the issue, which
reruns ``validate`` with ``--register-catalog`` to also add the
``patch-config.json`` / ``arch-config.json`` entries. Without ``keep`` the APK
stays available in the release but is not published in the store and is not
rebuilt automatically.

Design notes:
- Stdlib only: this runs before ``pip install`` in CI and is unit-tested
  without the project's runtime dependencies.
- Everything that can be decided from repository files is decided here. The
  workflow only adds the checks that need network access (patch repo releases).
- Exit codes: 0 accepted, 2 rejected with a user-facing reason, 1 unexpected.

Usage:
    python scripts/request_app.py parse-issue    --body-file body.md --result-file payload.json
    python scripts/request_app.py extract-marker --text-file text.txt --result-file payload.json
    python scripts/request_app.py validate       --payload-file payload.json --result-file result.json
    python scripts/request_app.py validate --register-catalog --payload-file payload.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

LOGGER = logging.getLogger("request-app")

MARKER_START = "<!-- morphe-build-request"
MARKER_END = "-->"

APP_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")
PACKAGE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)+$")
GITHUB_URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_SHORT_RE = re.compile(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
CODE_RE = re.compile(r"^[a-z0-9]{4,16}$")
FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)
MARKER_RE = re.compile(
    re.escape(MARKER_START) + r"\s*(\{.*?\})\s*" + re.escape(MARKER_END), re.DOTALL
)

ARCHES = ("arm64-v8a", "universal")
DEFAULT_ARCH = "arm64-v8a"

APP_PLATFORMS = ("playstore", "apkpure", "apkcombo", "uptodown", "aptoide")

PATCH_FILE_TEMPLATE = (
    "# {source} patches for {app}\n"
    "# Left empty to apply all default recommended patches automatically.\n"
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def rejection(code: str, reason: str, **extra) -> dict:
    result = {"status": "rejected", "code": code, "reason": reason}
    result.update(extra)
    return result


def slugify(value: str, limit: int = 40) -> str:
    """Lowercase, dash-separated slug safe to use as a file name."""
    value = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:limit].strip("-")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_repo(value: str):
    """Return (owner, repo) for a GitHub repository reference, else None.

    Accepts ``owner/repo``, ``github.com/owner/repo`` and full URLs with an
    optional ``.git`` suffix. GitHub owners only use letters, digits and single
    hyphens, which also keeps non-GitHub hosts (``example.com/x``) out.
    """
    value = (value or "").strip()
    for pattern in (GITHUB_URL_RE, GITHUB_SHORT_RE):
        match = pattern.match(value)
        if not match:
            continue
        owner, repo = match.group(1), match.group(2)
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", owner):
            return None
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repo):
            return None
        return owner, repo
    return None


def parse_json_payload(text: str):
    """Find the first fenced code block that holds a request payload."""
    for raw in FENCE_RE.findall(text or ""):
        try:
            data = json.loads(raw)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("app_name"):
            return data
    return None


def find_marker_payload(text: str):
    """Find the payload stored in a bot comment marker."""
    match = MARKER_RE.search(text or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------------------
# Request normalization
# ---------------------------------------------------------------------------
def normalize_request(payload: dict):
    """Return (normalized, None) or (None, rejection)."""
    if not isinstance(payload, dict):
        return None, rejection("unparseable", "The request payload could not be read.")

    app = str(payload.get("app_name") or "").strip().lower()
    if not APP_RE.match(app):
        return None, rejection(
            "invalid-app",
            "The app name must be 2-40 characters: lowercase letters, digits and dashes.",
        )

    package = str(payload.get("package") or payload.get("package_name") or "").strip()
    if not PACKAGE_RE.match(package) or len(package) > 255:
        return None, rejection(
            "invalid-package",
            f"'{package}' is not a valid Android package name (example: com.example.app).",
        )

    arch = str(payload.get("arch") or payload.get("architecture") or DEFAULT_ARCH).strip().lower()
    if arch not in ARCHES:
        return None, rejection("invalid-arch", f"Architecture must be one of: {', '.join(ARCHES)}.")

    repo = str(payload.get("repo_url") or payload.get("repo") or "").strip()
    source = str(payload.get("source") or "").strip().lower()
    code = str(payload.get("code") or "").strip().lower()

    if code and not CODE_RE.match(code):
        code = ""

    repo_owner = repo_name = None
    if repo:
        parsed = parse_repo(repo)
        if not parsed:
            return None, rejection(
                "invalid-repo",
                "The patch repository must be a public GitHub repository (owner/repo).",
            )
        repo_owner, repo_name = parsed
    elif not source:
        return None, rejection(
            "invalid-source",
            "Select a patch source or provide a custom GitHub patch repository.",
        )

    if source and not APP_RE.match(source):
        return None, rejection("invalid-source", f"'{source}' is not a valid patch source id.")

    return {
        "app_name": app,
        "package": package,
        "arch": arch,
        "source": source,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "code": code,
    }, None


def repo_matches_source_entry(entry, owner: str, repo: str) -> bool:
    if not isinstance(entry, dict):
        return False
    entry_repo = str(entry.get("repo") or "").strip()
    if not entry_repo:
        return False
    if "/" in entry_repo:
        entry = dict(entry)
        entry_owner, _, entry_repo = entry_repo.partition("/")
    else:
        entry_owner = str(entry.get("user") or entry.get("owner") or "").strip()
    return (
        entry_owner.lower() == owner.lower()
        and entry_repo.lower() == repo.lower()
    )


def available_sources(root: Path) -> list[str]:
    return sorted(p.stem for p in (root / "sources").glob("*.json"))


# ---------------------------------------------------------------------------
# Validation + catalog writing
# ---------------------------------------------------------------------------
def app_in_catalog(patch_list, app: str):
    for entry in patch_list:
        if isinstance(entry, dict) and str(entry.get("app_name") or "").lower() == app:
            return entry
    return None


def package_owner(root: Path, package: str, exclude_app: str):
    """Return (app, platform) when another app config already uses the package."""
    target = package.lower()
    apps_dir = root / "apps"
    if not apps_dir.is_dir():
        return None
    for platform_dir in sorted(apps_dir.iterdir()):
        if not platform_dir.is_dir():
            continue
        for config_path in sorted(platform_dir.glob("*.json")):
            if config_path.stem.lower() == exclude_app:
                continue
            data = read_json(config_path)
            if isinstance(data, dict) and str(data.get("package") or "").lower() == target:
                return config_path.stem, platform_dir.name
    return None


def validate_request(request: dict, root: Path):
    """Return (plan, None) or (None, rejection)."""
    app = request["app_name"]
    package = request["package"]

    patch_config_path = root / "patch-config.json"
    patch_config = read_json(patch_config_path)
    if not isinstance(patch_config, dict):
        return None, rejection("catalog-missing", "The build catalog (patch-config.json) could not be read.")

    existing = app_in_catalog(patch_config.get("patch_list") or [], app)
    if existing:
        existing_source = existing.get("source", "unknown")
        if existing_source == request["source"] and not request["repo_name"]:
            reason = (
                f"An app named '{app}' is already in the build catalog "
                f"(patch source: {existing_source})."
            )
        else:
            reason = (
                f"An app named '{app}' is already in the build catalog with a different "
                f"configuration (current source: {existing_source}; requested: "
                f"{request['repo_name'] or request['source'] or 'unknown'})."
            )
        return None, rejection(
            "app-exists",
            reason + " It is rebuilt automatically whenever the patch source or app version changes.",
            app=app,
            existing_source=existing_source,
        )

    owner_app = package_owner(root, package, app)
    if owner_app:
        return None, rejection(
            "package-in-use",
            f"The package '{package}' is already used by the app '{owner_app[0]}' "
            f"(apps/{owner_app[1]}/{owner_app[0]}.json). Two catalog entries cannot "
            "share one package name.",
            app=app,
            package=package,
        )

    source = request["source"]
    source_kind = "known"
    source_exists = True
    repo = None

    if request["repo_name"]:
        owner, repo_name = request["repo_owner"], request["repo_name"]
        source = slugify(repo_name) or slugify(owner)
        if not source or not APP_RE.match(source):
            return None, rejection(
                "invalid-repo",
                "The patch repository name cannot be turned into a source id; "
                "use a repository with letters, digits and dashes in its name.",
            )
        source_kind = "custom"
        repo = (owner, repo_name)
        source_path = root / "sources" / f"{source}.json"
        existing_source = read_json(source_path)
        if existing_source is None:
            source_exists = False
        elif not any(
            repo_matches_source_entry(entry, owner, repo_name)
            for entry in (existing_source if isinstance(existing_source, list) else [])
        ):
            return None, rejection(
                "source-name-taken",
                f"A patch source named '{source}' already exists for a different repository. "
                "Rename the patch repository or ask a maintainer to add it manually.",
                app=app,
            )
    else:
        if not (root / "sources" / f"{source}.json").exists():
            known = ", ".join(available_sources(root)) or "none"
            return None, rejection(
                "unknown-source",
                f"Patch source '{source}' does not exist. Available sources: {known}.",
                app=app,
            )

    plan = {
        "app_name": app,
        "package": package,
        "arch": request["arch"],
        "source": source,
        "source_kind": source_kind,
        "source_exists": source_exists,
        "repo": repo,
        "code": request["code"],
    }
    return plan, None


def build_catalog_files(plan: dict, root: Path, register_catalog: bool = False):
    """Return an ordered list of (relative_path, content_writer) for the plan.

    The build inputs are always written so the manual build can run. The
    patch-config.json / arch-config.json entries are only written when
    ``register_catalog`` is set, which the workflow does for the ``keep``
    label: without it the app is a one-off build instead of a catalog app.
    """
    app = plan["app_name"]
    package = plan["package"]
    source = plan["source"]

    files = []
    files.append((f"apps/playstore/{app}.json", {"package": package, "version": ""}))
    files.append((f"apps/apkpure/{app}.json", {"name": app, "package": package, "version": ""}))
    files.append((f"apps/apkcombo/{app}.json", {"slug": app, "package": package}))
    files.append((f"apps/uptodown/{app}.json", {"name": app, "package": package, "version": ""}))
    files.append((f"apps/aptoide/{app}.json", {"package": package, "version": ""}))
    files.append((
        f"patches/{app}-{source}.txt",
        PATCH_FILE_TEMPLATE.format(source=source, app=app),
    ))

    if plan["source_kind"] == "custom" and not plan.get("source_exists"):
        owner, repo_name = plan["repo"]
        files.append((
            f"sources/{source}.json",
            [
                {"name": source},
                {"provider": "github", "user": owner, "repo": repo_name, "tag": "latest"},
                {"provider": "github", "user": "MorpheApp", "repo": "morphe-cli", "tag": "latest"},
            ],
        ))

    if register_catalog:
        patch_config = read_json(root / "patch-config.json")
        if isinstance(patch_config, dict):
            patch_config.setdefault("patch_list", []).append({"app_name": app, "source": source})
            files.append(("patch-config.json", patch_config))

        arch_config = read_json(root / "arch-config.json") or []
        if isinstance(arch_config, list):
            arch_config.append({"app_name": app, "source": source, "arches": [plan["arch"]]})
            files.append(("arch-config.json", arch_config))

    return files


def write_catalog_files(
    plan: dict, root: Path, check_only: bool = False, register_catalog: bool = False
) -> list[str]:
    written = []
    for relative, content in build_catalog_files(plan, root, register_catalog=register_catalog):
        written.append(relative)
        if check_only:
            continue
        path = root / relative
        if isinstance(content, str):
            write_text(path, content)
        else:
            write_json(path, content)
    return written


def validate_and_write(
    request: dict, root: Path, check_only: bool = False, register_catalog: bool = False
):
    plan, error = validate_request(request, root)
    if error:
        return error
    written = write_catalog_files(
        plan, root, check_only=check_only, register_catalog=register_catalog
    )
    return {
        "status": "ok",
        "app": plan["app_name"],
        "package": plan["package"],
        "source": plan["source"],
        "source_kind": plan["source_kind"],
        "arch": plan["arch"],
        "repo": f"{plan['repo'][0]}/{plan['repo'][1]}" if plan["repo"] else "",
        "code": plan["code"],
        "files": written,
        "check_only": check_only,
        "register_catalog": register_catalog,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def write_result(result: dict, result_file: str | None) -> None:
    text = json.dumps(result, indent=2)
    if result_file:
        write_json(Path(result_file), result)
    else:
        print(text)


def cmd_parse_issue(args) -> int:
    body = Path(args.body_file).read_text(encoding="utf-8", errors="replace")
    payload = parse_json_payload(body) or find_marker_payload(body)
    if not payload:
        write_result(rejection("unparseable", "No request payload was found in the issue body."), args.result_file)
        return 2
    write_result({"status": "ok", "payload": payload}, args.result_file)
    return 0


def cmd_extract_marker(args) -> int:
    text = Path(args.text_file).read_text(encoding="utf-8", errors="replace")
    payload = find_marker_payload(text)
    if not payload:
        write_result(rejection("unparseable", "No stored request payload was found."), args.result_file)
        return 2
    write_result({"status": "ok", "payload": payload}, args.result_file)
    return 0


def cmd_validate(args) -> int:
    payload = read_json(Path(args.payload_file))
    if not isinstance(payload, dict):
        write_result(rejection("unparseable", "The request payload could not be read."), args.result_file)
        return 2

    # Accept both a bare payload and the wrapper written by parse-issue.
    if isinstance(payload.get("payload"), dict):
        payload = payload["payload"]

    request, error = normalize_request(payload)
    if error:
        write_result(error, args.result_file)
        return 2

    result = validate_and_write(
        request,
        Path(args.root).resolve(),
        check_only=args.check_only,
        register_catalog=args.register_catalog,
    )
    write_result(result, args.result_file)
    return 0 if result.get("status") == "ok" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_parse = sub.add_parser("parse-issue", help="Extract the request payload from an issue body")
    p_parse.add_argument("--body-file", required=True)
    p_parse.add_argument("--result-file", default="")
    p_parse.set_defaults(func=cmd_parse_issue)

    p_marker = sub.add_parser("extract-marker", help="Extract the stored payload from bot comment text")
    p_marker.add_argument("--text-file", required=True)
    p_marker.add_argument("--result-file", default="")
    p_marker.set_defaults(func=cmd_extract_marker)

    p_validate = sub.add_parser("validate", help="Validate a payload and write the build files")
    p_validate.add_argument("--payload-file", required=True)
    p_validate.add_argument("--result-file", default="")
    p_validate.add_argument("--root", default=".")
    p_validate.add_argument("--check-only", action="store_true")
    p_validate.add_argument(
        "--register-catalog",
        action="store_true",
        help="Also add the app to patch-config.json / arch-config.json (the keep step)",
    )
    p_validate.set_defaults(func=cmd_validate)

    return parser


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.error("request_app failed: %s", exc)
        write_result({"status": "error", "reason": str(exc)}, getattr(args, "result_file", None))
        return 1


if __name__ == "__main__":
    sys.exit(main())
