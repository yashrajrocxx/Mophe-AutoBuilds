#!/usr/bin/env python3
"""Generate pages/public/patch_lists.json from patches/*.txt.

Output maps "<app>|<source>" -> {"include": [...], "exclude": [...]} so the
web dashboard can show exactly which patches are enabled/disabled per build.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def split_app_source(stem: str, sources: set[str]) -> tuple[str, str]:
    """Split '<app>-<source>' using longest-source-match (handles dashes)."""
    for src in sorted(sources, key=len, reverse=True):
        if stem.endswith(f"-{src}"):
            app = stem[: -(len(src) + 1)]
            if app:
                return app, src
    if "-" in stem:
        app, src = stem.rsplit("-", 1)
        return app, src
    return stem, ""


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "pages" / "public" / "patch_lists.json"

    sources = {p.stem for p in (REPO_ROOT / "sources").glob("*.json")}
    try:
        patch_config = json.loads((REPO_ROOT / "patch-config.json").read_text(encoding="utf-8"))
        sources |= {item.get("source", "") for item in patch_config.get("patch_list", [])}
    except Exception:
        pass
    sources.discard("")

    result: dict[str, dict[str, list[str]]] = {}
    for txt in sorted((REPO_ROOT / "patches").glob("*.txt")):
        app, src = split_app_source(txt.stem, sources)
        include: list[str] = []
        exclude: list[str] = []
        for line in txt.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("+"):
                include.append(line[1:].strip())
            elif line.startswith("-"):
                exclude.append(line[1:].strip())
        result[f"{app}|{src}"] = {"include": include, "exclude": exclude}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {out_path} ({len(result)} patch lists)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
