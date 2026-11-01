select new_frames_since_last_query as new_frames, compositor_fps, frametime_max_ms, app_pid from steamvr_frame_timing;
select new_frames_since_last_query as new_frames, compositor_fps from steamvr_frame_timing;
