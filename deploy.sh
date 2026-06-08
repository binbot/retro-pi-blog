#!/bin/bash
# Sync website files to the Raspberry Pi

PI_IP="192.168.86.250"
PI_USER="binbot"
WEB_ROOT="/var/www/retro-blog"

echo "=== Syncing Website Files to Pi ==="
rsync -avz --delete --exclude="deploy.sh" --exclude="nginx.conf" --exclude="deploy_guide.md" /home/b/Projects/retro-pi-blog/ ${PI_USER}@${PI_IP}:${WEB_ROOT}/
echo "=== Sync Successful! Access at http://${PI_IP} ==="
