#!/usr/bin/env bash
# edit-post.sh - Quickly locate and edit an existing blog post in content/blog/

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENT_DIR="${DIR}/content/blog"

if [ ! -d "${CONTENT_DIR}" ]; then
  echo "Error: content directory not found at ${CONTENT_DIR}"
  exit 1
fi

# Detect preferred editor
EDITOR_CMD="${VISUAL:-${EDITOR:-nvim}}"
if ! command -v "${EDITOR_CMD}" &> /dev/null; then
  if command -v nvim &> /dev/null; then
    EDITOR_CMD="nvim"
  elif command -v vim &> /dev/null; then
    EDITOR_CMD="vim"
  elif command -v vi &> /dev/null; then
    EDITOR_CMD="vi"
  elif command -v nano &> /dev/null; then
    EDITOR_CMD="nano"
  else
    echo "Error: No suitable text editor found."
    exit 1
  fi
fi

QUERY="$1"
TARGET_FILE=""

# If query provided, search for matches
if [ -n "${QUERY}" ]; then
  MATCHES=($(find "${CONTENT_DIR}" -maxdepth 1 -type f -iname "*${QUERY}*.md" | sort -r))
  if [ ${#MATCHES[@]} -eq 1 ]; then
    TARGET_FILE="${MATCHES[0]}"
  elif [ ${#MATCHES[@]} -gt 1 ]; then
    echo "Multiple posts match '${QUERY}':"
    if command -v fzf &> /dev/null; then
      TARGET_FILE=$(printf "%s\n" "${MATCHES[@]}" | sed "s|${CONTENT_DIR}/||" | fzf --reverse --header="Select post to edit:" || true)
      [ -n "${TARGET_FILE}" ] && TARGET_FILE="${CONTENT_DIR}/${TARGET_FILE}"
    else
      select opt in "${MATCHES[@]}"; do
        if [ -n "$opt" ]; then
          TARGET_FILE="$opt"
          break
        fi
      done
    fi
  else
    echo "No posts matched '${QUERY}'. Listing all posts instead..."
  fi
fi

# If no target file selected yet, open interactive picker
if [ -z "${TARGET_FILE}" ]; then
  ALL_POSTS=($(find "${CONTENT_DIR}" -maxdepth 1 -type f -name "*.md" | sort -r))
  if [ ${#ALL_POSTS[@]} -eq 0 ]; then
    echo "No markdown posts found in ${CONTENT_DIR}."
    exit 1
  fi

  if command -v fzf &> /dev/null; then
    SELECTED=$(printf "%s\n" "${ALL_POSTS[@]}" | sed "s|${CONTENT_DIR}/||" | fzf --reverse --header="Select post to edit (Esc to cancel):" || true)
    if [ -n "${SELECTED}" ]; then
      TARGET_FILE="${CONTENT_DIR}/${SELECTED}"
    fi
  else
    echo "Select a post to edit (newest first):"
    PS3="Enter number (or Ctrl+C to cancel): "
    DISPLAY_POSTS=()
    for p in "${ALL_POSTS[@]}"; do
      DISPLAY_POSTS+=("$(basename "$p")")
    done
    select opt in "${DISPLAY_POSTS[@]}"; do
      if [ -n "$opt" ]; then
        TARGET_FILE="${CONTENT_DIR}/${opt}"
        break
      fi
    done
  fi
fi

if [ -z "${TARGET_FILE}" ]; then
  echo "No post selected."
  exit 0
fi

echo "Opening: ${TARGET_FILE}"
${EDITOR_CMD} "${TARGET_FILE}"

echo ""
echo "Saved edits to: ${TARGET_FILE}"
echo "-> To build and deploy changes to Raspberry Pi, run: ./deploy.sh"
