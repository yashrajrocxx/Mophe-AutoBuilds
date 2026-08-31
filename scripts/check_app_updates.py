#!/usr/bin/env python3
"""
Incremental update checker for Morphe AutoBuilds.

Strategy:
1. Read patch-config.json + arch-config.json -> full expected matrix.
2. Fetch existing 'latest' release manifest (manifest.json asset, if present).
3. For each (app, source, arch):
   - Determine current configured app version (from apps/<platform>/<app>.json).
   - Determine current patch-source signature & release changelog (from repos in sources/<source>.json).
   - Compare to manifest.json:
     * If patch source updated (new tag/release/commit) -> REBUILD & extract upstream changelog.
     * If app config version changed -> REBUILD.
     * If APK asset is missing from release -> REBUILD.
     * Otherwise -> CARRY OVER existing APK (no rebuild needed).
4. Output:
   - GitHub Actions outputs: build_matrix (JSON), has_updates, total/update counts.
   - File: build_matrix.json     (matrix entries that need rebuild).
   - File: carry_over.json       (existing APK names to re-upload unchanged).
   - File: new_manifest.json     (manifest to upload with the new release).
   - File: patch_changelogs.json (extracted changelogs for updated patch sources).
"""
import os
import sys
import re
import json
import logging
import subprocess
import traceback
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PATCH_CONFIG = REPO_ROOT / "patch-config.json"
ARCH_CONFIG = REPO_ROOT / "arch-config.json"
SOURCES_DIR = REPO_ROOT / "sources"
APPS_DIR = REPO_ROOT / "apps"

