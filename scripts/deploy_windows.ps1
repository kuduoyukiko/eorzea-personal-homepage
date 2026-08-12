[CmdletBinding()]
param(
    [string]$SiteRoot = "C:\inetpub\wwwroot\ffxiv_site",
    [string]$PythonExe = "C:\python\python.exe",
    [string]$Branch = "main",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$runtimeDir = Join-Path $SiteRoot ".deploy"
$lockFile = Join-Path $runtimeDir "deploy.lock"
$deployLog = Join-Path $runtimeDir "deploy.log"
$scriptDir = Join-Path $SiteRoot "scripts"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

try {
    $lockStream = [System.IO.File]::Open($lockFile, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    exit 0
}

try {
    Set-Location $SiteRoot
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $deployLog "[$stamp] Checking origin/$Branch"

    & git fetch --quiet origin $Branch
    if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }

    $localCommit = (& git rev-parse HEAD).Trim()
    $remoteCommit = (& git rev-parse "origin/$Branch").Trim()

    if ($localCommit -eq $remoteCommit) {
        exit 0
    }

    Add-Content $deployLog "[$stamp] Deploying $localCommit -> $remoteCommit"
    & (Join-Path $scriptDir "stop_windows.ps1") -SiteRoot $SiteRoot

    & git merge --ff-only "origin/$Branch"
    if ($LASTEXITCODE -ne 0) { throw "git fast-forward failed" }

    & $PythonExe -m pip install --disable-pip-version-check --quiet -r (Join-Path $SiteRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "dependency installation failed" }

    & (Join-Path $scriptDir "start_windows.ps1") -SiteRoot $SiteRoot -PythonExe $PythonExe -Port $Port
    Add-Content $deployLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Deployment completed"
} catch {
    Add-Content $deployLog "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $($_.Exception.Message)"
    try {
        & (Join-Path $scriptDir "start_windows.ps1") -SiteRoot $SiteRoot -PythonExe $PythonExe -Port $Port
    } catch {}
    exit 1
} finally {
    if ($lockStream) { $lockStream.Dispose() }
}

