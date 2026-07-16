#!/usr/bin/env bash
set -euo pipefail

# Print the duration, frame count, and frame rate for every MP4 in a directory.
#
# Usage:
#   ./verify_movies.sh [MOVIE_DIRECTORY]
#
# Example:
#   ./verify_movies.sh november_movies_4fps

MOVIE_DIR="${1:-movies_4fps}"

if [[ ! -d "$MOVIE_DIR" ]]; then
    echo "ERROR: Movie directory does not exist: $MOVIE_DIR" >&2
    exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
    echo "ERROR: ffprobe is not installed or not in PATH." >&2
    exit 1
fi

mapfile -t movies < <(find "$MOVIE_DIR" -maxdepth 1 -type f -name '*.mp4' -print | sort)

if (( ${#movies[@]} == 0 )); then
    echo "No MP4 files found in: $MOVIE_DIR"
    exit 0
fi

printf "%-38s %12s %12s %14s\n" "MOVIE" "DURATION" "FRAMES" "AVG_FRAME_RATE"
printf '%*s\n' 82 '' | tr ' ' '-'

for movie in "${movies[@]}"; do
    duration="$(
        ffprobe -v error \
            -show_entries format=duration \
            -of default=noprint_wrappers=1:nokey=1 \
            "$movie"
    )"

    frame_info="$(
        ffprobe -v error \
            -select_streams v:0 \
            -show_entries stream=nb_frames,avg_frame_rate \
            -of csv=p=0 \
            "$movie"
    )"

    IFS=',' read -r avg_rate frames <<< "$frame_info"

    printf "%-38s %12s %12s %14s\n" \
        "$(basename "$movie")" \
        "${duration:-unknown}" \
        "${frames:-unknown}" \
        "${avg_rate:-unknown}"
done
