#!/usr/bin/env python3
"""
Send beautifully formatted Morphe AutoBuilds reports to Telegram via Bot API.

Security & Privacy:
- Never exposes or requires a phone number. Destinations are chat IDs,
  group IDs, or channel usernames (@channel) / IDs (-100...), comma-separated
  for multiple targets.
- Credentials (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) are read exclusively from
  environment variables (e.g. GitHub Secrets).
- All tokens are masked in logs.
- Safe HTML escaping prevents injection or broken formatting.
- Gracefully skips if credentials are not configured (exit code 0).
"""

import os
import sys
import json
import html
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import datetime

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

MAX_TG_MSG_LEN = 4000  # Telegram limit is 4096; keep headroom for safety

def mask_token(token: str) -> str:
    if not token or len(token) < 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"

def escape_html(text: Any) -> str:
    if text is None:
        return ""
    return html.escape(str(text))

def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Send a single message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logging.warning(f"Telegram API HTTP error {e.code}: {error_body}")
        # If HTML parse error, try sending plain text as fallback
        if "can't parse entities" in error_body.lower() or e.code == 400:
            try:
                logging.info("Attempting fallback with plain text...")
                plain_payload = {
                    "chat_id": chat_id,
                    "text": text.replace("<b>", "").replace("</b>", "")
                               .replace("<code>", "").replace("</code>", "")
                               .replace("<i>", "").replace("</i>", "")
                               .replace("<pre>", "").replace("</pre>", "")
                               .replace("&lt;", "<").replace("&gt;", ">")
                               .replace("&amp;", "&"),
                    "disable_web_page_preview": True,
                }
                req_plain = Request(url, data=json.dumps(plain_payload).encode("utf-8"),
                                    headers={"Content-Type": "application/json"})
                with urlopen(req_plain, timeout=15) as fallback_resp:
                    return fallback_resp.status == 200
            except Exception as fe:
                logging.warning(f"Fallback plain text also failed: {fe}")
        return False
    except Exception as e:
        logging.warning(f"Failed to send Telegram message: {e}")
        return False

