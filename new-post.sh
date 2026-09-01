#!/bin/bash
# new-post.sh - Create a new blog post in Markdown and open in your editor

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENT_DIR="${DIR}/content/blog"

mkdir -p "${CONTENT_DIR}"

TITLE="$1"
if [ -z "${TITLE}" ]; then
  read -p "Enter post title: " TITLE
fi

if [ -z "${TITLE}" ]; then
  echo "Error: Title cannot be empty."
  exit 1
fi

DATE=$(date +"%Y-%m-%d")

# Create slug: lowercase, replace spaces and special characters with hyphens
SLUG=$(echo "${TITLE}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')

FILENAME="${CONTENT_DIR}/${DATE}-${SLUG}.md"

if [ -f "${FILENAME}" ]; then
  echo "File already exists: ${FILENAME}"
else
  cat << POST_EOF > "${FILENAME}"
---
title: ${TITLE}
date: ${DATE}
description: Brief description of ${TITLE}
tags: blog, linux, hardware
slug: ${SLUG}
---

## 01. introduction

Start typing your transmission here in Markdown...

POST_EOF
  echo "Created new post: ${FILENAME}"
fi

# Detect editor
if [ -n "${EDITOR}" ]; then
  ${EDITOR} "${FILENAME}"
elif command -v nvim &> /dev/null; then
  nvim "${FILENAME}"
elif command -v vim &> /dev/null; then
  vim "${FILENAME}"
elif command -v vi &> /dev/null; then
  vi "${FILENAME}"
else
  echo "Post created at: ${FILENAME}"
  echo "You can edit it with: nvim \"${FILENAME}\""
fi
