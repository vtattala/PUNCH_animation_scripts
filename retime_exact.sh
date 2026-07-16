#!/usr/bin/env bash
# Retime an MP4 to an exact duration without changing its image content.
# Usage: ./retime_exact.sh input.mp4 output.mp4 164
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 INPUT.mp4 OUTPUT.mp4 EXACT_SECONDS" >&2
  exit 2
fi

input=$1
output=$2
target=$3

duration=$(ffprobe -v error -show_entries format=duration \
  -of default=nokey=1:noprint_wrappers=1 "$input")

factor=$(python3 - "$duration" "$target" <<'PY'
import sys
current = float(sys.argv[1])
target = float(sys.argv[2])
if current <= 0 or target <= 0:
    raise SystemExit("Durations must be positive")
print(target / current)
PY
)

echo "Current duration: $duration"
echo "Target duration:  $target"
echo "setpts factor:    $factor"

ffmpeg -y -i "$input" -vf "setpts=${factor}*PTS" -an "$output"

ffprobe -v error -show_entries format=duration \
  -of default=nokey=1:noprint_wrappers=1 "$output"