MANIFEST_NAME = "manifest.json"
RELEASE_TAG = "latest"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
FORCE_FULL = os.environ.get("FORCE_FULL_REBUILD", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def write_gh_output(key: str, value: str) -> None:
    """Append key=value to GITHUB_OUTPUT or print locally."""
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        preview = value if len(value) < 200 else value[:200] + "..."
        print(f"[gh-output] {key}={preview}")
        return
    with open(out, "a", encoding="utf-8") as f:
        if "\n" in value:
            f.write(f"{key}<<EOF_GH\n{value}\nEOF_GH\n")
        else:
            f.write(f"{key}={value}\n")


def run_gh(args: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    """Run `gh ...`; returns (rc, stdout, stderr). Never raises."""
    env = os.environ.copy()
    if GITHUB_TOKEN and "GH_TOKEN" not in env:
        env["GH_TOKEN"] = GITHUB_TOKEN
    try:
        p = subprocess.run(
            ["gh", *args],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "gh CLI not found"
    except Exception as e:
        return 1, "", f"{e}"


def run_github_api(endpoint: str, timeout: int = 60) -> Optional[Any]:
    """Fetch from GitHub API using `gh api` or HTTPS session as fallback."""
    clean_endpoint = endpoint.lstrip("/")
    
    # Try gh CLI first
    rc, out, _ = run_gh(["api", clean_endpoint], timeout=timeout)
    if rc == 0 and out.strip():
        try:
            return json.loads(out)
        except Exception:
            pass

    # Fallback to HTTPS API
    url = f"https://api.github.com/{clean_endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Morphe-AutoBuilds/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        
    try:
        resp = provider_utils.session.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            logging.debug(f"GitHub API {clean_endpoint} HTTP {resp.status_code}")
    except Exception as e:
        logging.debug(f"GitHub API {clean_endpoint} exception: {e}")
        
    return None


def load_patch_config() -> List[dict]:
    with PATCH_CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f).get("patch_list", [])


def load_arch_config() -> Dict[Tuple[str, str], List[str]]:
    if not ARCH_CONFIG.exists():
        return {}
    with ARCH_CONFIG.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        (e["app_name"], e["source"]): e.get("arches", ["universal"])
        for e in data
    }


def load_app_config_version(app_name: str) -> str:
    """Return the configured 'version' field from the first matching app config."""
    cfg, _ = load_app_config(app_name)
    return (cfg.get("version") or "").strip() if cfg else ""


def load_app_config(app_name: str) -> Tuple[Optional[dict], Optional[str]]:
    for platform in ("playstore", "apkmirror", "apkpure", "uptodown", "aptoide"):
        fp = APPS_DIR / platform / f"{app_name}.json"
        if fp.exists():
            try:
                with fp.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return data, platform
            except Exception:
                continue
    return None, None


def get_app_package_name(app_name: str) -> str:
    config, _ = load_app_config(app_name)
    return config.get("package", "") if config else ""


def fetch_app_icon(package: str) -> str:
    if not package:
        return ""
    url = f"https://play.google.com/store/apps/details?id={package}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            img = soup.find("img", {"alt": "Icon image"})
            if img and img.get("src"):
                return img.get("src")
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Source-signature & Release Info: detect when patch repos publish new releases
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import utils as provider_utils
from record_build import extract_version_from_filename

_repo_sig_cache: Dict[Tuple[str, str, str, str], str] = {}
_github_release_cache: Dict[Tuple[str, str, str], Optional[dict]] = {}
_repo_release_info_cache: Dict[Tuple[str, str, str, str], dict] = {}


def fetch_repo_signature(user: str, repo: str, tag: str, provider: str = "github") -> str:
    key = (user, repo, tag, provider)
    if key in _repo_sig_cache:
        return _repo_sig_cache[key]

    try:
        if provider == "gitlab":
            sig = _fetch_gitlab_signature(repo, tag)
        elif provider == "codeberg":
            sig = _fetch_codeberg_signature(user, repo, tag)
        else:
            sig = _fetch_github_signature(user, repo, tag)
        _repo_sig_cache[key] = sig
        return sig
    except Exception as e:
        sig = f"{tag}@err:{type(e).__name__}"
        _repo_sig_cache[key] = sig
        logging.warning(f"  {provider} api failed for {user}/{repo}: {e}")
        return sig


def _fetch_default_branch_sha(user: str, repo: str) -> str:
    try:
        data = run_github_api(f"repos/{user}/{repo}")
        branch = "main"
        if isinstance(data, dict):
            branch = data.get("default_branch") or "main"
        commit_data = run_github_api(f"repos/{user}/{repo}/commits/{branch}")
        if isinstance(commit_data, dict):
            sha = commit_data.get("sha") or ""
            if sha:
                return sha[:12]
    except Exception:
        pass
    return ""


def _fetch_github_release_dict(user: str, repo: str, tag: str) -> Optional[dict]:
    key = (user, repo, tag)
    if key in _github_release_cache:
        return _github_release_cache[key]

    if tag == "latest":
        api = f"repos/{user}/{repo}/releases/latest"
    elif tag in ("", "dev", "prerelease"):
        api = f"repos/{user}/{repo}/releases?per_page=10"
    else:
        api = f"repos/{user}/{repo}/releases/tags/{tag}"

    data = run_github_api(api)
    if data is None and tag == "latest":
        data = run_github_api(f"repos/{user}/{repo}/releases?per_page=10")

    if not data:
        _github_release_cache[key] = None
        return None

    if isinstance(data, list):
        if tag == "dev":
            data = [r for r in data if "dev" in (r.get("tag_name") or "").lower()]
        elif tag == "prerelease":
            data = [r for r in data if r.get("prerelease")]
        if not data:
            _github_release_cache[key] = None
            return None
        data.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        rel = data[0]
    else:
        rel = data

    _github_release_cache[key] = rel
    return rel


def _fetch_github_signature(user: str, repo: str, tag: str) -> str:
    rel = _fetch_github_release_dict(user, repo, tag)
    if not rel:
        sha = _fetch_default_branch_sha(user, repo)
        if sha:
            return f"@|sha:{sha}"
        raise RuntimeError(f"no release and no default-branch sha for {user}/{repo}/{tag}")

    tag_name = rel.get("tag_name") or rel.get("name") or "?"
    published = rel.get("published_at") or rel.get("created_at") or "?"
    updated = rel.get("updated_at") or ""

    assets = rel.get("assets") or []
    asset_parts: List[str] = []
    if isinstance(assets, list):
        for a in assets:
            if not isinstance(a, dict):
                continue
            name = (a.get("name") or "").strip()
            if not name:
                continue
            digest = (a.get("digest") or "").strip()
            a_updated = (a.get("updated_at") or "").strip()
            size = str(a.get("size") or "").strip()
            token = digest or (f"{size}@{a_updated}" if size and a_updated else (a_updated or size))
            asset_parts.append(f"{name}:{token}")
    asset_parts.sort()
    assets_sig = ",".join(asset_parts)

    sha = _fetch_default_branch_sha(user, repo)
    sha_part = f"|sha:{sha}" if sha else ""
    return f"{tag_name}@{published}@{updated}|{assets_sig}{sha_part}"


def _fetch_gitlab_signature(project: str, tag: str) -> str:
    from urllib.parse import quote
    encoded = quote(project, safe="")
    if tag == "latest":
        api = f"https://gitlab.com/api/v4/projects/{encoded}/releases/permalink/latest"
    elif tag in ("", "dev", "prerelease"):
        api = f"https://gitlab.com/api/v4/projects/{encoded}/releases"
    else:
        api = f"https://gitlab.com/api/v4/projects/{encoded}/releases/{quote(tag, safe='')}"

    data = provider_utils.fetch_json(api)
    if isinstance(data, list):
        data = data[0] if data else {}
    tag_name = data.get("tag_name") or "?"
    published = data.get("released_at") or data.get("created_at") or "?"
    return f"{tag_name}@{published}"


def _fetch_codeberg_signature(user: str, repo: str, tag: str) -> str:
    from urllib.parse import quote
    base = f"https://codeberg.org/api/v1/repos/{user}/{repo}/releases"
    if tag == "latest":
        api = f"{base}/latest"
    elif tag in ("", "dev", "prerelease"):
        api = base
    else:
        api = f"{base}/tags/{quote(tag, safe='')}"

    data = provider_utils.fetch_json(api)
    tag_name = data.get("tag_name") or "?"
    published = data.get("published_at") or "?"
    return f"{tag_name}@{published}"


def _fetch_bundle_signature(bundle_url: str) -> str:
    try:
        data = provider_utils.fetch_json(bundle_url)
    except Exception as e:
        logging.warning(f"  bundle fetch failed for {bundle_url}: {e}")
        return f"bundle:{bundle_url}@err"

    if not isinstance(data, dict):
        return f"bundle:{bundle_url}@unparseable"

    tokens: List[str] = []
    for key in ("patches", "integrations"):
        for item in data.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            name = (item.get("name") or "").strip()
            if url or name:
                tokens.append(f"{key}:{name}:{url}")
    tokens.sort()
    body = ",".join(tokens)
    return f"bundle:{body}" if body else f"bundle:{bundle_url}@empty"


def fetch_repo_release_info(user: str, repo: str, tag: str, provider: str = "github") -> dict:
    key = (user, repo, tag, provider)
    if key in _repo_release_info_cache:
        return _repo_release_info_cache[key]

    info = {
        "provider": provider,
        "user": user,
        "repo": repo,
        "tag": tag,
        "title": "",
        "body": "",
        "published_at": "",
        "url": "",
    }

    try:
        if provider == "gitlab":
            from urllib.parse import quote
            encoded = quote(repo, safe="")
            if tag == "latest":
                api = f"https://gitlab.com/api/v4/projects/{encoded}/releases/permalink/latest"
            elif tag in ("", "dev", "prerelease"):
                api = f"https://gitlab.com/api/v4/projects/{encoded}/releases"
            else:
                api = f"https://gitlab.com/api/v4/projects/{encoded}/releases/{quote(tag, safe='')}"
            data = provider_utils.fetch_json(api)
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict):
                tag_name = data.get("tag_name") or tag
                info["tag"] = tag_name
                info["title"] = data.get("name") or tag_name
                info["body"] = data.get("description") or ""
                info["published_at"] = data.get("released_at") or data.get("created_at") or ""
                info["url"] = f"https://gitlab.com/{repo}/-/releases/{tag_name}"

        elif provider == "codeberg":
            from urllib.parse import quote
            base = f"https://codeberg.org/api/v1/repos/{user}/{repo}/releases"
            if tag == "latest":
                api = f"{base}/latest"
            elif tag in ("", "dev", "prerelease"):
                api = base
            else:
                api = f"{base}/tags/{quote(tag, safe='')}"
            data = provider_utils.fetch_json(api)
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict):
                tag_name = data.get("tag_name") or tag
                info["tag"] = tag_name
                info["title"] = data.get("name") or tag_name
                info["body"] = data.get("body") or ""
                info["published_at"] = data.get("published_at") or ""
                info["url"] = f"https://codeberg.org/{user}/{repo}/releases/tag/{tag_name}"

        else: # GitHub
            rel = _fetch_github_release_dict(user, repo, tag)
            if rel:
                tag_name = rel.get("tag_name") or tag
                info["tag"] = tag_name
                info["title"] = rel.get("name") or tag_name
                info["body"] = rel.get("body") or ""
                info["published_at"] = rel.get("published_at") or rel.get("created_at") or ""
                info["url"] = rel.get("html_url") or f"https://github.com/{user}/{repo}/releases/tag/{tag_name}"

    except Exception as e:
        logging.debug(f"fetch_repo_release_info failed for {provider}:{user}/{repo}: {e}")

    _repo_release_info_cache[key] = info
    return info


