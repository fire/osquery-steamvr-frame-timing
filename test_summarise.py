"""Checks summarise() on synthetic frames, with a control that must fail."""
from steamvr_frame_timing import summarise


def frames(gaps_ms, dropped_at=(), reproject_at=()):
    t, out = 100.0, []
    for i, gap in enumerate([0.0] + list(gaps_ms)):
        t += gap / 1000.0
        out.append({"m_nFrameIndex": i, "m_flSystemTimeInSeconds": t,
                    "m_nNumDroppedFrames": 1 if i in dropped_at else 0,
                    "m_nReprojectionFlags": 2 if i in reproject_at else 0,
                    "m_flTotalRenderGpuMs": 5.0 + (i % 3), "m_flCompositorRenderCpuMs": 0.5,
                    "m_flSubmitFrameMs": 0.1, "m_flTransferLatencyMs": 1.8})
    return list(reversed(out))  # newest first, as the API returns them


# 91 frames at exactly 90 Hz: 90 gaps of 1000/90 ms
steady = summarise(frames([1000 / 90] * 90))
assert steady["compositor_fps"] == "90.00", steady
assert steady["frametime_spread"] == "0.0000", steady
assert steady["dropped_frames"] == "0" and steady["reprojected_frames"] == "0"

# one 22.2 ms gap = one missed 11.1 ms frame, flagged dropped and reprojected
hitch = summarise(frames([1000 / 90] * 44 + [2000 / 90] + [1000 / 90] * 45, dropped_at={45}, reproject_at={45, 46}))
assert hitch["dropped_frames"] == "1" and hitch["reprojected_frames"] == "2", hitch
assert float(hitch["frametime_max_ms"]) > 22.0 and float(hitch["frametime_spread"]) > 0.05, hitch
assert float(hitch["compositor_fps"]) < 90.0, hitch

# control: the steady row must NOT pass the hitch check, or the check proves nothing
assert not (steady["dropped_frames"] == "1" and float(steady["frametime_max_ms"]) > 22.0)
assert summarise([]) == {}
print("ok")
