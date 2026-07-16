#!/usr/bin/env bash
# Verify first frame, last frame, frame count, MP4 frame count, and duration.
# Usage: ./verify_animation.sh FRAME_DIRECTORY VIDEO.mp4
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 FRAME_DIRECTORY VIDEO.mp4" >&2
  exit 2
fi

frame_dir=$1
video=$2

echo "First frame:"
find "$frame_dir" -maxdepth 1 -name '*.png' | sort | head -1

echo "Last frame:"
find "$frame_dir" -maxdepth 1 -name '*.png' | sort | tail -1

echo -n "PNG frame count: "
find "$frame_dir" -maxdepth 1 -name '*.png' | wc -l

echo -n "MP4 frame count: "
ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=nb_read_frames \
  -of default=nokey=1:noprint_wrappers=1 "$video"

echo -n "Duration: "
ffprobe -v error -show_entries format=duration \
  -of default=nokey=1:noprint_wrappers=1 "$video"
