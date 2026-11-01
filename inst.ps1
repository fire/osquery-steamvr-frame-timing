$ErrorActionPreference='Stop'
$dir='C:\ProgramData\osquery-steamvr'
New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item "$env:USERPROFILE\svft\steamvr_frame_timing.py" $dir -Force
$pyw=(Get-Command pythonw).Source
$act=New-ScheduledTaskAction -Execute $pyw -Argument "`"$dir\steamvr_frame_timing.py`" --socket \\.\pipe\osquery.em --timeout 30 --interval 3"
$trg=New-ScheduledTaskTrigger -AtLogOn -User 'DESKTOP-CME56A7\ernest.lee'
$pri=New-ScheduledTaskPrincipal -UserId 'DESKTOP-CME56A7\ernest.lee' -LogonType Interactive -RunLevel Highest
$set=New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'xrwin-osquery-steamvr-frame-timing' -Action $act -Trigger $trg -Principal $pri -Settings $set -Force | Out-Null
Start-ScheduledTask -TaskName 'xrwin-osquery-steamvr-frame-timing'
Start-Sleep 12
Get-ScheduledTask 'xrwin-osquery-steamvr-frame-timing' | Get-ScheduledTaskInfo | % { "task last result: $($_.LastTaskResult)" }
Get-Process pythonw -ErrorAction SilentlyContinue | % { "pythonw pid $($_.Id) session $($_.SessionId)" }
