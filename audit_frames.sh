#!/usr/bin/env bash
set -euo pipefail

# Audit recognized PUNCH/IPS PNG frame sequences.
#
# Usage:
#   ./audit_frames.sh [INPUT_DIRECTORY]
#
# Example:
#   ./audit_frames.sh /home/soft/vtattala/data/punch_Nov_25_nv3h_images

INPUT_DIR="${1:-.}"

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "ERROR: Input directory does not exist: $INPUT_DIR" >&2
    exit 1
fi

cd "$INPUT_DIR"

patterns=(
    "PUNCH-IPS_N_Ecliptic-cut_p_*.png"
    "PUNCH-IPS_N_Meridional-cut_p_*.png"
    "PUNCH-IPS_N_Synoptic_map_*.png"
    "PUNCH-IPS_V_Ecliptic-cut_p_*.png"
    "PUNCH-IPS_V_Meridional-cut_p_*.png"
    "PUNCH-IPS_V_Synoptic_map_*.png"
    "PUNCH-IPS_V_Fisheye_*.png"
    "PUNCH-IPS_V_H-A_*.png"
    "PUNCH-IPS_B_H-A_*.png"
    "PUNCH-IPS_B_Fisheye_*_b.png"
    "PUNCH-IPS_B_Fisheye_*_b_small.png"
    "PUNCH-IPS_IPS_Fisheye_*.png"
)

printf "%-48s %8s  %s\n" "PATTERN" "COUNT" "FIRST / LAST"
printf '%*s\n' 110 '' | tr ' ' '-'

for pattern in "${patterns[@]}"; do
    mapfile -t files < <(find . -maxdepth 1 -type f -name "$pattern" -printf '%f\n' | sort)
    count="${#files[@]}"

    if (( count == 0 )); then
        printf "%-48s %8d  %s\n" "$pattern" 0 "MISSING"
        continue
    fi

    printf "%-48s %8d  FIRST: %s\n" "$pattern" "$count" "${files[0]}"
    printf "%-48s %8s  LAST:  %s\n" "" "" "${files[$((count - 1))]}"
done

echo
echo "Placeholder timestamp files:"
find . -maxdepth 1 -type f -name '*20000101-0000UT*.png' -printf '%f\n' | sort || true
