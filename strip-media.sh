#!/usr/bin/env bash
# strip-media.sh - Strip all EXIF, GPS, camera, and device metadata from media files

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-${DIR}/media}"

if [ -f "$TARGET" ]; then
  echo "Stripping EXIF metadata from file: $TARGET"
  magick mogrify -strip "$TARGET"
  echo "Done!"
elif [ -d "$TARGET" ]; then
  echo "Stripping EXIF metadata from all images in: $TARGET"
  find "$TARGET" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.tiff" \) -exec magick mogrify -strip {} +
  echo "Done! All images sanitized."
else
  echo "Usage: ./strip-media.sh [path/to/image.jpg | path/to/folder]"
  exit 1
fi
