#!/usr/bin/env python3
"""
daily_yoga_log.py - Generate daily yoga practice blog posts from Down Dog (downdogapp.com)
Fetches completed practice sessions and pose sequences from Down Dog's JSON API
and formats a minimalist markdown transmission for binbot.dev.
Zero external dependencies (uses standard Python 3).
"""

import os
import sys
import time
import json
import socket
import argparse
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta

# Force IPv4 resolution to avoid 2-minute IPv6 connection timeouts on www.downdogapp.com
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT_DIR, "content", "blog")
DEFAULT_TOKEN_FILE = os.path.join(ROOT_DIR, ".downdog.token")

BASE_API_URL = "https://www.downdogapp.com/json"
DEFAULT_APP_TYPE = "ORIGINAL"
DEFAULT_APP_VERSION = "8.5.2"


def log_info(msg):
    """Write status messages to stderr so piping '--preview | bat' stays clean."""
    print(msg, file=sys.stderr)


def load_cred(cred_arg=None, token_file=DEFAULT_TOKEN_FILE):
    """Load Down Dog 'cred' token from CLI arg, env var, or local .downdog.token file."""
    if cred_arg:
        return cred_arg.strip()

    env_cred = os.environ.get("DOWNDOG_CRED", "").strip()
    if env_cred:
        return env_cred

    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as f:
            token = f.read().strip()
            if token:
                return token

    return None


def save_cred(cred_str, token_file=DEFAULT_TOKEN_FILE):
    """Save Down Dog 'cred' token to .downdog.token (gitignored via *.token) with 0600 permissions."""
    clean = cred_str.strip().strip('"').strip("'")
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(clean + "\n")
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        pass
    return clean


def prompt_for_cred(token_file=DEFAULT_TOKEN_FILE):
    """Interactively guide the user to grab their Google-authenticated 'cred' token once."""
    log_info("=== Down Dog Account Setup (Google Sign-In) ===")
    log_info("No Down Dog credential token found.")
    log_info("")
    log_info("To link your account (one-time setup):")
    log_info("  1. Open https://www.downdogapp.com/web in your browser and sign in with Google.")
    log_info("  2. Open DevTools Console (F12 or Ctrl+Shift+J) and run:")
    log_info("")
    log_info("     copy(localStorage.getItem('downdogapp-cred'))")
    log_info("")
    log_info("  3. Paste the copied token below.")
    log_info("")
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        log_info("Error: Cannot prompt interactively when stdout/stdin is piped. Run './log-yoga.sh --set-cred <TOKEN>' first.")
        sys.exit(1)
    try:
        entered = input("Paste Down Dog cred token: ").strip()
    except (EOFError, KeyboardInterrupt):
        log_info("\nAborted.")
        sys.exit(1)

    if not entered:
        log_info("Error: Credential token cannot be empty.")
        sys.exit(1)

    saved = save_cred(entered, token_file)
    log_info(f"[OK] Saved token to {token_file} (gitignored).\n")
    return saved


def post_downdog_api(endpoint, cred, params=None):
    """Make an authenticated form-urlencoded POST request to https://www.downdogapp.com/json/<endpoint>."""
    url = f"{BASE_API_URL}/{endpoint.lstrip('/')}"
    payload = {
        "version": DEFAULT_APP_VERSION,
        "appType": DEFAULT_APP_TYPE,
        "timestamp": str(int(time.time() * 1000)),
        "cred": cred,
        "languageOption": "",
    }
    if params:
        for k, v in params.items():
            if v is not None:
                payload[k] = str(v)

    encoded_body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded_body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Origin": "https://www.downdogapp.com",
            "Referer": "https://www.downdogapp.com/web",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"Down Dog API HTTP {e.code} on /{endpoint}: {err_body or e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error contacting Down Dog API (/{endpoint}): {e.reason}")


