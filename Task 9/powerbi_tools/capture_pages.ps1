# Switches the open Power BI report to each page (UI Automation, by tab name) and saves a window capture per page.
# Crop the captures to the report canvas afterwards (see README in this folder).
# Usage: powershell -File capture_pages.ps1 -Title Customer_Dashboard -Pages "Overview","Ratings" -OutDir C:\temp
param([Parameter(Mandatory = $true)][string]$Title, [Parameter(Mandatory = $true)][string[]]$Pages, [string]$OutDir = $PSScriptRoot)
. "$PSScriptRoot\win.ps1"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$pids = [uint32[]](Get-Process | Where-Object { $_.ProcessName -match 'PBIDesktop' } | ForEach-Object { $_.Id })
$w = [W]::Titles($pids) | Where-Object { $_.Split('|', 2)[1] -eq $Title } | Select-Object -First 1
if (-not $w) { "window '$Title' not found"; exit 1 }
$h = [IntPtr][long]$w.Split('|')[0]
[W]::SetWindowPos($h, [IntPtr]::Zero, 0, 0, 1920, 1080, 0x14) | Out-Null
Start-Sleep -Seconds 1
$root = [System.Windows.Automation.AutomationElement]::FromHandle($h)
$i = 1
foreach ($n in $Pages) {
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $n)
  $el = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
  if ($el -eq $null) { "tab not found: $n"; continue }
  $pats = $el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }
  if ($pats -match 'SelectionItem') { $el.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
  elseif ($pats -match 'Invoke') { $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
  Start-Sleep -Seconds 4
  [W]::Shot($h, (Join-Path $OutDir "page_$i.png")); "saved page_$i ($n)"
  $i++
}
