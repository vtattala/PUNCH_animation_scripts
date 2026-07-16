# PUNCH Time-Series Animation Scripts

These scripts reproduce the time-series animation workflow used for PUNCH/IPS products built from `EA_*`, `MA_*`, `ME_*`, or `e3_*` time-series files.

The recommended entry point is:

```bash
direct_timeseries_animator.py
```

It calls the existing `ts_plot` program once for every timestamp, detects the plot produced by `ts_plot`, saves timestamped PNG frames, builds an MP4 with `ffmpeg`, and can retime the result to an exact duration.

## 1. What must already be available

The scripts do **not** contain Ben Pieczynski's `ts_plot` or iAnimate software. Before using them, the machine must have:

- Linux shell access, such as Bitvise SSH
- Python 3
- `ts_plot` installed and available in `PATH`
- `ffmpeg` and `ffprobe`
- Pillow for the optional label-patching script
- ImageMagick only when a `ts_plot` installation outputs EPS/PS instead of PNG
- The raw time-series files, such as `EA_2304.000`, `MA_2304.000`, `ME_2304.000`, or `e3_2304.000`

The standalone animator does **not** require iAnimate. The iAnimate patch script is provided only for users who choose to continue using Ben's iAnimate mode-5 workflow.

## 2. Install public system dependencies

On Ubuntu/Debian, run:

```bash
sudo apt update
sudo apt install -y python3 python3-pip ffmpeg imagemagick fonts-dejavu-core
python3 -m pip install --user Pillow
```

Confirm the installations:

```bash
python3 --version
ffmpeg -version | head -1
ffprobe -version | head -1
python3 -c "from PIL import Image; print('Pillow OK')"
convert -version | head -1
```

If `sudo` is unavailable, ask the system administrator to install those packages. Pillow can usually still be installed for the current user with:

```bash
python3 -m pip install --user Pillow
```

## 3. Obtain and verify `ts_plot`

`ts_plot` is not a public package installed through `apt` or `pip`. Obtain the authorized installation from Ben Pieczynski, Dr. Bernard Jackson, or the relevant UCSD/IPS software administrator.

After it is installed, confirm that the shell can find it:

```bash
command -v ts_plot
ts_plot -il
```

The second command should list supported in-situ instruments such as:

```text
wind
mars
mercury
```

If `command -v ts_plot` prints nothing, add the directory containing `ts_plot` to `PATH`. For example:

```bash
export PATH="/path/to/ts_plot_directory:$PATH"
```

To make that permanent:

```bash
echo 'export PATH="/path/to/ts_plot_directory:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Replace `/path/to/ts_plot_directory` with the real installation directory.

## 4. Download these repository scripts

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_DIRECTORY>
```

Make the scripts executable:

```bash
chmod +x direct_timeseries_animator.py \
         patch_density_labels.py \
         patch_ianimate_plot_command.py \
         retime_exact.sh \
         verify_animation.sh
```

Replace `<REPOSITORY_URL>` and `<REPOSITORY_DIRECTORY>` with the actual GitHub repository URL and folder name.

## 5. Arrange the input data

Place the raw files together in one data directory. Examples:

```text
/path/to/data/EA_2304.000
/path/to/data/MA_2304.000
/path/to/data/ME_2304.000
```

or:

```text
/path/to/data/e3_2304.000
/path/to/data/EA_2304.000
```

The scripts never edit these raw files. They pass the directory to `ts_plot` using `-td` and write all generated files into a separate output directory.

## 6. Recommended workflow: standalone animator

### Earth/WIND density example

The following creates hourly frames from 2025-11-02 18 UT through 2025-11-30 01 UT, uses density smoothing `delt = 0.45`, sets the density y-axis maximum to 20, encodes at 4 fps, and retimes the result to exactly 164 seconds:

```bash
python3 direct_timeseries_animator.py \
  --data-dir /path/to/data \
  --output-dir /path/to/output/earth_density \
  --output-name november_hourly_earth_density \
  --measurement d \
  --instrument wind \
  --tomography ips \
  --forecast 2025113001 \
  --plot-range 2025110218_2025113001 \
  --start 2025110218 \
  --end 2025113001 \
  --cadence-hours 1 \
  --fps 4 \
  --exact-duration 164 \
  --delta-days 0.45 \
  --ymax 20
```

### Earth/WIND velocity example

Velocity normally keeps `ts_plot`'s default smoothing, so do not pass `--delta-days` unless a different value is specifically required:

```bash
python3 direct_timeseries_animator.py \
  --data-dir /path/to/data \
  --output-dir /path/to/output/earth_velocity \
  --output-name november_hourly_earth_velocity \
  --measurement v \
  --instrument wind \
  --tomography ips \
  --forecast 2025113001 \
  --plot-range 2025110218_2025113001 \
  --start 2025110218 \
  --end 2025113001 \
  --cadence-hours 1 \
  --fps 4 \
  --exact-duration 164
```

### Mars density

```bash
python3 direct_timeseries_animator.py \
  --data-dir /path/to/data \
  --output-dir /path/to/output/mars_density \
  --output-name november_hourly_mars_density \
  --measurement d \
  --instrument mars \
  --tomography ips \
  --forecast 2025113001 \
  --plot-range 2025110218_2025113001 \
  --start 2025110218 \
  --end 2025113001 \
  --cadence-hours 1 \
  --fps 4 \
  --exact-duration 164 \
  --delta-days 0.45 \
  --ymax 20
```

