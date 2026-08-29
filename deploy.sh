#!/bin/bash
# deploy.sh - Build markdown files and sync to Raspberry Pi

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_HOST="pipi.local"
PI_USER="binbot"
WEB_ROOT="/var/www/retro-blog"

echo "=== 1. Building Static Site from Markdown ==="
python3 "${DIR}/build.py"

echo "=== 2. Syncing Website Files to Raspberry Pi (${PI_HOST}) ==="
rsync -avz --delete \
  --exclude=".git" \
  --exclude=".gitignore" \
  --exclude="content" \
  --exclude="build.py" \
  --exclude="new-post.sh" \
  --exclude="scripts" \
  --exclude="deploy.sh" \
  --exclude="*.conf" \
  --exclude="deploy_guide.md" \
  "${DIR}/" "${PI_USER}@${PI_HOST}:${WEB_ROOT}/"

echo "=== Deployment Complete! Live at https://binbot.dev ==="