def parse_item_date(date_val):
    """Parse PracticeHistoryItem.date (YearMonthDay object, ISO string, or epoch ms) into datetime.date."""
    if not date_val:
        return None
    if isinstance(date_val, dict):
        y = int(date_val.get("year") or 0)
        m = int(date_val.get("month") or 0)
        d = int(date_val.get("day") or 0)
        if y and m and d:
            return date(y, m, d)
    if isinstance(date_val, (int, float)):
        ts = date_val / 1000.0 if date_val > 1e11 else float(date_val)
        return datetime.fromtimestamp(ts).date()
    if isinstance(date_val, str):
        clean = date_val.strip()
        if len(clean) >= 10 and clean[4] == "-" and clean[7] == "-":
            return datetime.strptime(clean[:10], "%Y-%m-%d").date()
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(clean, fmt).date()
            except ValueError:
                continue
    return None


def normalize_seconds(time_val):
    """Convert Down Dog duration value ({'seconds': ...}, ms, or seconds) into integer seconds."""
    if time_val is None:
        return 0
    if isinstance(time_val, dict):
        if "seconds" in time_val:
            try:
                return max(0, int(round(float(time_val["seconds"]))))
            except (ValueError, TypeError):
                return 0
        if "milliseconds" in time_val:
            try:
                return max(0, int(round(float(time_val["milliseconds"]) / 1000.0)))
            except (ValueError, TypeError):
                return 0
    try:
        val = float(time_val)
    except (ValueError, TypeError):
        return 0
    if val <= 0:
        return 0
    if val >= 10800:
        return int(round(val / 1000.0))
    return int(round(val))


def format_duration(seconds):
    """Format seconds into human-readable duration (e.g., 34m or 1h 05m)."""
    if seconds <= 0:
        return "--"
    mins = int(round(seconds / 60.0))
    if mins >= 60:
        hrs = mins // 60
        rem_mins = mins % 60
        return f"{hrs}h {rem_mins:02d}m"
    return f"{mins}m"


def hydrate_session(item, cred, properties):
    """Fetch historyDetails for a practice item and return a normalized session dict."""
    practice_id = item.get("practiceId")
    seq_id = item.get("sequenceId")
    seq_prop = properties.get(seq_id) or {}
    practice_name = (seq_prop.get("name") or "").strip()

    details = {}
    if practice_id:
        try:
            details = post_downdog_api("historyDetails", cred, {"practiceId": practice_id})
        except Exception as e:
            log_info(f"Warning: Could not fetch details for practiceId={practice_id}: {e}")

    played_sec = normalize_seconds(item.get("playedTime"))
    total_sec = normalize_seconds(item.get("totalTime"))
    duration_sec = played_sec if played_sec > 0 else total_sec

    settings_raw = item.get("settings") or []
    settings = []
    for s in settings_raw:
        lbl = (s.get("label") or "").strip()
        val = (s.get("value") or "").strip()
        if lbl and val:
            settings.append((lbl, val))
        elif val:
            settings.append(("Setting", val))

    poses_raw = details.get("poses") or []
    poses = []
    for p in poses_raw:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        poses.append({
            "name": name,
            "poseId": p.get("poseId"),
            "libraryUrl": (p.get("libraryUrl") or "").strip(),
            "boostNames": [b.strip() for b in (p.get("boostNames") or []) if b and b.strip()],
        })

    return {
        "practiceId": practice_id,
        "sequenceId": seq_id,
        "name": practice_name,
        "duration_sec": duration_sec,
        "total_sec": total_sec,
        "played_sec": played_sec,
        "settings": settings,
        "poses": poses,
        "poseListTitle": details.get("poseListTitle"),
    }


def get_practices_for_date(target_date, cred, include_incomplete=False):
    """Fetch practice history for target_date, returning (yoga_sessions, meditation_sessions)."""
    history_resp = post_downdog_api("practiceHistory", cred)
    items = history_resp.get("items") or []
    properties = history_resp.get("properties") or {}
    extra_filters = {f.get("id"): f.get("label") for f in (history_resp.get("extraFilters") or []) if "id" in f}

    yoga_filter_ids = {fid for fid, label in extra_filters.items() if "yoga" in (label or "").lower()} or {0}
    med_filter_ids = {fid for fid, label in extra_filters.items() if "meditation" in (label or "").lower()} or {2}

    yoga_items = []
    med_items = []
    for item in items:
        if not include_incomplete and item.get("incomplete"):
            continue
        item_date = parse_item_date(item.get("date"))
        if item_date != target_date:
            continue

        filter_ids = set(item.get("practiceHistoryItemFilterIds") or [])
        if filter_ids & med_filter_ids and not (filter_ids & yoga_filter_ids):
            med_items.append(item)
        else:
            yoga_items.append(item)

    # Sort chronological (API returns newest first)
    yoga_items.reverse()
    med_items.reverse()

    yoga_sessions = [hydrate_session(it, cred, properties) for it in yoga_items]
    med_sessions = [hydrate_session(it, cred, properties) for it in med_items]

    return yoga_sessions, med_sessions


