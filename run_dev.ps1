<#
.SYNOPSIS
    最终幻想14 个人主页 — 本地开发服务器启动脚本
.DESCRIPTION
    加载环境变量，安装依赖，启动 Flask 开发服务器
.PARAMETER Port
    监听端口 (默认 5000)
.PARAMETER Host
    监听地址 (默认 127.0.0.1)
.PARAMETER Debug
    是否启用调试模式 (默认 true)
.EXAMPLE
    .\run_dev.ps1                   # 启动在 localhost:5000
    .\run_dev.ps1 -Port 8080        # 启动在 localhost:8080
    .\run_dev.ps1 -Host 0.0.0.0     # 局域网可访问
#>

param(
    [int]$Port = 5000,
    [string]$Host = "127.0.0.1",
    [bool]$Debug = $true
)

# ---------- ANSI 颜色 ----------
$C   = "Cyan"
$G   = "Green"
$R   = "Red"
$Y   = "Yellow"

function W  { Write-Host "[$(Get-Date -Format HH:mm:ss)] $($args -join ' ')" }
function WI { Write-Host "[$(Get-Date -Format HH:mm:ss)]" -NoNewline; Write-Host " INFO" -ForegroundColor $C; Write-Host " $($args -join ' ')" }
function WO { Write-Host "[$(Get-Date -Format HH:mm:ss)]" -NoNewline; Write-Host "  OK" -ForegroundColor $G; Write-Host "  $($args -join ' ')" }
function WE { Write-Host "[$(Get-Date -Format HH:mm:ss)]" -NoNewline; Write-Host " ERR" -ForegroundColor $R; Write-Host "  $($args -join ' ')" }

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------- 1. 检查 Python ----------
$pythonCandidates = @(
    "C:\Users\10426\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    "python",
    "python3",
    "py -3"
)

$python = $null
foreach ($cmd in $pythonCandidates) {
    try {
        $v = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $v) {
            $python = $cmd
            WI "Python $v: $($cmd.Split('\')[-1])"
            break
        }
    } catch {}
}

if (-not $python) {
    WE "未找到 Python，请先安装 Python 3.10+"
    exit 1
}

# ---------- 2. 加载 .env ----------
$envFile = Join-Path $ROOT ".env"
if (Test-Path $envFile) {
    WI "加载环境变量: .env"
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim()
            # 处理引号
            if ($val -match '^["''](.*)["'']$') { $val = $matches[1] }
            # 处理注释
            $val = $val -replace '#.*$', ''
            $val = $val.Trim()
            if ($key -and $val) {
                [Environment]::SetEnvironmentVariable($key, $val, "Process")
            }
        }
    }
    WO "环境变量已加载"
} else {
    WW ".env 文件不存在，使用默认配置"
    $env:SECRET_KEY = "replace-this-local-development-key"
    $env:ADMIN_USERNAME = "admin"
    $env:ADMIN_PASSWORD = "replace-this-local-development-password"
}

# ---------- 3. 安装依赖 ----------
WI "检查 Python 依赖 ..."
$required = @("flask", "flask-login", "python-dotenv", "Pillow")
$missing = @()
foreach ($pkg in $required) {
    $pkgName = $pkg.ToLower()
    $check = & $python -c "import $pkgName" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    WI "安装缺失依赖: $($missing -join ', ')"
    foreach ($pkg in $missing) {
        $pkgMap = @{
            "flask" = "flask"
            "flask-login" = "flask-login"
            "python-dotenv" = "python-dotenv"
            "Pillow" = "Pillow"
        }
        $pipName = $pkgMap[$pkg]
        if (-not $pipName) { continue }
        WO "安装 $pipName ..."
        & $python -m pip install $pipName 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            WE "安装 $pipName 失败"
        }
    }
} else {
    WO "所有依赖已就绪"
}

# ---------- 4. 设置 Flask 环境 ----------
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = if ($Debug) { "development" } else { "production" }
$env:PYTHONUNBUFFERED = "1"

# ---------- 5. 确认目录 ----------
$dataDir = Join-Path $ROOT "data"
$uploadsDir = Join-Path $ROOT "static\uploads"
if (-not (Test-Path $dataDir))  { New-Item -Path $dataDir -ItemType Directory -Force | Out-Null }
if (-not (Test-Path $uploadsDir)) { New-Item -Path $uploadsDir -ItemType Directory -Force | Out-Null }

$imgCount = @(Get-ChildItem $uploadsDir -File | Where-Object { -not $_.Name.Contains('_thumb') }).Count
$thumbCount = @(Get-ChildItem $uploadsDir -Filter "*_thumb*" -File).Count

# ---------- 6. 启动 ----------
Write-Host @"

  ╔═══════════════════════════════════════╗
  ║   最终幻想14 个人主页 — 开发服务器   ║
  ╚═══════════════════════════════════════╝

  地址: http://$($Host):$Port
  调试模式: $Debug
  图片: $imgCount 原图 / $thumbCount 缩略图
  按 Ctrl+C 停止服务器

"@ -ForegroundColor $C

WI "启动 Flask 开发服务器 ..."

# 切换到项目目录
Push-Location $ROOT

try {
    & $python app.py
} catch {
    WE "启动失败: $_"
} finally {
    Pop-Location
}
