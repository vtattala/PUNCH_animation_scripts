#!/usr/bin/env bash
set -euo pipefail

# Build synchronized PUNCH/IPS MP4 movies from existing PNG frame sequences.
#
# Usage:
#   ./make_plot_movies.sh --input DIR --output DIR --fps FPS
#
# Example:
#   ./make_plot_movies.sh \
#     --input /home/soft/vtattala/data/punch_Nov_25_nv3h_images \
#     --output /home/soft/vtattala/data/punch_Nov_25_nv3h_images/november_movies_4fps \
#     --fps 4

INPUT_DIR="."
OUTPUT_DIR="movies_4fps"
FPS="4"

while (( $# > 0 )); do
    case "$1" in
        --input)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --fps)
            FPS="$2"
            shift 2
            ;;
        -h|--help)
            sed -n '1,20p' "$0"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "ERROR: Input directory does not exist: $INPUT_DIR" >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ERROR: ffmpeg is not installed or not in PATH." >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Convert paths to absolute paths before changing directories.
INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"
OUTPUT_DIR="$(mkdir -p "$OUTPUT_DIR" && cd "$OUTPUT_DIR" && pwd)"

make_movie() {
    local pattern="$1"
    local output_name="$2"

    local list_file
    list_file="$(mktemp)"
    trap 'rm -f "$list_file"' RETURN

    find "$INPUT_DIR" -maxdepth 1 -type f -name "$pattern" -print \
        | sort \
        | while IFS= read -r frame; do
            # Escape single quotes for FFmpeg concat-list syntax.
            escaped="${frame//\'/\'\\\'\'}"
            printf "file '%s'\n" "$escaped"
        done > "$list_file"

    local frame_count
    frame_count="$(wc -l < "$list_file")"

    if (( frame_count == 0 )); then
        echo "SKIP: $output_name"
        echo "      No files matched: $pattern"
        return 0
    fi

    echo "BUILD: $output_name"
    echo "       Pattern: $pattern"
    echo "       Frames:  $frame_count"
    echo "       FPS:     $FPS"

    ffmpeg -y \
        -r "$FPS" \
        -f concat \
        -safe 0 \
        -i "$list_file" \
        -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" \
        -c:v libx264 \
        -pix_fmt yuv420p \
        "$OUTPUT_DIR/$output_name"
}

# Density
make_movie "PUNCH-IPS_N_Ecliptic-cut_p_*.png"   "N_Ecliptic.mp4"
make_movie "PUNCH-IPS_N_Meridional-cut_p_*.png" "N_Meridional.mp4"
make_movie "PUNCH-IPS_N_Synoptic_map_*.png"     "N_Synoptic.mp4"

# Velocity
make_movie "PUNCH-IPS_V_Ecliptic-cut_p_*.png"   "V_Ecliptic.mp4"
make_movie "PUNCH-IPS_V_Meridional-cut_p_*.png" "V_Meridional.mp4"
make_movie "PUNCH-IPS_V_Synoptic_map_*.png"     "V_Synoptic.mp4"
make_movie "PUNCH-IPS_V_Fisheye_*.png"          "V_Fisheye.mp4"
make_movie "PUNCH-IPS_V_H-A_*.png"              "V_H_A.mp4"

# Brightness
make_movie "PUNCH-IPS_B_H-A_*.png"              "B_H_A.mp4"

# Important: *_b.png does not match *_b_small.png, so the two
# brightness fisheye products stay separated.
make_movie "PUNCH-IPS_B_Fisheye_*_b.png"        "B_Fisheye_110.mp4"
make_movie "PUNCH-IPS_B_Fisheye_*_b_small.png"  "B_Fisheye_50.mp4"

# Optional IPS fisheye sequence.
make_movie "PUNCH-IPS_IPS_Fisheye_*.png"        "IPS_Fisheye.mp4"

echo
echo "Finished. Movies are stored in:"
echo "  $OUTPUT_DIR"
find "$OUTPUT_DIR" -maxdepth 1 -type f -name '*.mp4' -printf '  %f\n' | sort
