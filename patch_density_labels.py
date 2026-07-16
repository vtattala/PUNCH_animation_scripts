#!/usr/bin/env python3
"""Replace IPS density labels with PUNCH labels in generated PNG frames.

This is a presentation-only post-processing step. It does not touch raw data,
change correlations, or alter the curves plotted by ts_plot.

The default coordinates reproduce the 1560x780 PUNCH/WIND density plots used
in the original workflow. Use ``--no-bottom-label`` if only the top legend
needs changing.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frame_dir", type=Path)
    parser.add_argument("--no-bottom-label", action="store_true")
    parser.add_argument(
        "--font",
        default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    args = parser.parse_args()

    frames = sorted(args.frame_dir.expanduser().glob("*.png"))
    if not frames:
        raise SystemExit(f"No PNG frames found in {args.frame_dir}")

    top_font = ImageFont.truetype(args.font, 16)
    bottom_font = ImageFont.truetype(args.font, 28)

    for frame in frames:
        image = Image.open(frame).convert("RGB")
        draw = ImageDraw.Draw(image)

        # Replace only the word IPS in the top legend; leave Tomography intact.
        draw.rectangle((276, 150, 324, 184), fill="white")
        draw.text((266, 158), "PUNCH", fill="black", font=top_font)

        if not args.no_bottom_label:
            draw.rectangle((995, 720, 1505, 779), fill="white")
            draw.text(
                (1015, 728),
                "PUNCH Tomography n(cm⁻³)",
                fill="black",
                font=bottom_font,
            )

        image.save(frame)

    print(f"Patched {len(frames)} frames in {args.frame_dir}")


if __name__ == "__main__":
    main()
