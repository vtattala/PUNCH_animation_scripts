#!/usr/bin/env python3
"""Create time-series animations from ts_plot-compatible EA/MA/ME/e3 data.

This script reproduces the workflow used for the PUNCH time-series animations:

1. Call ``ts_plot`` once for every requested timestamp.
2. Detect the plot file that ``ts_plot`` creates, regardless of whether its
   filename begins with e3, EA, MA, ME, or another prefix.
3. Rename each plot to a timestamped PNG frame.
4. Encode the frames into an MP4 with ffmpeg.
5. Optionally retime the MP4 to an exact requested duration.

The script never edits the raw data files. It only reads them through ts_plot
and writes frames/video into the selected output directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Dict, Iterable, List


def parse_timestamp(value: str) -> dt.datetime:
    """Parse a timestamp in YYYYMMDDHH format."""
    try:
        return dt.datetime.strptime(value, "%Y%m%d%H")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid timestamp {value!r}; expected YYYYMMDDHH"
        ) from exc


def timestamp_range(start: dt.datetime, end: dt.datetime, cadence_hours: int) -> Iterable[dt.datetime]:
    """Yield an inclusive time range at a fixed hourly cadence."""
    if cadence_hours <= 0:
        raise ValueError("cadence_hours must be positive")
    if end < start:
        raise ValueError("end must not be earlier than start")

    current = start
    step = dt.timedelta(hours=cadence_hours)
    while current <= end:
        yield current
        current += step


def run_checked(command: List[str]) -> None:
    """Print and execute a command, raising on failure."""
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def file_snapshot(directory: Path) -> Dict[Path, int]:
    """Return nanosecond mtimes for every regular file in a directory."""
    snapshot: Dict[Path, int] = {}
    for item in directory.iterdir():
        if item.is_file():
            snapshot[item] = item.stat().st_mtime_ns
    return snapshot


def find_new_or_changed_file(directory: Path, before: Dict[Path, int], destination: Path) -> Path:
    """Find the newest file created or modified by the last ts_plot call.

    This avoids assuming that ts_plot always names its product ``e3*``. Newer
    PUNCH products may instead create ``EA*``, ``MA*``, or ``ME*`` outputs.
    """
    changed: List[Path] = []
    for item in directory.iterdir():
        if not item.is_file() or item.resolve() == destination.resolve():
            continue
        old_mtime = before.get(item)
        new_mtime = item.stat().st_mtime_ns
        if old_mtime is None or old_mtime != new_mtime:
            changed.append(item)

    if not changed:
        present = "\n".join(f"  {p.name}" for p in sorted(directory.iterdir()))
        raise RuntimeError(
            "ts_plot finished but no new or updated output file was detected.\n"
            f"Files currently present in {directory}:\n{present or '  <none>'}"
        )

    # Prefer common plot/image formats and then the newest modification time.
    preferred = [p for p in changed if p.suffix.lower() in {".png", ".eps", ".ps", ".jpg", ".jpeg"}]
    candidates = preferred or changed
    return max(candidates, key=lambda p: p.stat().st_mtime_ns)


def convert_to_png(source: Path, destination: Path) -> None:
    """Move a PNG directly, or convert EPS/PS/JPEG to PNG with ImageMagick.

    ts_plot normally creates PNG output in this workflow. The conversion path
    is included for portability in case another installation emits EPS/PS.
    """
    if source.suffix.lower() == ".png":
        os.replace(source, destination)
        return

    convert = shutil.which("convert") or shutil.which("magick")
    if not convert:
        raise RuntimeError(
            f"ts_plot created {source.name}, not a PNG, and ImageMagick is not installed."
        )

    if Path(convert).name == "magick":
        run_checked([convert, "convert", str(source), str(destination)])
    else:
        run_checked([convert, str(source), str(destination)])
    source.unlink(missing_ok=True)


def build_ts_plot_command(args: argparse.Namespace, current_time: dt.datetime) -> List[str]:
    """Construct one ts_plot command for one frame timestamp."""
    command = [
        args.ts_plot,
        f"-{args.measurement}",
        "-i", args.instrument,
        "-f", args.forecast,
        "-tr", args.plot_range,
        "-t", args.tomography,
        "-td", str(args.data_dir),
        "-od", str(args.frames_dir),
        "-ct", current_time.strftime("%Y%m%d%H"),
    ]

    # Density-only options used in the PUNCH workflow. Velocity intentionally
    # keeps ts_plot's default smoothing unless the user explicitly overrides it.
    if args.measurement == "d":
        if args.delta_days is not None:
            command += ["-dt", str(args.delta_days)]
        if args.ymax is not None:
            command += ["-ymax", str(args.ymax)]
    elif args.delta_days is not None:
        command += ["-dt", str(args.delta_days)]

    return command


def encode_video(args: argparse.Namespace, frame_count: int) -> Path:
    """Encode timestamped PNG frames into an MP4 and optionally retime it."""
    pattern = str(args.frames_dir / "%Y%m%d%H.png")
    # ffmpeg's glob input is more reliable here than interpreting date tokens.
    concat_file = args.output_dir / "frames.txt"
    frames = sorted(args.frames_dir.glob("*.png"))
    with concat_file.open("w", encoding="utf-8") as handle:
        for frame in frames:
            escaped = str(frame).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")

    raw_video = args.output_dir / f"{args.output_name}_raw.mp4"
    final_video = args.output_dir / f"{args.output_name}.mp4"

    run_checked([
        args.ffmpeg, "-y",
        "-r", str(args.fps),
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(raw_video),
    ])

    if args.exact_duration is None:
        os.replace(raw_video, final_video)
        return final_video

    # setpts scales presentation timestamps. A factor >1 slows the video down.
    nominal_duration = frame_count / args.fps
    factor = args.exact_duration / nominal_duration
    run_checked([
        args.ffmpeg, "-y",
        "-i", str(raw_video),
        "-vf", f"setpts={factor:.12f}*PTS",
        "-an",
        str(final_video),
    ])
    raw_video.unlink(missing_ok=True)
    return final_video


def probe_duration(ffprobe: str, video: Path) -> float:
    """Read the container duration with ffprobe."""
    result = subprocess.run(
        [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nokey=1:noprint_wrappers=1",
            str(video),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return float(result.stdout.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate timestamped ts_plot frames and an MP4 animation."
    )
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Directory containing EA_*, MA_*, ME_*, e3_*, etc.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--measurement", choices=["d", "v"], required=True,
                        help="d=density, v=velocity")
    parser.add_argument("--instrument", required=True,
                        help="ts_plot instrument, e.g. wind, mars, mercury")
    parser.add_argument("--tomography", default="ips")
    parser.add_argument("--forecast", required=True, help="YYYYMMDDHH")
    parser.add_argument("--plot-range", required=True,
                        help="YYYYMMDDHH_YYYYMMDDHH passed unchanged to ts_plot -tr")
    parser.add_argument("--start", type=parse_timestamp, required=True)
    parser.add_argument("--end", type=parse_timestamp, required=True)
    parser.add_argument("--cadence-hours", type=int, required=True)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--exact-duration", type=float,
                        help="Retimes output to exactly this many seconds")
    parser.add_argument("--delta-days", type=float,
                        help="Pass -dt to ts_plot; commonly 0.45 for density")
    parser.add_argument("--ymax", type=float,
                        help="Pass -ymax to ts_plot; commonly 20 for density")
    parser.add_argument("--ts-plot", default="ts_plot")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--keep-existing", action="store_true",
                        help="Skip frames that already exist instead of rebuilding them")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.data_dir = args.data_dir.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.frames_dir = args.output_dir / f"ts_images_{args.instrument}_{args.measurement}"

    if not args.data_dir.is_dir():
        raise SystemExit(f"Data directory does not exist: {args.data_dir}")
    for executable in (args.ts_plot, args.ffmpeg, args.ffprobe):
        if shutil.which(executable) is None:
            raise SystemExit(f"Required executable not found in PATH: {executable}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.frames_dir.mkdir(parents=True, exist_ok=True)

    times = list(timestamp_range(args.start, args.end, args.cadence_hours))
    print(f"Generating {len(times)} frames from {args.start} through {args.end}.")

    for index, current in enumerate(times, start=1):
        frame_name = current.strftime("%Y%m%d%H.png")
        destination = args.frames_dir / frame_name
        if args.keep_existing and destination.exists():
            print(f"[{index}/{len(times)}] keeping existing {frame_name}")
            continue

        print(f"[{index}/{len(times)}] TS_PLOT {current:%Y%m%d%H}")
        before = file_snapshot(args.frames_dir)
        command = build_ts_plot_command(args, current)
        run_checked(command)

        source = find_new_or_changed_file(args.frames_dir, before, destination)
        print(f"  frame source: {source.name} -> {destination.name}")
        convert_to_png(source, destination)

        # Remove non-frame temporary files created by the same ts_plot call.
        for item in args.frames_dir.iterdir():
            if item.is_file() and item != destination and item.suffix.lower() != ".png":
                item.unlink(missing_ok=True)

    actual_frames = sorted(args.frames_dir.glob("*.png"))
    if len(actual_frames) != len(times):
        raise RuntimeError(
            f"Expected {len(times)} PNG frames but found {len(actual_frames)} in {args.frames_dir}"
        )

    video = encode_video(args, len(actual_frames))
    duration = probe_duration(args.ffprobe, video)

    print("\nCOMPLETE")
    print(f"First frame: {actual_frames[0].name}")
    print(f"Last frame:  {actual_frames[-1].name}")
    print(f"Frame count: {len(actual_frames)}")
    print(f"Video:       {video}")
    print(f"Duration:    {duration:.6f} seconds")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
