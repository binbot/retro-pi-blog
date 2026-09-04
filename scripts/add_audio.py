#!/usr/bin/env python3
"""
scripts/add_audio.py - Helper script to append an audio track entry to content/audio.md
"""

import os
import re
import sys
import argparse

def add_track(audio_md_path, title, src, duration="--:--", date=None, description=None):
    if not os.path.exists(audio_md_path):
        print(f"Error: {audio_md_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(audio_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build track entry block
    entry_lines = [
        f"- title: {title}",
        f"  src: {src}",
        f"  duration: {duration}"
    ]
    if date:
        entry_lines.append(f"  date: {date}")
    if description:
        entry_lines.append(f"  description: {description}")
    
    new_entry = "\n".join(entry_lines)

    # Search for <!-- tracks: ... -->
    tracks_match = re.search(r'(<!--\s*tracks:\s*)(.*?)(\s*-->)', content, re.DOTALL)
    if tracks_match:
        prefix = tracks_match.group(1).rstrip()
        existing = tracks_match.group(2).strip()
        if existing:
            updated_body = f"{prefix}\n{existing}\n{new_entry}\n-->"
        else:
            updated_body = f"{prefix}\n{new_entry}\n-->"
        content = content[:tracks_match.start()] + updated_body + content[tracks_match.end():]
    else:
        # If no tracks comment exists, append to Section 02
        if "## 02. tracklist" in content:
            content = content.replace("## 02. tracklist", f"## 02. tracklist\n\n<!-- tracks:\n{new_entry}\n-->")
        else:
            content += f"\n\n## 02. tracklist\n\n<!-- tracks:\n{new_entry}\n-->\n"

    with open(audio_md_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Add audio track to content/audio.md")
    parser.add_argument("--file", default="content/audio.md", help="Path to content/audio.md")
    parser.add_argument("--title", required=True, help="Track title")
    parser.add_argument("--src", required=True, help="Audio src (e.g. /media/song.mp3)")
    parser.add_argument("--duration", default="--:--", help="Track duration (e.g. 03:20)")
    parser.add_argument("--date", default=None, help="Recording / release date")
    parser.add_argument("--description", default=None, help="Track description / liner notes")

    args = parser.parse_args()
    add_track(
        audio_md_path=args.file,
        title=args.title,
        src=args.src,
        duration=args.duration,
        date=args.date,
        description=args.description
    )

if __name__ == "__main__":
    main()
