# Runs DAX queries against the model of the report open in Power BI Desktop (its local Analysis Services instance).
# Usage: powershell -File dax_check.ps1 -Query "EVALUATE ROW(`"Customers`", [Customers])"   (several -Query values allowed)
param([Parameter(Mandatory = $true)][string[]]$Query)
$ms = Get-Process msmdsrv
# the msmdsrv.port.txt file was not where older guides say, so read the listening port of the msmdsrv process instead
$p = Get-NetTCPConnection -State Listen | Where-Object { $ms.Id -contains $_.OwningProcess } | Select-Object -ExpandProperty LocalPort -First 1
$pkg = Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop
Add-Type -Path (Join-Path $pkg.InstallLocation "bin\Microsoft.PowerBI.AdomdClient.dll")
$cn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$p")
$cn.Open()
$c0 = $cn.CreateCommand(); $c0.CommandText = "SELECT [CATALOG_NAME] FROM `$SYSTEM.DBSCHEMA_CATALOGS"
$r0 = $c0.ExecuteReader(); $r0.Read() | Out-Null; $db = $r0.GetValue(0); $r0.Close()
$cn.ChangeDatabase($db)
foreach ($dax in $Query) {
  $cmd = $cn.CreateCommand(); $cmd.CommandText = $dax
  try { $r = $cmd.ExecuteReader() } catch { "ERROR: $($_.Exception.Message)"; continue }
  while ($r.Read()) {
    $vals = @()
    for ($i = 0; $i -lt $r.FieldCount; $i++) { $v = $r.GetValue($i); if ($v -is [double]) { $v = [math]::Round($v, 4) }; $vals += "$($r.GetName($i) -replace '^.*\[|\]$', '')=$v" }
    ($vals -join "; ")
  }
  $r.Close()
}
$cn.Close()
