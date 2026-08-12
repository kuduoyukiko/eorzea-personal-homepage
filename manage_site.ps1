<#
.SYNOPSIS
    FF14 个人主页 — Python 进程管理脚本
.DESCRIPTION
    管理 Flask 应用的启动/停止/重启/状态/部署
    适用于直接用 python app.py 运行的方式
.PARAMETER Action
    操作: start | stop | restart | status | deploy | logs
.PARAMETER Port
    Flask 端口 (默认 5000)
.PARAMETER Source
    源代码目录 (默认当前目录)
.PARAMETER Target
    部署目标目录 (默认同 Source)
.EXAMPLE
    .\manage_site.ps1 status       # 查看运行状态
    .\manage_site.ps1 restart      # 重启
    .\manage_site.ps1 logs         # 查看最近20行日志
#>
param(
    [Parameter(Mandatory, Position=0)]
    [ValidateSet("start","stop","restart","status","deploy","logs")]
    [string]$Action,

    [int]$Port = 5000,
    [string]$Source = "",
    [string]$Target = ""
)

$C = "Cyan"; $G = "Green"; $R = "Red"; $Y = "Yellow"

if (-not $Source)  { $Source = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $Target)  { $Target = $Source }

$PID_FILE = Join-Path $Source "app.pid"
$LOG_FILE = Join-Path $Source "app.log"
$APP_PORT = $Port

# ========== 工具函数 ==========

function Find-Python {
    $candidates = @(
        "C:\Users\10426\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
        "python",
        "python3"
    )
    foreach ($cmd in $candidates) {
        try {
            $v = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $v) { return $cmd }
        } catch {}
    }
    return $null
}

function Get-SavedPid {
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE -Raw -ErrorAction SilentlyContinue
        if ($pid -match '\d+') { return [int]$Matches[0] }
    }
    return $null
}

function Test-ProcessAlive($pid) {
    if (-not $pid) { return $false }
    try { $p = Get-Process -Id $pid -ErrorAction Stop; return $true }
    catch { return $false }
}

function Find-ProcessByPort {
    try {
        $conn = Get-NetTCPConnection -LocalPort $APP_PORT -ErrorAction SilentlyContinue
        if ($conn) { return $conn.OwningProcess | Select-Object -First 1 }
    } catch {}
    return $null
}

function Write-Info  { Write-Host "  INFO " -ForegroundColor $C -NoNewline; Write-Host $($args -join ' ') }
function Write-Ok   { Write-Host "   OK  " -ForegroundColor $G -NoNewline; Write-Host $($args -join ' ') }
function Write-Err  { Write-Host "  ERR  " -ForegroundColor $R -NoNewline; Write-Host $($args -join ' ') }
function Write-Warn { Write-Host " WARN  " -ForegroundColor $Y -NoNewline; Write-Host $($args -join ' ') }

# ========== 核心操作 ==========

function Start-App {
    $python = Find-Python
    if (-not $python) { Write-Err "未找到 Python"; return }

    # 检查是否已在运行
    $pid = Get-SavedPid
    if ($pid -and (Test-ProcessAlive $pid)) {
        Write-Warn "应用已在运行 (PID: $pid)"
        return
    }
    
    # 清理旧的端口占用
    $oldPid = Find-ProcessByPort
    if ($oldPid) {
        Write-Info "清理端口 $APP_PORT 上的旧进程 (PID: $oldPid) ..."
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # 获取 Python 路径用于日志
    $pyPath = if ($python -eq "python") { (Get-Command python).Source } else { $python }
    Write-Info "Python: $pyPath"
    Write-Info "启动 Flask 在 http://0.0.0.0:$APP_PORT ..."

    # 启动进程 (无窗口后台运行)
    $process = Start-Process -FilePath $python -ArgumentList "app.py" `
        -WorkingDirectory $Source `
        -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $LOG_FILE `
        -RedirectStandardError "${LOG_FILE}.err"

    # 保存 PID
    $process.Id | Out-File -FilePath $PID_FILE -Encoding utf8
    Start-Sleep -Seconds 2

    # 验证
    if (Test-ProcessAlive $process.Id) {
        Write-Ok "应用已启动 (PID: $($process.Id))"
        Write-Info "访问地址: http://localhost:$APP_PORT"
    } else {
        Write-Err "应用启动失败，查看日志: $LOG_FILE"
        Get-Content $LOG_FILE -Tail 5 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor $R }
    }
}

function Stop-App {
    # 按 PID 文件停止
    $pid = Get-SavedPid
    if ($pid -and (Test-ProcessAlive $pid)) {
        Write-Info "停止进程 PID: $pid ..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        if (-not (Test-ProcessAlive $pid)) { Write-Ok "已停止" }
        else { Write-Err "停止失败" }
    } else {
        Write-Info "PID 文件无效，尝试按端口查找 ..."
        $portPid = Find-ProcessByPort
        if ($portPid) {
            Write-Info "停止端口 $APP_PORT 上的进程 PID: $portPid ..."
            Stop-Process -Id $portPid -Force -ErrorAction SilentlyContinue
            Write-Ok "已停止"
        } else {
            Write-Warn "没有运行中的应用"
        }
    }
    
    # 清理 PID 文件
    if (Test-Path $PID_FILE) { Remove-Item $PID_FILE -Force }
}

function Restart-App {
    Write-Info "正在重启 ..."
    Stop-App
    Start-Sleep -Seconds 2
    Start-App
}

function Get-Status {
    Write-Host "`n================================================" -ForegroundColor $C
    Write-Host "  FF14 个人主页 — 运行状态" -ForegroundColor $C
    Write-Host "================================================`n" -ForegroundColor $C

    Write-Info "站点目录: $Source"
    
    # 进程状态
    $pid = Get-SavedPid
    $alive = $pid -and (Test-ProcessAlive $pid)
    
    if ($alive) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
        $cpu = $proc.CPU
        $started = $proc.StartTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Ok "应用运行中"
        Write-Info "  PID:      $pid"
        Write-Info "  内存:     ${memMB} MB"
        Write-Info "  CPU:      ${cpu}s"
        Write-Info "  启动:     $started"
    } else {
        # 按端口查找
        $portPid = Find-ProcessByPort
        if ($portPid) {
            $proc = Get-Process -Id $portPid -ErrorAction SilentlyContinue
            Write-Warn "应用运行中但 PID 文件不匹配"
            Write-Info "  实际 PID: $portPid ($($proc.ProcessName))"
            Write-Info "  建议: 运行 restart 重新建立 PID 文件"
        } else {
            Write-Err "应用未运行"
        }
    }

    # 端口状态
    try {
        $listener = Get-NetTCPConnection -LocalPort $APP_PORT -ErrorAction SilentlyContinue | Where-Object State -eq Listen
        if ($listener) {
            Write-Ok "端口 $APP_PORT 正在监听"
        } else {
            Write-Warn "端口 $APP_PORT 无监听"
        }
    } catch {}

    # 日志大小
    if (Test-Path $LOG_FILE) {
        $logSize = [math]::Round((Get-Item $LOG_FILE).Length / 1KB, 1)
        $logLines = (Get-Content $LOG_FILE -ErrorAction SilentlyContinue).Count
        Write-Info "日志: ${logLines} 行 (${logSize} KB)"
    }

    # 图片统计
    $uploads = Join-Path $Target "static\uploads"
    if (Test-Path $uploads) {
        $imgs = @(Get-ChildItem $uploads -File | Where-Object { -not $_.Name.Contains('_thumb') }).Count
        $thumbs = @(Get-ChildItem $uploads -Filter "*_thumb*" -File).Count
        Write-Info "图片: $imgs 原图 / $thumbs 缩略图"
    }

    Write-Host "`n----------------------------------------------" -ForegroundColor $C
    Write-Host "  http://localhost:$APP_PORT" -ForegroundColor $G
    Write-Host "----------------------------------------------`n" -ForegroundColor $C
}

