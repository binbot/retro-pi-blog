#!/usr/bin/env bash
# Shortcut to generate listening report and publish to blog
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${DIR}/scripts/daily_music_log.py" "$@"
