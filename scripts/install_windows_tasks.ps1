[CmdletBinding()]
param(
    [string]$SiteRoot = "C:\inetpub\wwwroot\ffxiv_site",
    [string]$PythonExe = "C:\python\python.exe",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$scriptsDir = Join-Path $SiteRoot "scripts"
$deployScript = Join-Path $scriptsDir "deploy_windows.ps1"
$startScript = Join-Path $scriptsDir "start_windows.ps1"

foreach ($requiredPath in @($PythonExe, $deployScript, $startScript)) {
    if (-not (Test-Path $requiredPath)) { throw "Required path not found: $requiredPath" }
}

$powerShellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$deployCommand = "`"$powerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$deployScript`" -SiteRoot `"$SiteRoot`" -PythonExe `"$PythonExe`" -Port $Port"
$startCommand = "`"$powerShellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -SiteRoot `"$SiteRoot`" -PythonExe `"$PythonExe`" -Port $Port"

& schtasks.exe /Create /TN "FFXIV Site Auto Deploy" /SC MINUTE /MO 1 /TR $deployCommand /RU SYSTEM /RL HIGHEST /F
if ($LASTEXITCODE -ne 0) { throw "Failed to create deployment task" }

& schtasks.exe /Create /TN "FFXIV Site Startup" /SC ONSTART /DELAY 0000:30 /TR $startCommand /RU SYSTEM /RL HIGHEST /F
if ($LASTEXITCODE -ne 0) { throw "Failed to create startup task" }

& $PythonExe -m pip install -r (Join-Path $SiteRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies" }

& $startScript -SiteRoot $SiteRoot -PythonExe $PythonExe -Port $Port

Write-Output "Scheduled tasks installed:"
Write-Output "  FFXIV Site Auto Deploy (every minute)"
Write-Output "  FFXIV Site Startup (at system startup)"