function Deploy-Site {
    Write-Info "部署: $Source → $Target"
    
    # 先停止
    Stop-App
    
    # 排除列表
    $exclude = @("__pycache__", "*.pyc", "*.log", "*.pid", "debug_*.txt")
    
    # 复制代码文件
    Write-Info "复制代码文件 ..."
    $items = @("app.py", "config.py", ".env", "web.config", "utils", "data", "templates")
    $count = 0
    foreach ($item in $items) {
        $src = Join-Path $Source $item
        $dst = Join-Path $Target $item
        if (Test-Path $src) {
            if ((Get-Item $src) -is [System.IO.DirectoryInfo]) {
                Copy-Item "$src\*" $dst -Recurse -Force -Exclude $exclude -ErrorAction SilentlyContinue
            } else {
                Copy-Item $src $dst -Force -ErrorAction SilentlyContinue
            }
            $count++
        }
    }
    
    # 复制图片
    Write-Info "复制图片文件 ..."
    $srcImg = Join-Path $Source "static\uploads"
    $dstImg = Join-Path $Target "static\uploads"
    if (Test-Path $srcImg) {
        if (-not (Test-Path $dstImg)) { New-Item $dstImg -ItemType Directory -Force | Out-Null }
        Copy-Item "$srcImg\*" $dstImg -Force -ErrorAction SilentlyContinue
        $imgCount = @(Get-ChildItem $dstImg -File).Count
        Write-Ok "  已复制 $imgCount 个文件"
    }
    
    Write-Ok "部署完成 ($count 项)"
    
    # 启动
    Start-App
}

function Show-Logs {
    $lines = 30
    if (-not (Test-Path $LOG_FILE)) { Write-Warn "日志文件不存在: $LOG_FILE"; return }
    
    Write-Host "`n====== 最近 $lines 行日志 ======" -ForegroundColor $C
    Get-Content $LOG_FILE -Tail $lines -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  $_" }
    Write-Host "================================`n" -ForegroundColor $C
    
    # 错误日志
    $errFile = "${LOG_FILE}.err"
    if (Test-Path $errFile) {
        $errLines = Get-Content $errFile -Tail 10 -ErrorAction SilentlyContinue
        if ($errLines) {
            Write-Host "====== 错误输出 ======" -ForegroundColor $R
            $errLines | ForEach-Object { Write-Host "  $_" -ForegroundColor $R }
            Write-Host "======================" -ForegroundColor $R
        }
    }
}

# ========== 主入口 ==========

Write-Host @"
 ╔══════════════════════════════════════╗
 ║  FF14 个人主页 - 进程管理            ║
 ╚══════════════════════════════════════╝
"@ -ForegroundColor $C

switch ($Action) {
    "start"   { Start-App }
    "stop"    { Stop-App }
    "restart" { Restart-App }
    "status"  { Get-Status }
    "deploy"  { Deploy-Site }
    "logs"    { Show-Logs }
}

Write-Host ""
