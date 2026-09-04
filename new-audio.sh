#!/usr/bin/env bash
# new-audio.sh - Add a new audio track to /audio and binbot.dev

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENT_FILE="${DIR}/content/audio.md"
MEDIA_DIR="${DIR}/media"

mkdir -p "${MEDIA_DIR}"

# Detect editor (same priority as new-post.sh & edit-post.sh)
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
    EDITOR_CMD=""
  fi
fi

# Track audio file input
AUDIO_INPUT="$1"
if [ -z "${AUDIO_INPUT}" ]; then
  echo "=== binbot.dev Audio Track Uploader ==="
  echo ""
  read -p "Audio file path or filename (e.g. ~/Music/rain.mp3 or rain.mp3): " AUDIO_INPUT
fi

if [ -z "${AUDIO_INPUT}" ]; then
  echo "Error: Audio file cannot be empty."
  exit 1
fi

# Determine source path and copy to media/ if needed
if [ -f "${AUDIO_INPUT}" ]; then
  RAW_BASENAME=$(basename "${AUDIO_INPUT}")
  SAFE_BASENAME=$(echo "${RAW_BASENAME}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g')
  TARGET_PATH="${MEDIA_DIR}/${SAFE_BASENAME}"
  
  REAL_SRC=$(realpath "${AUDIO_INPUT}")
  REAL_DEST=$(realpath -m "${TARGET_PATH}")
  if [ "${REAL_SRC}" != "${REAL_DEST}" ]; then
    cp "${AUDIO_INPUT}" "${TARGET_PATH}"
    echo "-> Copied '${AUDIO_INPUT}' to 'media/${SAFE_BASENAME}'"
  fi
  AUDIO_SRC="/media/${SAFE_BASENAME}"
else
  # Filename entered directly without existing local path
  SAFE_BASENAME=$(basename "${AUDIO_INPUT}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g')
  AUDIO_SRC="/media/${SAFE_BASENAME}"
  echo "-> Note: Local file '${AUDIO_INPUT}' not found. Using '${AUDIO_SRC}'."
  echo "   Remember to place '${SAFE_BASENAME}' in 'media/' before deploying!"
fi

# Title
TITLE="$2"
if [ -z "${TITLE}" ]; then
  DEFAULT_TITLE=$(basename "${SAFE_BASENAME}" | sed -E 's/\.[^.]+$//' | tr '-' ' ')
  read -p "Track title [${DEFAULT_TITLE}]: " TITLE
  [ -z "${TITLE}" ] && TITLE="${DEFAULT_TITLE}"
fi

# Duration
read -p "Track duration (MM:SS, default --:--): " DURATION
[ -z "${DURATION}" ] && DURATION="--:--"

# Date
DEFAULT_DATE=$(date +"%Y-%m-%d")
read -p "Recording / Release date [${DEFAULT_DATE}]: " DATE
[ -z "${DATE}" ] && DATE="${DEFAULT_DATE}"

# Description
read -p "Track description / liner notes (optional): " DESCRIPTION

# Add track using python helper
python3 "${DIR}/scripts/add_audio.py" \
  --file "${CONTENT_FILE}" \
  --title "${TITLE}" \
  --src "${AUDIO_SRC}" \
  --duration "${DURATION}" \
  --date "${DATE}" \
  --description "${DESCRIPTION}"

echo ""
echo "-> Added track to content/audio.md"
echo "-> Building site..."
python3 "${DIR}/build.py"

echo ""
echo "Successfully added '${TITLE}' to /audio!"
echo "-> To preview locally: python3 -m http.server 8080"
echo "-> To deploy to Raspberry Pi: ./deploy.sh"
echo ""

if [ -n "${EDITOR_CMD}" ]; then
  read -p "Open content/audio.md in ${EDITOR_CMD} now to inspect/edit? [y/N]: " OPEN_ED
  if [[ "${OPEN_ED}" =~ ^[Yy]$ ]]; then
    ${EDITOR_CMD} "${CONTENT_FILE}"
    echo "-> Rebuilding site with any manual edits..."
    python3 "${DIR}/build.py"
  fi
fi