_source_patch_info_cache: Dict[str, dict] = {}

def get_source_patch_info(source: str) -> dict:
    if source in _source_patch_info_cache:
        return _source_patch_info_cache[source]

    src_file = SOURCES_DIR / f"{source}.json"
    if not src_file.exists():
        for f in SOURCES_DIR.glob("*.json"):
            if f.stem.lower() == source.lower():
                src_file = f
                break

    result = {
        "source": source,
        "tag": "",
        "title": "",
        "url": "",
        "body": "",
        "published_at": "",
        "repos": [],
    }

    if not src_file.exists():
        _source_patch_info_cache[source] = result
        return result

    try:
        with src_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        _source_patch_info_cache[source] = result
        return result

    if isinstance(data, dict) and "bundle_url" in data:
        result["tag"] = "bundle"
        result["url"] = data["bundle_url"]
        result["title"] = data.get("name", "bundle-patches")
        _source_patch_info_cache[source] = result
        return result

    repos_info = []
    primary_patch_info = None

    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            provider = (entry.get("provider") or "github").lower().strip()
            tag = entry.get("tag", "latest")
            user = (entry.get("user") or "").strip()
            repo = (entry.get("repo") or entry.get("project") or "").strip()
            if not repo:
                continue

            r_info = fetch_repo_release_info(user, repo, tag, provider)
            is_cli = "cli" in repo.lower()
            is_patches = "patch" in repo.lower() or not is_cli

            r_info_copy = dict(r_info)
            r_info_copy["is_cli"] = is_cli
            r_info_copy["is_patches"] = is_patches
            repos_info.append(r_info_copy)

            if is_patches and not primary_patch_info:
                primary_patch_info = r_info_copy

    if not primary_patch_info and repos_info:
        primary_patch_info = repos_info[-1]

    if primary_patch_info:
        result["tag"] = primary_patch_info.get("tag", "")
        result["title"] = primary_patch_info.get("title", "")
        result["url"] = primary_patch_info.get("url", "")
        result["body"] = primary_patch_info.get("body", "")
        result["published_at"] = primary_patch_info.get("published_at", "")

    result["repos"] = repos_info
    _source_patch_info_cache[source] = result
    return result