def split_message(text: str, max_length: int = MAX_TG_MSG_LEN) -> List[str]:
    """Split long message into chunks respecting line breaks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_length = 0

    for line in lines:
        line_len = len(line) + 1
        if current_length + line_len > max_length and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_len
        else:
            current_chunk.append(line)
            current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def load_build_reports() -> List[Dict[str, Any]]:
    """Gather all build reports from build_report.json or build_records/."""
    reports: List[Dict[str, Any]] = []
    
    # 1. Check root build_report.json
    root_report = Path("build_report.json")
    if root_report.exists():
        try:
            with root_report.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass

    # 2. Check release-apks/build_report.json
    rel_report = Path("release-apks/build_report.json")
    if rel_report.exists():
        try:
            with rel_report.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass

    # 3. Aggregate build_records/build_report_*.json
    records_dir = Path("build_records")
    if records_dir.exists():
        for fpath in sorted(records_dir.rglob("build_report_*.json")):
            try:
                with fpath.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        reports.extend(data)
                    elif isinstance(data, dict):
                        reports.append(data)
            except Exception:
                pass

    return reports

def load_failed_patches() -> Dict[str, List[str]]:
    """Load any failed patch records."""
    for p in [Path("build_records/failed_patches.json"), Path("release-apks/failed_patches.json"), Path("failed_patches.json")]:
        if p.exists():
            try:
                with p.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

def load_counts() -> Dict[str, int]:
    """Retrieve build/carry counts from files if available."""
    counts = {"rebuilt": 0, "carried": 0, "failed": 0}

    bm_path = Path("build_matrix.json")
    if bm_path.exists():
        try:
            with bm_path.open("r", encoding="utf-8") as f:
                matrix = json.load(f)
                counts["planned"] = len(matrix)
        except Exception:
            pass

    co_path = Path("carry_over.json")
    if co_path.exists():
        try:
            with co_path.open("r", encoding="utf-8") as f:
                carry = json.load(f)
                counts["carried"] = len(carry)
        except Exception:
            pass

    return counts

def format_app_display(app_name: str) -> str:
    name_map = {
        "youtube": "YouTube",
        "youtube-music": "YouTube Music",
        "reddit": "Reddit",
        "instagram": "Instagram",
        "x": "X (Twitter)",
        "pinterest": "Pinterest",
        "telegram": "Telegram",
        "vn": "VN Video Editor",
        "sdmaidse": "SD Maid 2 / SE",
        "threads": "Threads",
        "google-photos": "Google Photos",
        "tradingview": "TradingView",
        "pocketcasts": "Pocket Casts",
        "depthwallpaper": "Depth Wallpaper",
        "minimalwidgets": "Minimal Widgets",
        "protonpass": "Proton Pass",
        "serverauditor": "Server Auditor",
        "vocabulary": "Vocabulary",
        "pinnit": "Pinnit",
        "gboard": "Gboard",
        "vivaldi-snapshot": "Vivaldi Snapshot",
        "vivaldi": "Vivaldi Browser",
        "taskmanager": "TaskManager",
        "habitkit": "HabitKit",
        "notesnook": "Notesnook",
        "duolingo": "Duolingo",
        "brave": "Brave Browser",
        "jiohotstar": "JioHotstar",
    }
    return name_map.get(app_name.lower().strip(), app_name.replace("-", " ").title())

def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    raw_chats = (os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHATID") or "").strip()

    if not token or not raw_chats:
        logging.info(
            "[INFO] Telegram credentials (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID / TELEGRAM_CHATID) "
            "not set. Skipping Telegram notification."
        )
        return 0

    # One or many destinations: personal chat, group/supergroup, or channel.
    # Channels use @username (public) or -100... numeric ID (private).
    chat_ids = [c.strip() for c in raw_chats.split(",") if c.strip()]
    if not chat_ids:
        logging.info("[INFO] No valid Telegram chat IDs configured. Skipping.")
        return 0

    logging.info(f"Preparing Telegram report for {len(chat_ids)} destination(s) (token={mask_token(token)})...")

    # Context info
    repo = os.environ.get("GITHUB_REPOSITORY", "yashrajrocxx/Mophe-AutoBuilds")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Morphe AutoBuilds")
    run_url = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id else f"{server_url}/{repo}/actions"
    release_url = f"{server_url}/{repo}/releases/tag/latest"
    pages_url = f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/" if "/" in repo else "https://yashrajrocxx.github.io/Mophe-AutoBuilds/"

    reports = load_build_reports()
    failed_patches_map = load_failed_patches()
    counts = load_counts()

    successful_builds = [r for r in reports if r.get("status") == "success"]
    failed_builds = [r for r in reports if r.get("status") == "failed"]

    # Deduce overall status
    if not reports:
        # Check if we built individual APKs directly
        apk_files = list(Path(".").glob("*.apk")) + (list(Path("release-apks").glob("*.apk")) if Path("release-apks").exists() else [])
        deduped_apks = {a.name for a in apk_files}
        if deduped_apks:
            status_emoji = "✅"
            status_text = "Builds Succeeded"
            successful_count = len(deduped_apks)
            failed_count = 0
        else:
            status_emoji = "ℹ️"
            status_text = "No Rebuilds Needed (Up to Date)"
            successful_count = 0
            failed_count = 0
    elif failed_builds and not successful_builds:
        status_emoji = "❌"
        status_text = "All Builds Failed"
        successful_count = 0
        failed_count = len(failed_builds)
    elif failed_builds:
        status_emoji = "⚠️"
        status_text = f"Partial Success ({len(successful_builds)}/{len(reports)} Passed)"
        successful_count = len(successful_builds)
        failed_count = len(failed_builds)
    else:
        status_emoji = "✅"
        status_text = "All Builds Succeeded"
        successful_count = len(successful_builds)
        failed_count = 0

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build Header
    lines = [
        f"🚀 <b>Morphe AutoBuilds — Pipeline Report</b>",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"<b>Workflow:</b> {escape_html(workflow)}",
        f"<b>Status:</b> {status_emoji} <b>{escape_html(status_text)}</b>",
        f"<b>Time:</b> <code>{now_utc}</code>",
        "",
        f"📊 <b>Summary:</b>",
        f"• Rebuilt APKs: <b>{successful_count}</b>",
        f"• Carried Over: <b>{counts.get('carried', 0)}</b>",
    ]
    if failed_count > 0:
        lines.append(f"• Failed Builds: <b>{failed_count}</b>")

    # Rebuilt Apps Section
    if successful_builds:
        lines.append("")
        lines.append(f"📦 <b>Newly Built Applications:</b>")
        for b in successful_builds:
            app = b.get("app", "App")
            arch = b.get("arch", "universal")
            src = b.get("source", "")
            ver = b.get("version", "")
            apk_name = b.get("apk", "")
            app_display = format_app_display(app)

            ver_text = f"v{ver}" if ver else "latest"
            apk_dl_link = f"{release_url}/download/{apk_name}" if apk_name else release_url

            lines.append(
                f"• 🟢 <b>{escape_html(app_display)}</b> (<code>{escape_html(arch)}</code> • <i>{escape_html(src)}</i>)\n"
                f"  └ 🏷️ <code>{escape_html(ver_text)}</code> • <a href=\"{apk_dl_link}\">Download APK</a>"
            )

    # Failed Builds Section
    if failed_builds:
        lines.append("")
        lines.append(f"❌ <b>Build Failures:</b>")
        for b in failed_builds:
            app = b.get("app", "App")
            arch = b.get("arch", "universal")
            src = b.get("source", "")
            err = b.get("error") or "Patching/compilation error"
            app_display = format_app_display(app)
            lines.append(
                f"• 🔴 <b>{escape_html(app_display)}</b> (<code>{escape_html(arch)}</code> • <i>{escape_html(src)}</i>)\n"
                f"  └ <i>Reason:</i> <code>{escape_html(err)[:120]}</code>"
            )

    # Failed Patches Section (warnings)
    if failed_patches_map:
        lines.append("")
        lines.append(f"⚠️ <b>Non-fatal Failed Patches:</b>")
        for app, patches in failed_patches_map.items():
            if patches:
                app_display = format_app_display(app)
                patches_str = ", ".join(escape_html(p) for p in patches[:3])
                if len(patches) > 3:
                    patches_str += f" (+{len(patches) - 3} more)"
                lines.append(f"• <b>{escape_html(app_display)}:</b> <code>{patches_str}</code>")

    # Links Footer
    lines.append("")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━")
    footer_links = []
    if release_url:
        footer_links.append(f"<a href=\"{release_url}\">📦 GitHub Release</a>")
    if pages_url:
        footer_links.append(f"<a href=\"{pages_url}\">🌐 Web Catalog</a>")
    if run_url:
        footer_links.append(f"<a href=\"{run_url}\">⚙️ Actions Log</a>")
    lines.append(" | ".join(footer_links))

    full_message = "\n".join(lines)
    chunks = split_message(full_message)

    logging.info(f"Sending Telegram notification in {len(chunks)} message(s) × {len(chat_ids)} destination(s)...")
    success = True
    for chat_id in chat_ids:
        for idx, chunk in enumerate(chunks, 1):
            ok = send_telegram_message(token, chat_id, chunk)
            if not ok:
                logging.warning(f"Failed to deliver Telegram chunk {idx}/{len(chunks)} to {chat_id}")
                success = False

    if success:
        logging.info("[OK] Telegram build report delivered successfully.")
    else:
        logging.warning("[WARN] Could not deliver one or more Telegram messages.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