### Mercury density

```bash
python3 direct_timeseries_animator.py \
  --data-dir /path/to/data \
  --output-dir /path/to/output/mercury_density \
  --output-name november_hourly_mercury_density \
  --measurement d \
  --instrument mercury \
  --tomography ips \
  --forecast 2025113001 \
  --plot-range 2025110218_2025113001 \
  --start 2025110218 \
  --end 2025113001 \
  --cadence-hours 1 \
  --fps 4 \
  --exact-duration 164 \
  --delta-days 0.45 \
  --ymax 20
```

For Mars or Mercury velocity, use the corresponding instrument and `--measurement v`, and omit the density-only `--delta-days` and `--ymax` arguments.

## 7. Output structure

For an Earth density run, the output will look like:

```text
earth_density/
├── frames.txt
├── november_hourly_earth_density.mp4
└── ts_images_wind_d/
    ├── 2025110218.png
    ├── 2025110219.png
    ├── ...
    └── 2025113001.png
```

The standalone script uses the exact `--start` and `--end` timestamps. It does not use the time-offset workaround that was needed in one local iAnimate installation.

## 8. Optional PUNCH density label patch

Use this only when the generated density frames need the IPS label replaced with PUNCH. The default coordinates match the 1560×780 plots used in this workflow:

```bash
python3 patch_density_labels.py \
  /path/to/output/earth_density/ts_images_wind_d
```

This edits only the generated PNG frames. It does not edit raw data, curves, correlations, or numerical values.

After patching the PNGs, rerun the animator or rebuild the video from the patched frames. The simplest approach is to remove only the MP4 and rerun with `--keep-existing`:

```bash
rm -f /path/to/output/earth_density/november_hourly_earth_density.mp4

python3 direct_timeseries_animator.py \
  --data-dir /path/to/data \
  --output-dir /path/to/output/earth_density \
  --output-name november_hourly_earth_density \
  --measurement d \
  --instrument wind \
  --tomography ips \
  --forecast 2025113001 \
  --plot-range 2025110218_2025113001 \
  --start 2025110218 \
  --end 2025113001 \
  --cadence-hours 1 \
  --fps 4 \
  --exact-duration 164 \
  --delta-days 0.45 \
  --ymax 20 \
  --keep-existing
```

## 9. Verify a completed animation

```bash
./verify_animation.sh \
  /path/to/output/earth_density/ts_images_wind_d \
  /path/to/output/earth_density/november_hourly_earth_density.mp4
```

It reports:

- first PNG frame
- last PNG frame
- PNG frame count
- MP4 frame count
- MP4 duration

## 10. Retime an existing MP4

When an already-created MP4 needs an exact duration:

```bash
./retime_exact.sh input.mp4 output_EXACT.mp4 164
```

For a 53-second animation:

```bash
./retime_exact.sh input.mp4 output_EXACT_53sec.mp4 53
```

For a 36.5-second animation:

```bash
./retime_exact.sh input.mp4 output_EXACT_36p5sec.mp4 36.5
```

## 11. Optional iAnimate workflow

The standalone animator is recommended because it avoids local iAnimate timestamp-offset and filename assumptions.

To use Ben's iAnimate instead, first obtain an authorized iAnimate installation from the lab. Copy it before patching:

```bash
cp -a /usr/lib/iAnimate "$HOME/iAnimate_custom"
```

Patch the copied `plot_command.py`:

```bash
python3 patch_ianimate_plot_command.py \
  "$HOME/iAnimate_custom/plot_command.py" \
  --density-delta 0.45 \
  --density-ymax 20
```

This patch allows iAnimate to detect generated plot files regardless of whether their names begin with `e3`, `EA`, `MA`, or `ME`. It does not modify the raw scientific data.

## 12. Troubleshooting

### `Required executable not found in PATH: ts_plot`

Check:

```bash
command -v ts_plot
```

Then add its installation directory to `PATH`.

### `ts_plot finished but no new or updated output file was detected`

Run one direct diagnostic command to confirm `ts_plot` can read the data:

```bash
mkdir -p direct_test

ts_plot -d \
  -i wind \
  -f 2025113001 \
  -tr 2025110218_2025113001 \
  -t ips \
  -td /path/to/data \
  -od "$PWD/direct_test" \
  -ct 2025110218 \
  -dt 0.45 \
  -ymax 20

find direct_test -maxdepth 1 -type f -printf '%f\n'
```

### `ts_plot` outputs EPS or PS instead of PNG

Install ImageMagick:

```bash
sudo apt update
sudo apt install -y imagemagick
```

The standalone animator will then convert the generated output to PNG automatically.

### Resume an interrupted run

Rerun the same command with:

```bash
--keep-existing
```

Existing timestamped PNG frames will be preserved, and only missing frames will be generated.

## 13. Scientific settings

These scripts do not decide which scientific settings are correct for every dataset. Set them according to the dataset and guidance from the project lead.

Settings used in the established workflow included:

```text
Density comparison instrument: WIND
Density delta:                 0.45 days
Density y-axis maximum:        20
Velocity delta:                ts_plot default, generally 1.0 day
Tomography type:               ips
```

The raw `EA`, `MA`, `ME`, and `e3` files are read by `ts_plot`; none of these scripts rewrite their contents.
