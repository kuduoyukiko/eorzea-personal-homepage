[CmdletBinding()]
param(
    [string]$SiteRoot = "C:\inetpub\wwwroot\ffxiv_site",
    [string]$PythonExe = "C:\python\python.exe",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$runtimeDir = Join-Path $SiteRoot ".deploy"
$pidFile = Join-Path $runtimeDir "site.pid"
$stdoutLog = Join-Path $runtimeDir "site.log"
$stderrLog = Join-Path $runtimeDir "site-error.log"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

if (Test-Path $pidFile) {
    $savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($savedPid -match '^\d+$' -and (Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue)) {
        Write-Output "Website is already running (PID $savedPid)."
        exit 0
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $PythonExe)) {
    throw "Python was not found at $PythonExe"
}

$arguments = @(
    "-m", "waitress",
    "--listen=0.0.0.0:$Port",
    "app:app"
)

$process = Start-Process -FilePath $PythonExe `
    -ArgumentList $arguments `
    -WorkingDirectory $SiteRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

$process.Id | Set-Content -Path $pidFile -Encoding Ascii
Start-Sleep -Seconds 3

if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
    throw "Website failed to start. Check $stderrLog"
}

Write-Output "Website started on port $Port (PID $($process.Id))."