def format_meditation_summary(med_session):
    """Format a single meditation session into a concise one-line telemetry summary."""
    dur = format_duration(med_session["duration_sec"])
    theme_vals = [val for lbl, val in med_session["settings"] if val]
    theme_str = ", ".join(theme_vals) if theme_vals else (med_session.get("name") or "Guided Meditation")
    techniques = [p["name"] for p in med_session.get("poses") or [] if p.get("name")]
    tech_str = f" ({', '.join(techniques)})" if techniques else ""
    return f"{dur} — {theme_str}{tech_str}"


def generate_markdown(target_date, yoga_sessions, med_sessions=None, note=""):
    """Format Down Dog yoga (and optional meditation) sessions into a retro-pi-blog markdown transmission."""
    med_sessions = med_sessions or []
    if not yoga_sessions and not med_sessions:
        return None

    date_str = target_date.strftime("%Y-%m-%d")
    pretty_date = target_date.strftime("%B %d, %Y")

    yoga_seconds = sum(s["duration_sec"] for s in yoga_sessions)
    yoga_duration_str = format_duration(yoga_seconds)
    total_poses = sum(len(s["poses"]) for s in yoga_sessions)

    telemetry_lines = [
        "==================================================",
        f"  DATE:            {pretty_date}",
    ]

    if len(yoga_sessions) == 1:
        y = yoga_sessions[0]
        if y.get("name"):
            telemetry_lines.append(f"  PRACTICE:        {y['name']}")
        telemetry_lines.append(f"  DURATION:        {yoga_duration_str}")
        telemetry_lines.append(f"  TOTAL POSES:     {total_poses}")
        for lbl, val in y["settings"]:
            key_str = f"{lbl.upper()}:"
            telemetry_lines.append(f"  {key_str:<17}{val}")
    elif len(yoga_sessions) > 1:
        telemetry_lines.append(f"  YOGA SESSIONS:   {len(yoga_sessions)}")
        telemetry_lines.append(f"  YOGA DURATION:   {yoga_duration_str}")
        telemetry_lines.append(f"  TOTAL POSES:     {total_poses}")

    # Include Meditation summary lines in the telemetry header if present
    for idx, m in enumerate(med_sessions, 1):
        label = "MEDITATION:" if len(med_sessions) == 1 else f"MEDITATION {idx}:"
        telemetry_lines.append(f"  {label:<17}{format_meditation_summary(m)}")

    telemetry_lines.append("  SOURCE:          down dog (downdogapp.com)")
    telemetry_lines.append("==================================================")
    telemetry_block = "\n".join(telemetry_lines)

    sections = []
    sec_num = 1

    # Section 01: Telemetry
    sections.append(f"## {sec_num:02d}. practice telemetry\n\n```text\n{telemetry_block}\n```")
    sec_num += 1

    # Optional personal note section
    clean_note = (note or "").strip()
    if clean_note:
        sections.append(f"## {sec_num:02d}. practice notes\n\n{clean_note}")
        sec_num += 1

    # Settings summary if multiple yoga sessions
    if len(yoga_sessions) > 1 and any(s["settings"] or s.get("name") for s in yoga_sessions):
        settings_lines = []
        for idx, s in enumerate(yoga_sessions, 1):
            s_dur = format_duration(s["duration_sec"])
            s_name = s.get("name") or f"Session {idx}"
            pairs = ", ".join(f"{k}: {v}" if k.lower() != "setting" else v for k, v in s["settings"])
            if pairs:
                settings_lines.append(f"- **{s_name} ({s_dur}):** {pairs}")
            else:
                settings_lines.append(f"- **{s_name} ({s_dur})**")
        sections.append(f"## {sec_num:02d}. session settings & boosts\n\n" + "\n".join(settings_lines))
        sec_num += 1

    # Pose sequence section(s) — strictly for Yoga sessions
    if len(yoga_sessions) == 1:
        poses = yoga_sessions[0]["poses"]
        pose_lines = []
        for idx, p in enumerate(poses, 1):
            boost_tag = f"  [boost: {', '.join(p['boostNames'])}]" if p["boostNames"] else ""
            pose_lines.append(f"  {idx:02d}. {p['name']}{boost_tag}")
        pose_block = "\n".join(pose_lines) if pose_lines else "  (no pose breakdown recorded for this session)"
        sections.append(f"## {sec_num:02d}. pose sequence\n\n```text\n{pose_block}\n```")
    elif len(yoga_sessions) > 1:
        session_blocks = []
        for s_idx, s in enumerate(yoga_sessions, 1):
            s_dur = format_duration(s["duration_sec"])
            s_name = s.get("name") or f"session {s_idx}"
            poses = s["poses"]
            pose_lines = [f"  --- {s_name.lower()} ({s_dur}, {len(poses)} poses) ---"]
            for idx, p in enumerate(poses, 1):
                boost_tag = f"  [boost: {', '.join(p['boostNames'])}]" if p["boostNames"] else ""
                pose_lines.append(f"  {idx:02d}. {p['name']}{boost_tag}")
            session_blocks.append("\n".join(pose_lines))
        pose_block = "\n\n".join(session_blocks)
        sections.append(f"## {sec_num:02d}. pose sequences\n\n```text\n{pose_block}\n```")

    body_sections = "\n\n".join(sections)

    if yoga_sessions:
        med_desc = f" + {format_duration(sum(m['duration_sec'] for m in med_sessions))} meditation" if med_sessions else ""
        desc = f"Daily yoga practice log ({yoga_duration_str}, {total_poses} poses{med_desc}) recorded from Down Dog."
    else:
        med_dur = format_duration(sum(m["duration_sec"] for m in med_sessions))
        desc = f"Daily mindfulness and meditation log ({med_dur}) recorded from Down Dog."

    tags = "yoga, meditation, downdog, practice-log" if med_sessions else "yoga, downdog, practice-log"

    md = f"""---
title: daily yoga practice: {pretty_date}
date: {date_str}
description: {desc}
tags: {tags}
slug: {date_str}-daily-yoga
---

{body_sections}

---
*transmission generated from down dog practice history.*
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="Generate daily yoga practice blog post from Down Dog")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--yesterday", action="store_true", help="Fetch practice for yesterday")
    parser.add_argument("--note", help="Optional personal note to include in the post")
    parser.add_argument("--no-prompt", action="store_true", help="Skip interactive note prompt (for cron/automation)")
    parser.add_argument("--include-meditation", action="store_true", help="Allow generating a post on meditation-only days")
    parser.add_argument("--no-meditation", action="store_true", help="Omit meditation sessions from the telemetry header")
    parser.add_argument("--include-incomplete", action="store_true", help="Include incomplete/partial sessions")
    parser.add_argument("--cred", help="Down Dog 'cred' token (overrides .downdog.token and DOWNDOG_CRED)")
    parser.add_argument("--set-cred", metavar="TOKEN", help="Save your Down Dog 'cred' token to .downdog.token and exit")
    parser.add_argument("--list-recent", action="store_true", help="List recent practice dates in your account and exit")
    parser.add_argument("--preview", action="store_true", help="Preview generated markdown to stdout without saving")
    parser.add_argument("--deploy", action="store_true", help="Build and deploy site immediately after saving")
    args = parser.parse_args()

    if args.set_cred:
        save_cred(args.set_cred)
        log_info(f"[OK] Saved Down Dog credential token to {DEFAULT_TOKEN_FILE}")
        return

    cred = load_cred(args.cred)
    if not cred:
        cred = prompt_for_cred()

    if args.list_recent:
        log_info("Fetching recent Down Dog practice history...")
        resp = post_downdog_api("practiceHistory", cred)
        items = resp.get("items") or []
        props = resp.get("properties") or {}
        extra_filters = {f.get("id"): f.get("label") for f in (resp.get("extraFilters") or []) if "id" in f}
        if not items:
            log_info("No practices found in account history (check if your cred token is valid).")
            return
        print(f"Found {len(items)} total session(s). Showing 15 most recent:")
        for item in items[:15]:
            d = parse_item_date(item.get("date"))
            dur = format_duration(normalize_seconds(item.get("playedTime")) or normalize_seconds(item.get("totalTime")))
            seq_name = (props.get(item.get("sequenceId")) or {}).get("name", "Practice")
            fids = item.get("practiceHistoryItemFilterIds") or []
            kind = "/".join(extra_filters.get(fid, str(fid)) for fid in fids) if fids else "Yoga"
            settings_str = ", ".join(f"{s.get('label')}: {s.get('value')}" for s in (item.get("settings") or []) if s.get("value"))
            inc = " [INCOMPLETE]" if item.get("incomplete") else ""
            print(f"  - {d} | {kind:<10} | {dur:<5} | {seq_name} ({settings_str}){inc}")
        return

    if args.yesterday:
        target_date = date.today() - timedelta(days=1)
    elif args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    log_info(f"Fetching Down Dog sessions for {target_date}...")
    try:
        yoga_sessions, med_sessions = get_practices_for_date(
            target_date,
            cred,
            include_incomplete=args.include_incomplete,
        )
    except Exception as e:
        log_info(f"Error fetching Down Dog data: {e}")
        sys.exit(1)

    if args.no_meditation:
        med_sessions = []

    if not yoga_sessions:
        if med_sessions and not args.include_meditation:
            log_info(f"No yoga sessions found for {target_date} (found {len(med_sessions)} meditation session(s); pass --include-meditation to generate a meditation-only post).")
            log_info("Tip: Run './log-yoga.sh --list-recent' to inspect available session dates in your account.")
            sys.exit(0)
        elif not med_sessions:
            log_info(f"No completed yoga or meditation sessions found for {target_date}.")
            log_info("Tip: Run './log-yoga.sh --list-recent' to inspect available session dates in your account.")
            sys.exit(0)

    total_poses = sum(len(s["poses"]) for s in yoga_sessions)
    med_msg = f" + {len(med_sessions)} meditation session(s)" if med_sessions else ""
    log_info(f"Found {len(yoga_sessions)} yoga session(s) ({total_poses} total poses){med_msg}.")

    out_file = os.path.join(CONTENT_DIR, f"{target_date.strftime('%Y-%m-%d')}-daily-yoga.md")
    existing_note = ""
    if os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as ef:
                existing_md = ef.read()
            import re
            m_note = re.search(r"## \d+\.\s+practice notes\s*\n+(.+?)(?=\n+## \d+\.|\n+---|\Z)", existing_md, flags=re.DOTALL)
            if m_note:
                existing_note = m_note.group(1).strip()
        except Exception:
            pass

    note = args.note
    if note is None and not args.no_prompt and not args.preview and sys.stdin.isatty() and sys.stdout.isatty():
        prompt_msg = "Add a personal note for this practice (optional, press Enter to keep existing): " if existing_note else "Add a personal note for this practice (optional, press Enter to skip): "
        try:
            sys.stderr.write(prompt_msg)
            sys.stderr.flush()
            entered_note = sys.stdin.readline().strip()
            if entered_note and existing_note:
                note = f"{existing_note}\n\n{entered_note}"
            else:
                note = entered_note or existing_note
        except (EOFError, KeyboardInterrupt):
            log_info("")
            note = existing_note
    elif note is None:
        note = existing_note
    elif existing_note and note != existing_note:
        note = f"{existing_note}\n\n{note}"

    md_content = generate_markdown(target_date, yoga_sessions, med_sessions=med_sessions, note=note or "")

    if args.preview:
        print(md_content, end="")
        return

    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    log_info(f"[OK] Generated post: {out_file}")

    if args.deploy:
        deploy_script = os.path.join(ROOT_DIR, "deploy.sh")
        log_info("Running deployment...")
        subprocess.run(["bash", deploy_script], check=True)
    else:
        log_info("-> To build locally: python3 build.py")
        log_info("-> To build & deploy to Raspberry Pi: ./deploy.sh")


if __name__ == "__main__":
    main()