_source_sig_cache: Dict[str, str] = {}

def get_source_signature(source: str) -> str:
    if source in _source_sig_cache:
        return _source_sig_cache[source]

    src_file = SOURCES_DIR / f"{source}.json"
    if not src_file.exists():
        for f in SOURCES_DIR.glob("*.json"):
            if f.stem.lower() == source.lower():
                src_file = f
                break
    if not src_file.exists():
        sig = f"missing-source:{source}"
        _source_sig_cache[source] = sig
        return sig

    try:
        with src_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        sig = f"unparseable:{e}"
        _source_sig_cache[source] = sig
        return sig

    if isinstance(data, dict) and "bundle_url" in data:
        sig = _fetch_bundle_signature(data["bundle_url"])
        _source_sig_cache[source] = sig
        return sig

    parts: List[str] = []
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            provider = (entry.get("provider") or "github").lower().strip()
            tag = entry.get("tag", "latest")

            has_github = bool(entry.get("user") and entry.get("repo"))
            has_project = bool(entry.get("project"))
            if provider == "gitlab" and has_project:
                project = entry.get("project")
                parts.append(f"gitlab:{project}@{fetch_repo_signature('', project, tag, provider)}")
            elif provider == "codeberg" and has_github:
                user = entry.get("user")
                repo = entry.get("repo")
                parts.append(f"codeberg:{user}/{repo}@{fetch_repo_signature(user, repo, tag, provider)}")
            elif provider == "github" and has_github:
                user = entry.get("user")
                repo = entry.get("repo")
                parts.append(f"{user}/{repo}@{fetch_repo_signature(user, repo, tag, provider)}")

    sig = ";".join(parts) if parts else f"empty:{source}"
    _source_sig_cache[source] = sig
    return sig


