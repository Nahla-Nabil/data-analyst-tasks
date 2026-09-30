# Opens a generated .pbip in Power BI Desktop (Store app), waits for it to load, presses "Refresh now" via UI Automation
# and reports any error dialog (captured as a PNG next to this script). Does not touch the mouse or keyboard.
# Usage: powershell -File open_refresh.ps1 -Pbip "C:\...\PowerBI\Customer_Dashboard.pbip"
param([Parameter(Mandatory = $true)][string]$Pbip)
. "$PSScriptRoot\win.ps1"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$name = [System.IO.Path]::GetFileNameWithoutExtension($Pbip)
Start-Process "$env:LOCALAPPDATA\Microsoft\WindowsApps\PBIDesktopStore.exe" -ArgumentList "`"$Pbip`""
$h = [IntPtr]::Zero; $seen = @{}; $pids = @()
for ($i = 0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 1
  $pids = [uint32[]](Get-Process | Where-Object { $_.ProcessName -match 'PBIDesktop' } | ForEach-Object { $_.Id })
  if ($pids.Count -eq 0) { continue }
  foreach ($t in [W]::Titles($pids)) {
    $title = $t.Split('|', 2)[1]
    if (-not $seen.ContainsKey($title)) { $seen[$title] = $i; "$i s: window '$title'" }
    # load errors appear as dialogs that close themselves within seconds, so poll every second and capture them
    if ($title -match 'Issues|rror|wrong|Unable') { [W]::Shot([IntPtr][long]$t.Split('|')[0], "$PSScriptRoot\issue_$i.png"); "captured issue dialog at $i s" }
    if ($title -eq $name) { $h = [IntPtr][long]$t.Split('|')[0] }
  }
  if ($h -ne [IntPtr]::Zero -and $i -gt ($seen[$name] + 8)) { break }
}
if ($h -eq [IntPtr]::Zero) { "report window not found"; exit 1 }
[W]::SetWindowPos($h, [IntPtr]::Zero, 0, 0, 1920, 1080, 0x14) | Out-Null     # NOZORDER | NOACTIVATE
Start-Sleep -Seconds 2
$root = $AE::FromHandle($h)
$btns = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, "Refresh now")))
"Refresh now buttons: $($btns.Count)"
if ($btns.Count -gt 0) { $btns[$btns.Count - 1].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  foreach ($t in [W]::Titles($pids)) {
    $title = $t.Split('|', 2)[1]
    if ($title -match 'Issues|rror|wrong|Unable') { [W]::Shot([IntPtr][long]$t.Split('|')[0], "$PSScriptRoot\refresh_issue_$i.png"); "refresh dialog '$title' at $i s" }
  }
}
"refresh done"
