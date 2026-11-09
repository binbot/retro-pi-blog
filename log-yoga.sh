#!/usr/bin/env bash
# Shortcut to generate daily yoga practice report from Down Dog and publish to blog
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${DIR}/scripts/daily_yoga_log.py" "$@"
