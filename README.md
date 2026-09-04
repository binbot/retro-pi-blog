# retro-pi-blog

A minimalist, lightweight personal digital outpost and blog served from a low-power Raspberry Pi at [binbot.dev](https://binbot.dev).

## Quick Start & Workflow

- **[Blog Publishing & Editing Guide (Checklist)](BLOG_GUIDE.md)**: How to create, edit, test, and deploy posts.
- **[Raspberry Pi Deployment Guide](deploy_guide.md)**: Hardware setup, OS installation, Nginx configuration, and DDNS/SSL.

### Common Commands

```bash
# Create a new post
./new-post.sh "My New Transmission"

# Edit an existing post (fuzzy search with fzf)
./edit-post.sh

# Rebuild static site locally
python3 build.py

# Build, sync to Raspberry Pi, and push to GitHub/Codeberg
./deploy.sh
```

### Architecture
- **Zero External Dependencies**: `build.py` uses only Python 3 standard library.
- **Auto Metadata Stripping**: EXIF and GPS data are automatically scrubbed from media files before deployment.
- **Pure Data Minimalist UI**: Ultra-low page weight (~5KB - 10KB) designed for vintage, low-power hardware.