# ---------------------------------------------------------------------------
# Existing release manifest + assets
# ---------------------------------------------------------------------------
def _get_repo_owner_name() -> Optional[Tuple[str, str]]:
    repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    if "/" in repo:
        owner, name = repo.split("/", 1)
        if owner.strip() and name.strip():
            return owner.strip(), name.strip()
            
    try:
        p = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True)
        if p.returncode == 0 and p.stdout.strip():
            url = p.stdout.strip()
            m = re.search(r"github\.com[/:]([^/]+)/([^/\.]+)(?:\.git)?", url)
            if m:
                return m.group(1), m.group(2)
    except Exception:
        pass
        
    return ("yashrajrocxx", "Mophe-AutoBuilds")


def fetch_existing_manifest() -> Optional[dict]:
    if Path(MANIFEST_NAME).exists():
        try:
            with open(MANIFEST_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    rc, _, _ = run_gh(["release", "download", RELEASE_TAG, "--pattern", MANIFEST_NAME, "--clobber"])
    if rc == 0 and Path(MANIFEST_NAME).exists():
        try:
            with open(MANIFEST_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    repo = _get_repo_owner_name()
    if repo:
        owner, name = repo
        data = run_github_api(f"repos/{owner}/{name}/releases/tags/{RELEASE_TAG}")
        if isinstance(data, dict):
            for asset in data.get("assets", []):
                if asset.get("name") == MANIFEST_NAME:
                    download_url = asset.get("browser_download_url")
                    if download_url:
                        try:
                            resp = provider_utils.session.get(download_url, timeout=30)
                            if resp.status_code == 200:
                                manifest_data = resp.json()
                                with open(MANIFEST_NAME, "w", encoding="utf-8") as f:
                                    json.dump(manifest_data, f, indent=2)
                                return manifest_data
                        except Exception:
                            pass

    return None


def fetch_existing_apk_names() -> List[str]:
    repo = _get_repo_owner_name()
    if repo:
        owner, name = repo
        data = run_github_api(f"repos/{owner}/{name}/releases/tags/{RELEASE_TAG}")
        if isinstance(data, dict):
            return [
                a.get("name", "")
                for a in data.get("assets", [])
                if a.get("name", "").endswith(".apk")
            ]

    return [f.name for f in Path(".").glob("*.apk")]


# ---------------------------------------------------------------------------
# Matrix planning
# ---------------------------------------------------------------------------
def build_full_matrix() -> List[dict]:
    patch_list = load_patch_config()
    arch_map = load_arch_config()
    matrix: List[dict] = []
    seen = set()
    for entry in patch_list:
        app = entry.get("app_name")
        src = entry.get("source")
        if not app or not src:
            continue
        arches = arch_map.get((app, src), ["universal"])
        for arch in arches:
            key = (app, src, arch)
            if key in seen:
                continue
            seen.add(key)
            matrix.append({"app_name": app, "source": src, "arch": arch})
    return matrix


def make_manifest_key(app: str, source: str, arch: str) -> str:
    return f"{app}|{source}|{arch}"


def _is_unreliable_source_sig(sig: str) -> bool:
    s = (sig or "").lower()
    return (
        "@err:" in s
        or "@badjson:" in s
        or s.startswith("missing-source:")
        or s.startswith("unparseable:")
    )


def _recover_apk_from_release(app: str, arch: str, existing_apks: List[str]) -> str:
    a = (app or "").lower()
    rarch = (arch or "").lower()
    candidates: List[str] = []
    for n in existing_apks:
        nl = (n or "").lower()
        if not nl.endswith(".apk"):
            continue
        if not nl.startswith(f"{a}-{rarch}-"):
            continue
        candidates.append(n)
    candidates.sort()
    return candidates[-1] if candidates else ""


def plan_incremental(full_matrix: List[dict], old_manifest: Optional[dict],
                     existing_apks: List[str]) -> Tuple[List[dict], List[str], dict, dict]:
    """Decide which entries need rebuilding.
    Returns (build_matrix, carry_over_apks, new_manifest_entries, patch_changelogs)."""
    old_entries = (old_manifest or {}).get("entries", {}) if isinstance(old_manifest, dict) else {}
    existing_apk_set = set(existing_apks)

    build_matrix: List[dict] = []
    carry_over: List[str] = []
    new_entries: dict = {}
    patch_changelogs: dict = {}

    for entry in full_matrix:
        app = entry["app_name"]
        src = entry["source"]
        arch = entry["arch"]
        mkey = make_manifest_key(app, src, arch)

        cur_app_ver = load_app_config_version(app)
        cur_src_sig = get_source_signature(src)
        patch_info = get_source_patch_info(src)
        cur_patch_tag = patch_info.get("tag", "")
        cur_patch_url = patch_info.get("url", "")
        cur_patch_body = patch_info.get("body", "")

        old = old_entries.get(mkey)
        old_src_sig = (old or {}).get("source_sig", "")
        old_patch_tag = (old or {}).get("patch_tag", "")

        if old and old_src_sig and _is_unreliable_source_sig(cur_src_sig):
            cur_src_sig = old_src_sig

        carried_apk = (old or {}).get("apk", "")
        old_built_ver = (old or {}).get("built_version", "")
        if old:
            if not carried_apk or carried_apk not in existing_apk_set:
                recovered = _recover_apk_from_release(app, arch, existing_apks)
                if recovered:
                    carried_apk = recovered
                    old_built_ver = extract_version_from_filename(recovered)

        if not old_built_ver and carried_apk:
            old_built_ver = extract_version_from_filename(carried_apk)

        package_name = get_app_package_name(app)
        icon_url = (old or {}).get("icon_url", "")
        if not icon_url and package_name:
            icon_url = fetch_app_icon(package_name)
        
        new_entries[mkey] = {
            "app_name": app,
            "source": src,
            "arch": arch,
            "config_version": cur_app_ver,
            "source_sig": "",
            "patch_tag": cur_patch_tag,
            "patch_url": cur_patch_url,
            "patch_changelog": (cur_patch_body[:400] + "...") if len(cur_patch_body) > 400 else cur_patch_body,
            "apk": carried_apk,
            "built_version": old_built_ver,
            "built_at": (old or {}).get("built_at", ""),
            "package": package_name,
            "icon_url": icon_url,
        }

        reasons: List[str] = []
        if FORCE_FULL:
            reasons.append("force-rebuild")
        if not old:
            reasons.append("new-entry")
        else:
            # 1. Configured version changed in apps/<platform>/<app>.json
            if old.get("config_version", "") != cur_app_ver:
                reasons.append(f"app-config-changed: {old.get('config_version','')!r}->{cur_app_ver!r}")
            # 2. Patch source updated (new tag, release, commit, or patch file)
            if old.get("source_sig", "") != cur_src_sig:
                reasons.append("patch-source-updated")
            elif cur_patch_tag and old_patch_tag and old_patch_tag != cur_patch_tag:
                reasons.append(f"patch-tag: {old_patch_tag!r}->{cur_patch_tag!r}")
            # 3. APK missing
            if not carried_apk:
                reasons.append("no-apk-recorded")
            elif carried_apk not in existing_apk_set:
                reasons.append("apk-missing-from-release")

        if reasons:
            logging.info(f"  REBUILD {app}/{src}/{arch}: {'; '.join(reasons)}")
            build_matrix.append(entry)
            new_entries[mkey]["source_sig"] = old_src_sig
            new_entries[mkey]["pending_source_sig"] = cur_src_sig
            
            # Record patch changelog ONLY if the patch source was updated or on initial new entry
            is_patch_update = any(
                r.startswith("patch-source-updated")
                or r.startswith("patch-tag")
                or r in ("new-entry", "force-rebuild")
                for r in reasons
            )
            if is_patch_update and cur_patch_body:
                if src not in patch_changelogs:
                    patch_changelogs[src] = {
                        "source": src,
                        "old_tag": old_patch_tag,
                        "new_tag": cur_patch_tag,
                        "title": patch_info.get("title", ""),
                        "url": cur_patch_url,
                        "published_at": patch_info.get("published_at", ""),
                        "body": cur_patch_body,
                        "repos": patch_info.get("repos", []),
                        "affected_apps": [],
                    }
                if app not in patch_changelogs[src]["affected_apps"]:
                    patch_changelogs[src]["affected_apps"].append(app)
        else:
            new_entries[mkey]["source_sig"] = cur_src_sig
            old_apk = carried_apk
            if old_apk and old_apk in existing_apk_set:
                carry_over.append(old_apk)
                logging.info(f"  carry  {app}/{src}/{arch}: {old_apk}")
            else:
                logging.info(f"  REBUILD {app}/{src}/{arch}: no carry-over apk")
                build_matrix.append(entry)
                new_entries[mkey]["source_sig"] = old_src_sig
                new_entries[mkey]["pending_source_sig"] = cur_src_sig

    deduped: List[dict] = []
    seen_pairs = set()
    for e in build_matrix:
        pair = (e["app_name"], e["source"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        deduped.append({"app_name": e["app_name"], "source": e["source"]})

    rebuilding_pairs = seen_pairs
    filtered_carry: List[str] = []
    for apk in carry_over:
        owner_pair = None
        for ekey, eval_ in new_entries.items():
            if eval_.get("apk") == apk:
                owner_pair = (eval_["app_name"], eval_["source"])
                break
        if owner_pair is None or owner_pair not in rebuilding_pairs:
            filtered_carry.append(apk)
        else:
            logging.info(f"  drop carry {apk}: its (app,source) is rebuilding")

    return deduped, filtered_carry, new_entries, patch_changelogs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def emit_full_rebuild(reason: str) -> None:
    logging.warning(f"Falling back to FULL rebuild: {reason}")
    full = build_full_matrix()
    build_mx, carry_over, new_entries, patch_changelogs = plan_incremental(full, {}, [])
    Path("build_matrix.json").write_text(json.dumps(build_mx), encoding="utf-8")
    Path("carry_over.json").write_text(json.dumps(carry_over), encoding="utf-8")
    Path("new_manifest.json").write_text(
        json.dumps({"entries": new_entries}, indent=2), encoding="utf-8")
    Path("patch_changelogs.json").write_text(
        json.dumps(patch_changelogs, indent=2), encoding="utf-8")
    write_gh_output("build_matrix", json.dumps(build_mx))
    write_gh_output("has_updates", "true" if build_mx else "false")
    write_gh_output("update_count", str(len(build_mx)))
    write_gh_output("total_count", str(len(full)))
    write_gh_output("carry_count", str(len(carry_over)))
    write_gh_output("incremental", "false")


def main() -> int:
    try:
        full = build_full_matrix()
        logging.info(f"Full matrix: {len(full)} (app, source, arch) entries")

        if FORCE_FULL:
            logging.info("FORCE_FULL_REBUILD=true -> rebuilding everything")
            old_manifest = None
        else:
            old_manifest = fetch_existing_manifest()

        existing_apks = fetch_existing_apk_names()
        logging.info(f"Existing release has {len(existing_apks)} APK assets")

        if old_manifest is None and not FORCE_FULL:
            emit_full_rebuild("no manifest in existing release (first incremental run)")
            return 0

        build_mx, carry_over, new_entries, patch_changelogs = plan_incremental(
            full, old_manifest, existing_apks)

        Path("build_matrix.json").write_text(json.dumps(build_mx), encoding="utf-8")
        Path("carry_over.json").write_text(json.dumps(carry_over), encoding="utf-8")
        Path("new_manifest.json").write_text(
            json.dumps({"entries": new_entries}, indent=2), encoding="utf-8")
        Path("patch_changelogs.json").write_text(
            json.dumps(patch_changelogs, indent=2), encoding="utf-8")

        write_gh_output("build_matrix", json.dumps(build_mx))
        write_gh_output("has_updates", "true" if build_mx else "false")
        write_gh_output("update_count", str(len(build_mx)))
        write_gh_output("total_count", str(len(full)))
        write_gh_output("carry_count", str(len(carry_over)))
        write_gh_output("incremental", "true")

        logging.info("=" * 60)
        logging.info(f"  Total entries:     {len(full)}")
        logging.info(f"  Need rebuild:      {len(build_mx)}")
        logging.info(f"  Carry over:        {len(carry_over)}")
        logging.info(f"  Updated patches:   {len(patch_changelogs)}")
        logging.info("=" * 60)

        return 0

    except Exception as e:
        logging.error(f"check_app_updates failed: {e}")
        traceback.print_exc()
        emit_full_rebuild(f"unexpected error: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
