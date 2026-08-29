#!/usr/bin/env python3
"""
daily_music_log.py - Generate daily listening log blog posts from Navidrome
Connects to the Mac Mini Navidrome database, aggregates scrobbles, and creates a markdown post.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, date, timedelta
from collections import Counter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT_DIR, "content", "blog")

DEFAULT_SERVER_HOST = os.environ.get("NAVIDROME_SSH_HOST", "homi3@serverland")
DEFAULT_DB_PATH = os.environ.get("NAVIDROME_DB_PATH", "/home/homi3/Projects/homelab/navidrome/data/navidrome.db")

def get_scrobbles(target_date, host=DEFAULT_SERVER_HOST, db_path=DEFAULT_DB_PATH):
    """Fetch scrobbles for a specific day from Navidrome SQLite DB."""
    start_dt = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    end_dt = start_dt + timedelta(days=1)
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    sql_query = f"""
    SELECT s.submission_time, m.title, m.artist, m.album, m.duration, m.genre
    FROM scrobbles s
    JOIN media_file m ON s.media_file_id = m.id
    WHERE s.submission_time >= {start_ts} AND s.submission_time < {end_ts}
    ORDER BY s.submission_time ASC
    """

    # If running locally on the server where DB is present
    if os.path.exists(db_path) and host == "localhost":
        import sqlite3
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        con.close()
        return rows

    # Remote fetch over SSH
    py_remote = f"""
import sqlite3, json
con = sqlite3.connect('{db_path}')
cur = con.cursor()
cur.execute('''{sql_query}''')
print(json.dumps(cur.fetchall()))
"""
    # Try primary host then fallback to IP if needed
    hosts_to_try = [host, "homi3@100.125.107.97", "homi3@192.168.86.40"]
    for h in hosts_to_try:
        try:
            res = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=4", "-o", "BatchMode=yes", h, f"python3 -c \"{py_remote}\""],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(res.stdout)
            return data
        except Exception:
            continue

    raise RuntimeError(f"Could not connect to Navidrome server at {host}")


def format_duration(seconds):
    """Format seconds into HH:MM or MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins >= 60:
        hrs = mins // 60
        rem_mins = mins % 60
        return f"{hrs}h {rem_mins}m"
    return f"{mins}m {secs}s"


def generate_markdown(target_date, scrobbles):
    """Format scrobbles into clean markdown with retro summary block."""
    date_str = target_date.strftime("%Y-%m-%d")
    pretty_date = target_date.strftime("%B %d, %Y")
    
    if not scrobbles:
        return None

    total_tracks = len(scrobbles)
    total_seconds = sum(s[4] or 0 for s in scrobbles)
    playtime_str = format_duration(total_seconds)

    artists = [s[2] or "Unknown Artist" for s in scrobbles]
    albums = [f"{s[3] or 'Unknown Album'} — {s[2] or 'Unknown Artist'}" for s in scrobbles if s[3]]

    top_artists = Counter(artists).most_common(5)
    top_albums = Counter(albums).most_common(5)

    # Top artists summary
    artist_list = "\n".join([f"- **{name}** ({count} plays)" for name, count in top_artists])
    album_list = "\n".join([f"- **{name}** ({count} plays)" for name, count in top_albums])

    # Chronological log table/items
    track_rows = []
    for ts, title, artist, album, dur, genre in scrobbles:
        dt = datetime.fromtimestamp(ts)
        t_str = dt.strftime("%H:%M")
        dur_str = f"{int((dur or 0)//60)}:{int((dur or 0)%60):02d}"
        track_rows.append(f"  [{t_str}] {artist} - {title} ({album}) [{dur_str}]")

    track_log_block = "\n".join(track_rows)

    md = f"""---
title: daily listening habits: {pretty_date}
date: {date_str}
description: Automated daily listening transmission recorded from Navidrome music server.
tags: music, navidrome, listening-log
slug: {date_str}-daily-listening
---

## 01. daily playback telemetry

```text
==================================================
  DATE:            {pretty_date}
  TOTAL TRACKS:    {total_tracks}
  TOTAL PLAYTIME:  {playtime_str}
  STREAM SERVER:   navidrome @ serverland
==================================================
```

## 02. top artists

{artist_list}

## 03. top albums

{album_list}

## 04. full chronological track log

```text
{track_log_block}
```

---
*transmission generated automatically from local navidrome scrobbles.*
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="Generate daily music listening post for retro-pi-blog")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--yesterday", action="store_true", help="Fetch for yesterday")
    parser.add_argument("--preview", action="store_true", help="Preview post to stdout without saving")
    parser.add_argument("--deploy", action="store_true", help="Build and deploy site immediately")
    parser.add_argument("--server", default=DEFAULT_SERVER_HOST, help="SSH host for Navidrome server")
    args = parser.parse_args()

    if args.yesterday:
        target_date = date.today() - timedelta(days=1)
    elif args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    print(f"Fetching Navidrome scrobbles for {target_date} from {args.server}...")
    try:
        scrobbles = get_scrobbles(target_date, host=args.server)
    except Exception as e:
        print(f"Error fetching scrobbles: {e}", file=sys.stderr)
        sys.exit(1)

    if not scrobbles:
        print(f"No scrobbles found for {target_date}.")
        sys.exit(0)

    print(f"Found {len(scrobbles)} scrobbles.")
    md_content = generate_markdown(target_date, scrobbles)

    if args.preview:
        print("\n--- PREVIEW ---")
        print(md_content)
        print("--- END PREVIEW ---")
        return

    out_file = os.path.join(CONTENT_DIR, f"{target_date.strftime('%Y-%m-%d')}-daily-listening.md")
    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[OK] Generated post: {out_file}")

    if args.deploy:
        deploy_script = os.path.join(ROOT_DIR, "deploy.sh")
        print("Running deployment...")
        subprocess.run(["bash", deploy_script], check=True)

if __name__ == "__main__":
    main()
