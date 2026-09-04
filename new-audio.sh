#!/usr/bin/env bash
# new-audio.sh - Add a new audio track to /audio and binbot.dev

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTENT_FILE="${DIR}/content/audio.md"
MEDIA_DIR="${DIR}/media"

mkdir -p "${MEDIA_DIR}"

# Detect editor
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

echo "=== binbot.dev Audio Track Uploader ==="
echo ""

AUDIO_INPUT="$1"

# Helper to normalize paths (expand tilde and strip surrounding quotes)
normalize_path() {
  local p="$1"
  p="${p/#\~/$HOME}"
  p="${p#\"}"
  p="${p%\"}"
  p="${p#\'}"
  p="${p%\'}"
  echo "$p"
}

# If no audio file specified, check for unindexed tracks in media/
if [ -z "${AUDIO_INPUT}" ]; then
  UNINDEXED=($(python3 "${DIR}/scripts/add_audio.py" --unindexed --file "${CONTENT_FILE}" --media-dir "${MEDIA_DIR}"))
  
  if [ ${#UNINDEXED[@]} -gt 0 ]; then
    echo "Found audio file(s) in media/ not yet on /audio:"
    for i in "${!UNINDEXED[@]}"; do
      printf "  %d) %s\n" "$((i+1))" "${UNINDEXED[$i]}"
    done
    echo "  o) Enter custom path or new filename"
    echo ""
    read -p "Select a file [1-${#UNINDEXED[@]} or o]: " CHOICE || true
    
    if [[ "${CHOICE}" =~ ^[0-9]+$ ]] && [ "${CHOICE}" -ge 1 ] && [ "${CHOICE}" -le "${#UNINDEXED[@]}" ]; then
      AUDIO_INPUT="${UNINDEXED[$((CHOICE-1))]}"
    fi
  fi
fi

# If still empty, prompt for path
if [ -z "${AUDIO_INPUT}" ] || [ "${AUDIO_INPUT}" = "o" ] || [ "${AUDIO_INPUT}" = "O" ]; then
  read -p "Enter audio file path or filename in media/: " AUDIO_INPUT || true
fi

AUDIO_INPUT=$(normalize_path "${AUDIO_INPUT}")

if [ -z "${AUDIO_INPUT}" ]; then
  echo "Error: Audio file cannot be empty."
  exit 1
fi

# Locate the actual file on disk
RESOLVED_FILE=""
if [ -f "${AUDIO_INPUT}" ]; then
  RESOLVED_FILE="${AUDIO_INPUT}"
elif [ -f "${MEDIA_DIR}/${AUDIO_INPUT}" ]; then
  RESOLVED_FILE="${MEDIA_DIR}/${AUDIO_INPUT}"
elif [ -f "${DIR}/${AUDIO_INPUT}" ]; then
  RESOLVED_FILE="${DIR}/${AUDIO_INPUT}"
fi

if [ -n "${RESOLVED_FILE}" ]; then
  RAW_BASENAME=$(basename "${RESOLVED_FILE}")
  SAFE_BASENAME=$(echo "${RAW_BASENAME}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g')
  TARGET_PATH="${MEDIA_DIR}/${SAFE_BASENAME}"

  REAL_SRC=$(realpath "${RESOLVED_FILE}")
  REAL_DEST=$(realpath -m "${TARGET_PATH}")
  if [ "${REAL_SRC}" != "${REAL_DEST}" ]; then
    cp "${RESOLVED_FILE}" "${TARGET_PATH}"
    echo "-> Copied '${RESOLVED_FILE}' to 'media/${SAFE_BASENAME}'"
  fi
  AUDIO_SRC="/media/${SAFE_BASENAME}"
  FINAL_FILE_PATH="${TARGET_PATH}"
else
  SAFE_BASENAME=$(basename "${AUDIO_INPUT}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g')
  AUDIO_SRC="/media/${SAFE_BASENAME}"
  FINAL_FILE_PATH=""
  echo "-> Note: Local file '${AUDIO_INPUT}' not found yet. Using src '${AUDIO_SRC}'."
  echo "   Remember to place '${SAFE_BASENAME}' in 'media/' before deploying!"
fi

# Inspect audio file for duration and title
DETECTED_TITLE=""
DETECTED_DURATION="--:--"
if [ -n "${FINAL_FILE_PATH}" ] && [ -f "${FINAL_FILE_PATH}" ]; then
  INSPECT_JSON=$(python3 "${DIR}/scripts/add_audio.py" --inspect "${FINAL_FILE_PATH}")
  DETECTED_TITLE=$(echo "${INSPECT_JSON}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('title', ''))")
  DETECTED_DURATION=$(echo "${INSPECT_JSON}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('duration', '--:--'))")
fi

if [ -z "${DETECTED_TITLE}" ]; then
  DETECTED_TITLE=$(basename "${SAFE_BASENAME}" | sed -E 's/\.[^.]+$//' | tr '_' ' ' | tr '-' ' ')
fi

# Title
TITLE="$2"
if [ -z "${TITLE}" ]; then
  read -p "Track title [${DETECTED_TITLE}]: " TITLE || true
  [ -z "${TITLE}" ] && TITLE="${DETECTED_TITLE}"
fi

# Duration
read -p "Track duration [${DETECTED_DURATION}]: " DURATION || true
[ -z "${DURATION}" ] && DURATION="${DETECTED_DURATION}"

# Date
DEFAULT_DATE=$(date +"%Y-%m-%d")
read -p "Recording / Release date [${DEFAULT_DATE}]: " DATE || true
[ -z "${DATE}" ] && DATE="${DEFAULT_DATE}"

# Description
read -p "Track description / liner notes (optional): " DESCRIPTION || true

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
echo "Successfully added '${TITLE}' (${DURATION}) to /audio!"
echo "-> To preview locally: python3 -m http.server 8080"
echo "-> To deploy to Raspberry Pi: ./deploy.sh"
echo ""

if [ -n "${EDITOR_CMD}" ]; then
  read -p "Open content/audio.md in ${EDITOR_CMD} now to inspect/edit? [y/N]: " OPEN_ED || true
  if [[ "${OPEN_ED}" =~ ^[Yy]$ ]]; then
    ${EDITOR_CMD} "${CONTENT_FILE}"
    echo "-> Rebuilding site with any manual edits..."
    python3 "${DIR}/build.py"
  fi
fi
