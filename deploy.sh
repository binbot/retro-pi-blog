#!/usr/bin/env bash
# deploy.sh - Build markdown files, sync to Raspberry Pi, and push to Git remotes

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_HOST="pipi"
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
  --exclude="strip-media.sh" \
  --exclude="*.conf" \
  --exclude="deploy_guide.md" \
  "${DIR}/" "${PI_USER}@${PI_HOST}:${WEB_ROOT}/"

echo "=== 3. Syncing with Git Remotes ==="
cd "${DIR}"
if [[ -n $(git status --porcelain) ]]; then
  echo "-> Staging changes and committing..."
  git add -A
  DATE_NOW=$(date +"%Y-%m-%d %H:%M")
  git commit -m "chore(deploy): sync site build & transmissions (${DATE_NOW})" || true
  
  echo "-> Pushing to origin (GitHub)..."
  git push origin main || true
  
  if git remote | grep -q "^codeberg$"; then
    echo "-> Pushing to codeberg..."
    git push codeberg main 2>/dev/null || true
  fi
  echo "-> Git sync complete!"
else
  echo "-> Working tree clean, nothing new to commit."
fi

echo "=== Deployment Complete! Live at https://binbot.dev ==="
