#!/usr/bin/env python3
"""Patch Ben Pieczynski's iAnimate ``plot_command.py`` safely.

The stock time-series helper assumes every ts_plot output begins with ``e3``.
New PUNCH datasets may instead produce EA, MA, or ME plot names. This patch:

- preserves the original ts_plot scientific command,
- keeps density-only ``-dt`` and ``-ymax`` options configurable,
- detects whichever file ts_plot just created or updated,
- renames that file to the requested timestamp frame,
- never edits the raw EA/MA/ME/e3 input files.

Always patch a COPY of iAnimate, not the system installation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plot_command", type=Path,
                        help="Path to the copied iAnimate plot_command.py")
    parser.add_argument("--density-delta", type=float, default=0.45)
    parser.add_argument("--density-ymax", type=float, default=20.0)
    args = parser.parse_args()

    path = args.plot_command.expanduser().resolve()
    original = path.read_text(encoding="utf-8")
    backup = path.with_suffix(path.suffix + ".before_punch_patch")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")

    replacement = f'''def run_ts_plot(mes, instrument, forecast_date, time_range,
                tomo, tomo_dir, out_dir, fname,
                cur_time) -> str:
    import glob
    import os
    import subprocess

    # Density-only settings used in this workflow. Velocity retains ts_plot's
    # default smoothing because delta_arg is empty when mes == "v".
    delta_arg = ' -dt {args.density_delta:g} -ymax {args.density_ymax:g}' if mes == 'd' else ''

    os.makedirs(out_dir, exist_ok=True)
    before = {{}}
    for item in glob.glob(os.path.join(out_dir, '*')):
        if os.path.isfile(item):
            before[item] = os.stat(item).st_mtime_ns

    command = f'ts_plot -{{mes}} -i "{{instrument}}" -f {{forecast_date}}'\\
              f' -tr {{time_range}} -t {{tomo}} -td {{tomo_dir}} -od {{out_dir}} -ct {{cur_time}}'\\
              f'{{delta_arg}}'
    print('running command:', command)
    subprocess.run(command, shell=True, check=True)

    destination = os.path.join(out_dir, fname)
    changed = []
    for item in glob.glob(os.path.join(out_dir, '*')):
        if not os.path.isfile(item):
            continue
        current_mtime = os.stat(item).st_mtime_ns
        if item not in before or before[item] != current_mtime:
            if os.path.abspath(item) != os.path.abspath(destination):
                changed.append(item)

    if not changed:
        print('Files present after ts_plot:')
        for item in sorted(glob.glob(os.path.join(out_dir, '*'))):
            print('   ', item)
        raise FileNotFoundError('ts_plot created no detectable frame output')

    source = max(changed, key=lambda item: os.stat(item).st_mtime_ns)
    print('renaming plot:', source, '->', destination)
    os.replace(source, destination)

    for item in changed:
        if item != source and os.path.exists(item):
            os.remove(item)

    return command
'''

    pattern = re.compile(
        r'^def run_ts_plot\(.*?(?=^def run_arc_ts_plot)',
        flags=re.DOTALL | re.MULTILINE,
    )
    if not pattern.search(original):
        raise SystemExit("Could not locate run_ts_plot in the supplied file")

    path.write_text(pattern.sub(replacement + "\n", original), encoding="utf-8")
    print(f"Patched: {path}")
    print(f"Backup:  {backup}")


if __name__ == "__main__":
    main()
