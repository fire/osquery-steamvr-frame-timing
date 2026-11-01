Stop-ScheduledTask 'xrwin-osquery-steamvr-frame-timing' -ErrorAction SilentlyContinue
Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force
Copy-Item "$env:USERPROFILE\svft\steamvr_frame_timing.py" C:\ProgramData\osquery-steamvr -Force
Start-ScheduledTask 'xrwin-osquery-steamvr-frame-timing'
Start-Sleep 10
Restart-Service osqueryd
Start-Sleep 100
$n=(Get-Content 'C:\Program Files\osquery\log\osqueryd.snapshots.log' | Select-String '"name":"steamvr_frame_timing"')
"steamvr snapshots: $($n.Count)"
$n | Select -Last 1 | % { $_.Line.Substring(0,[Math]::Min(800,$_.Line.Length)) }
Get-Process pythonw -ErrorAction SilentlyContinue | % { "pythonw pid $($_.Id) session $($_.SessionId)" }
