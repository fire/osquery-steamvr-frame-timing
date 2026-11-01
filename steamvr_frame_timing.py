"""osquery extension: a steamvr_frame_timing table, read from the SteamVR compositor through OpenVR.

The extension is its own OpenVR client (a background application). It reads the compositor's
frame-timing ring from outside the game: nothing is injected into or hooked in VRChat or any other
app. SteamVR must be running, and this process must run in the same Windows session as SteamVR
(session 0, where the osqueryd service lives, cannot reach it). One row per query:

  select * from steamvr_frame_timing;
"""
import statistics
import threading
import time

import osquery

SAMPLE_FRAMES = 90  # about one second of frames at 90 Hz; the ring holds the most recent frames

REPROJECTION_REASONS = 1 | 2  # VRCompositor_ReprojectionReason_Cpu | _Gpu

COLUMNS = [
    ("sampled_frames", osquery.INTEGER),
    ("new_frames_since_last_query", osquery.INTEGER),  # 0 means the ring is frozen: no app is rendering
    ("compositor_fps", "DOUBLE"),
    ("frametime_avg_ms", "DOUBLE"),
    ("frametime_max_ms", "DOUBLE"),
    ("frametime_spread", "DOUBLE"),  # std dev over mean: the cs of the 144 Hz budget rule
    ("dropped_frames", osquery.INTEGER),
    ("reprojected_frames", osquery.INTEGER),
    ("total_render_gpu_ms_avg", "DOUBLE"),
    ("total_render_gpu_ms_max", "DOUBLE"),
    ("compositor_render_cpu_ms_avg", "DOUBLE"),
    ("submit_frame_ms_avg", "DOUBLE"),
    ("transfer_latency_ms", "DOUBLE"),
    ("app_pid", osquery.INTEGER),
    ("app_presents_total", osquery.INTEGER),
    ("app_dropped_total", osquery.INTEGER),
    ("app_reprojected_total", osquery.INTEGER),
]


def summarise(frames, cumulative=None):
    """frames: newest-first list of dicts with the Compositor_FrameTiming fields (m_*).
    cumulative: dict of Compositor_CumulativeStats fields, or None. Returns a str-valued row."""
    if len(frames) < 2:
        return {}
    ordered = sorted(frames, key=lambda f: f["m_nFrameIndex"])
    times = [f["m_flSystemTimeInSeconds"] for f in ordered]
    gaps = [(b - a) * 1000.0 for a, b in zip(times, times[1:]) if b > a]
    span = times[-1] - times[0]
    row = {"sampled_frames": str(len(ordered))}
    if gaps and span > 0:
        mean = statistics.fmean(gaps)
        row.update({
            "compositor_fps": f"{(len(ordered) - 1) / span:.2f}",
            "frametime_avg_ms": f"{mean:.3f}",
            "frametime_max_ms": f"{max(gaps):.3f}",
            "frametime_spread": f"{statistics.pstdev(gaps) / mean:.4f}",
        })
    gpu = [f["m_flTotalRenderGpuMs"] for f in ordered]
    row.update({
        "dropped_frames": str(sum(f["m_nNumDroppedFrames"] for f in ordered)),
        "reprojected_frames": str(sum(1 for f in ordered if f["m_nReprojectionFlags"] & REPROJECTION_REASONS)),
        "total_render_gpu_ms_avg": f"{statistics.fmean(gpu):.3f}",
        "total_render_gpu_ms_max": f"{max(gpu):.3f}",
        "compositor_render_cpu_ms_avg": f"{statistics.fmean(f['m_flCompositorRenderCpuMs'] for f in ordered):.3f}",
        "submit_frame_ms_avg": f"{statistics.fmean(f['m_flSubmitFrameMs'] for f in ordered):.3f}",
        "transfer_latency_ms": f"{ordered[-1]['m_flTransferLatencyMs']:.3f}",
    })
    if cumulative:
        row.update({
            "app_pid": str(cumulative["m_nPid"]),
            "app_presents_total": str(cumulative["m_nNumFramePresents"]),
            "app_dropped_total": str(cumulative["m_nNumDroppedFrames"]),
            "app_reprojected_total": str(cumulative["m_nNumReprojectedFrames"]),
        })
    return row


class Compositor:
    """One OpenVR background connection, opened lazily and reopened after SteamVR restarts."""

    def __init__(self):
        self._lock = threading.Lock()
        self._vr = None
        self._openvr = None
        self.last_index = None  # newest frame index at the previous query

    def _fields(self, struct):
        return {f[0]: getattr(struct, f[0]) for f in struct._fields_}

    def read(self):
        with self._lock:
            try:
                if self._vr is None:
                    import openvr
                    openvr.init(openvr.VRApplication_Background)
                    self._openvr = openvr
                    self._vr = openvr.VRCompositor()
                frames = []
                for ago in range(SAMPLE_FRAMES):
                    ok, timing = self._vr.getFrameTiming(ago)
                    if not ok:
                        break
                    frames.append(self._fields(timing))
                stats = self._vr.getCumulativeStats(
                    self._openvr.sizeof(self._openvr.Compositor_CumulativeStats))
                return frames, self._fields(stats)
            except Exception:
                self.close()
                raise

    def close(self):
        if self._openvr is not None:
            try:
                self._openvr.shutdown()
            except Exception:
                pass
        self._vr = None
        self._openvr = None


COMPOSITOR = Compositor()


@osquery.register_plugin
class SteamvrFrameTimingTable(osquery.TablePlugin):
    def name(self):
        return "steamvr_frame_timing"

    def columns(self):
        return [osquery.TableColumn(name=n, type=t) for n, t in COLUMNS]

    def generate(self, context):
        try:
            frames, stats = COMPOSITOR.read()
        except Exception:
            return []  # SteamVR not running, or not in this session: an empty table, not an error
        row = summarise(frames, stats)
        if not row:
            return []
        newest = max(f["m_nFrameIndex"] for f in frames)
        if COMPOSITOR.last_index is not None:
            row["new_frames_since_last_query"] = str(newest - COMPOSITOR.last_index)
        COMPOSITOR.last_index = newest
        return [row]


if __name__ == "__main__":
    # osqueryd restarts end start_extension; reconnect instead of exiting, so one logon task is enough.
    while True:
        try:
            osquery.start_extension(name="steamvr_frame_timing", version="0.1.0")
        except Exception:
            pass
        COMPOSITOR.close()
        time.sleep(5)
