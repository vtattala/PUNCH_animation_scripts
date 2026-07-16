#!/usr/bin/env bash
set -euo pipefail

# Safely move known placeholder PNG frames out of the source directory.
#
# Default placeholder timestamp:
#   20000101-0000UT
#
# Usage:
#   ./clean_bad_frames.sh [INPUT_DIRECTORY] [PLACEHOLDER_TEXT]
#
# Example:
#   ./clean_bad_frames.sh . 20000101-0000UT

INPUT_DIR="${1:-.}"
PLACEHOLDER="${2:-20000101-0000UT}"
QUARANTINE_DIR="$INPUT_DIR/excluded_bad_frames"

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "ERROR: Input directory does not exist: $INPUT_DIR" >&2
    exit 1
fi

mkdir -p "$QUARANTINE_DIR"

mapfile -t bad_files < <(
    find "$INPUT_DIR" -maxdepth 1 -type f -name "*${PLACEHOLDER}*.png" -print | sort
)

if (( ${#bad_files[@]} == 0 )); then
    echo "No placeholder frames found containing: $PLACEHOLDER"
    exit 0
fi

echo "Moving ${#bad_files[@]} placeholder frame(s) to:"
echo "  $QUARANTINE_DIR"

for file in "${bad_files[@]}"; do
    echo "  $(basename "$file")"
    mv -- "$file" "$QUARANTINE_DIR/"
done

echo "Done. No files were deleted."
