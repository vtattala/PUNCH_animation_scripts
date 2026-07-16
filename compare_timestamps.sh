#!/usr/bin/env bash
set -euo pipefail

# Compare timestamps encoded in two PNG filename patterns.
#
# Usage:
#   ./compare_timestamps.sh 'PATTERN_A' 'PATTERN_B' [INPUT_DIRECTORY]
#
# Example:
#   ./compare_timestamps.sh \
#     'PUNCH-IPS_N_Ecliptic-cut_p_*.png' \
#     'PUNCH-IPS_N_Synoptic_map_*.png' \
#     .

if (( $# < 2 )); then
    echo "Usage: $0 'PATTERN_A' 'PATTERN_B' [INPUT_DIRECTORY]" >&2
    exit 1
fi

PATTERN_A="$1"
PATTERN_B="$2"
INPUT_DIR="${3:-.}"

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "ERROR: Input directory does not exist: $INPUT_DIR" >&2
    exit 1
fi

tmp_a="$(mktemp)"
tmp_b="$(mktemp)"
trap 'rm -f "$tmp_a" "$tmp_b"' EXIT

find "$INPUT_DIR" -maxdepth 1 -type f -name "$PATTERN_A" -printf '%f\n' \
    | sed -nE 's/.*_([0-9]{8}-[0-9]{4}UT)_.*/\1/p' \
    | sort -u > "$tmp_a"

find "$INPUT_DIR" -maxdepth 1 -type f -name "$PATTERN_B" -printf '%f\n' \
    | sed -nE 's/.*_([0-9]{8}-[0-9]{4}UT)_.*/\1/p' \
    | sort -u > "$tmp_b"

echo "Timestamps in A but missing from B:"
comm -23 "$tmp_a" "$tmp_b" || true

echo
echo "Timestamps in B but missing from A:"
comm -13 "$tmp_a" "$tmp_b" || true

echo
echo "Counts:"
printf "A: %s\n" "$(wc -l < "$tmp_a")"
printf "B: %s\n" "$(wc -l < "$tmp_b")"
