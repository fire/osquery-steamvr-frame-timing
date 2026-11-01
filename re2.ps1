Stop-ScheduledTask 'xrwin-osquery-steamvr-frame-timing' -ErrorAction SilentlyContinue
Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force
Copy-Item "$env:USERPROFILE\svft\steamvr_frame_timing.py" C:\ProgramData\osquery-steamvr -Force
Start-ScheduledTask 'xrwin-osquery-steamvr-frame-timing'
Start-Sleep 10
"pythonw: " + (Get-Process pythonw -ErrorAction SilentlyContinue | % { "$($_.Id)/s$($_.SessionId)" })
