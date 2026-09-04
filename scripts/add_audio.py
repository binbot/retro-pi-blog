#!/usr/bin/env python3
"""
scripts/add_audio.py - Helper script to inspect audio files and add track entries to content/audio.md
"""

import os
import re
import sys
import json
import struct
import argparse

AUDIO_EXTS = ('.mp3', '.ogg', '.flac', '.wav', '.m4a', '.aac', '.opus')

def inspect_audio_file(filepath):
    """Detect title and estimated duration for an audio file."""
    if not os.path.exists(filepath):
        return {"error": "File not found"}

    basename = os.path.basename(filepath)
    name_no_ext = os.path.splitext(basename)[0]
    default_title = re.sub(r'[_\-]+', ' ', name_no_ext).strip()

    duration_str = "--:--"
    title = default_title

    # Try reading mp3 duration and ID3 title
    try:
        with open(filepath, 'rb') as f:
            data = f.read()

        offset = 0
        if data[:3] == b'ID3':
            size = ((data[6] & 0x7f) << 21) | ((data[7] & 0x7f) << 14) | ((data[8] & 0x7f) << 7) | (data[9] & 0x7f)
            id3_data = data[10:10+size]
            offset = 10 + size
            tit2_idx = id3_data.find(b'TIT2')
            if tit2_idx != -1:
                frame_size = struct.unpack('>I', id3_data[tit2_idx+4:tit2_idx+8])[0]
                raw = id3_data[tit2_idx+10:tit2_idx+10+frame_size]
                enc = raw[0]
                if enc == 0: t = raw[1:].decode('latin1', errors='ignore')
                elif enc == 1: t = raw[1:].decode('utf-16', errors='ignore')
                elif enc == 3: t = raw[1:].decode('utf-8', errors='ignore')
                else: t = raw[1:].decode('utf-8', errors='ignore')
                t = t.strip('\x00').strip()
                if t: title = t

        bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
        idx = offset
        while idx < len(data) - 4:
            if data[idx] == 0xFF and (data[idx+1] & 0xE0) == 0xE0:
                header = struct.unpack('>I', data[idx:idx+4])[0]
                version = (header >> 19) & 3
                layer = (header >> 17) & 3
                br_idx = (header >> 12) & 0xF
                sr_idx = (header >> 10) & 3
                if version == 3 and layer == 1 and 0 < br_idx < 15 and sr_idx < 3:
                    bitrate_kbps = bitrates[br_idx]
                    audio_bytes = len(data) - offset
                    seconds = int((audio_bytes * 8) / (bitrate_kbps * 1000))
                    duration_str = f'{seconds // 60:02d}:{seconds % 60:02d}'
                    break
            idx += 1
    except Exception:
        pass

    return {
        "filepath": filepath,
        "basename": basename,
        "title": title,
        "duration": duration_str
    }

def get_unindexed_audio(audio_md_path, media_dir):
    """Find audio files in media/ that are not yet listed in audio.md."""
    indexed_srcs = set()
    if os.path.exists(audio_md_path):
        with open(audio_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'src:\s*([^\s\n]+)', content):
            indexed_srcs.add(os.path.basename(m.group(1)))

    unindexed = []
    if os.path.exists(media_dir):
        for fname in sorted(os.listdir(media_dir)):
            if fname.lower().endswith(AUDIO_EXTS):
                if fname not in indexed_srcs:
                    unindexed.append(fname)
    return unindexed

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
        if "## 02. tracklist" in content:
            content = content.replace("## 02. tracklist", f"## 02. tracklist\n\n<!-- tracks:\n{new_entry}\n-->")
        else:
            content += f"\n\n## 02. tracklist\n\n<!-- tracks:\n{new_entry}\n-->\n"

    with open(audio_md_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Audio utility for binbot.dev")
    parser.add_argument("--inspect", help="Inspect an audio file and output JSON metadata")
    parser.add_argument("--unindexed", action="store_true", help="List audio files in media/ not yet in audio.md")
    parser.add_argument("--file", default="content/audio.md", help="Path to content/audio.md")
    parser.add_argument("--media-dir", default="media", help="Path to media directory")
    parser.add_argument("--title", help="Track title")
    parser.add_argument("--src", help="Audio src (e.g. /media/song.mp3)")
    parser.add_argument("--duration", default="--:--", help="Track duration (e.g. 03:20)")
    parser.add_argument("--date", default=None, help="Recording / release date")
    parser.add_argument("--description", default=None, help="Track description / liner notes")

    args = parser.parse_args()

    if args.inspect:
        info = inspect_audio_file(args.inspect)
        print(json.dumps(info))
        return

    if args.unindexed:
        unindexed = get_unindexed_audio(args.file, args.media_dir)
        for item in unindexed:
            print(item)
        return

    if args.title and args.src:
        add_track(
            audio_md_path=args.file,
            title=args.title,
            src=args.src,
            duration=args.duration,
            date=args.date,
            description=args.description
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
