# osquery-steamvr-frame-timing

An osquery extension that adds a `steamvr_frame_timing` table: the SteamVR compositor's frame rate,
frame time, dropped and reprojected frames, and GPU/CPU render time. It is the sibling of
[osquery-nvidia-gpu](https://github.com/fire/osquery-nvidia-gpu) and follows the same pattern: the
data lives in osquery, so a snapshot schedule logs it with no side files.

## How it reads

The extension is its own OpenVR client (a background application). It reads the compositor's
frame-timing ring through the OpenVR API, from outside the game. Nothing is injected into or hooked
in VRChat or any other app, which is the line VRChat draws for tools that load in via SteamVR
(https://hello.vrchat.com/blog/vrchat-security-update). Check that rule yourself before relying on it.

## Columns

sampled_frames, new_frames_since_last_query, compositor_fps, frametime_avg_ms, frametime_max_ms,
frametime_spread, dropped_frames, reprojected_frames, total_render_gpu_ms_avg,
total_render_gpu_ms_max, compositor_render_cpu_ms_avg, submit_frame_ms_avg, transfer_latency_ms,
app_pid, app_presents_total, app_dropped_total, app_reprojected_total.

- The window is the compositor's last 90 frames, about one second at 90 Hz.
- `frametime_spread` is the standard deviation over the mean of the frame gaps.
- `new_frames_since_last_query` is 0 when the ring is frozen. SteamVR keeps the last frames of the
  previous app after it exits, so every other column then reads stale. Check this column first.
- `app_*` are cumulative counters for the app the compositor last served, by `app_pid`.

## The session rule

OpenVR is reachable only from the Windows session SteamVR runs in. The osqueryd service runs in
session 0 and gets an init error. So run the extension in the desktop session, as a logon task that
connects to osqueryd's extension socket:

    pythonw steamvr_frame_timing.py --socket \\.\pipe\osquery.em --timeout 30 --interval 3

The script reconnects by itself when osqueryd restarts. Install `osquery` and `openvr` with
`pip install osquery openvr`. Then add a snapshot query to `osquery.conf`:

    "steamvr_frame_timing": {"query": "SELECT * FROM steamvr_frame_timing;", "interval": 60, "snapshot": true}

With SteamVR not running, the table is empty.

## Test

    python test_summarise.py

Checks the summary maths on synthetic frames, with a control that must fail. A live check on Windows
11 with SteamVR, osquery 5.24.0, osquery-python 3.1.1 and pyopenvr: `osqueryi --connect
\\.\pipe\osquery.em` returned one row.

## Licence

MIT. See [LICENSE](LICENSE).
