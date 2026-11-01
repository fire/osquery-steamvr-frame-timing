$f='C:\Program Files\osquery\osquery.conf'
$c=Get-Content $f -Raw | ConvertFrom-Json
$q=[pscustomobject]@{query='SELECT * FROM steamvr_frame_timing;';interval=60;snapshot=$true}
$c.schedule | Add-Member -NotePropertyName steamvr_frame_timing -NotePropertyValue $q -Force
[IO.File]::WriteAllText($f, ($c | ConvertTo-Json -Depth 6))
& 'C:\Program Files\osquery\osqueryi.exe' --config_path $f --config_check; "config_check exit $LASTEXITCODE"
Restart-Service osqueryd
Start-Sleep 5
# the user-session extension must reconnect after the daemon restart
Start-Sleep 80
$n=(Get-Content 'C:\Program Files\osquery\log\osqueryd.snapshots.log' | Select-String '"name":"steamvr_frame_timing"')
"steamvr snapshots: $($n.Count)"
$n | Select -Last 1 | % { $_.Line.Substring(0,[Math]::Min(700,$_.Line.Length)) }
Get-Process pythonw -ErrorAction SilentlyContinue | % { "pythonw pid $($_.Id)" }
