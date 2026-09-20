#!/usr/bin/env python3
"""Generate pages/public/downloads.html from manifest.json.

The page lists every published APK as a plain <a> link. It exists so the
HTML app source in Obtainium can track per-app versions: each app entry
filters this page's links by filename pattern and extracts the version
from the matched download URL.

This indirection is required because our single rolling GitHub release uses
the tag "latest" for every app — a release-title-based version regex can
never yield per-app versions. The filenames are the only per-app version
signal, and only the HTML source applies the extraction regex to links.
"""
import html
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO = "yashrajrocxx/Mophe-AutoBuilds"


def apk_download_url(repo_slug: str, apk_name: str) -> str:
    return f"https://github.com/{repo_slug}/releases/download/latest/{apk_name}"


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "pages" / "public" / "downloads.html"
    manifest_path = REPO_ROOT / "manifest.json"

    repo_slug = os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPO

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Cannot read {manifest_path}: {e}")
        return 1

    entries = manifest.get("entries", {})
    rows = []
    for key in sorted(entries):
        e = entries[key]
        apk = (e.get("apk") or "").strip()
        if not apk:
            continue
        rows.append({
            "app": e.get("app_name", ""),
            "arch": e.get("arch", ""),
            "source": e.get("source", ""),
            "version": e.get("built_version", ""),
            "package": e.get("package", ""),
            "apk": apk,
            "url": apk_download_url(repo_slug, apk),
        })

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Morphe Builds — Downloads</title>",
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "</head>",
        "<body>",
        "<h1>Morphe Builds — APK Downloads</h1>",
        "<p>Machine-readable catalog for update trackers. One link per published APK.</p>",
    ]
    for r in rows:
        parts.append(
            f'<section data-app="{html.escape(r["app"])}" '
            f'data-arch="{html.escape(r["arch"])}" '
            f'data-version="{html.escape(r["version"])}">'
            f'<a class="apk" href="{html.escape(r["url"])}" '
            f'data-version="{html.escape(r["version"])}" '
            f'data-arch="{html.escape(r["arch"])}">'
            f'{html.escape(r["apk"])}</a> '
            f'<span class="version">{html.escape(r["version"])}</span>'
            f"</section>"
        )
    parts += ["</body>", "</html>", ""]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"[OK] Wrote {out_path} ({len(rows)} APK links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
