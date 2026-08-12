[CmdletBinding()]
param(
    [string]$SiteRoot = "C:\inetpub\wwwroot\ffxiv_site"
)

$ErrorActionPreference = "Stop"
$pidFile = Join-Path $SiteRoot ".deploy\site.pid"

if (-not (Test-Path $pidFile)) {
    Write-Output "Website PID file does not exist."
    exit 0
}

$savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
if ($savedPid -match '^\d+$') {
    $process = Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
        Write-Output "Website stopped (PID $savedPid)."
    }
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

