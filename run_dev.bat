@echo off
chcp 65001 >nul
title FF14 个人主页 - 开发服务器

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║   最终幻想14 个人主页 — 开发服务器   ║
echo  ╚═══════════════════════════════════════╝
echo.
echo  正在启动，请稍候 ...
echo  按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"

:: 尝试多个 Python 路径
set PYTHON=
if exist "C:\Users\10426\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON=C:\Users\10426\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
) else if exist "C:\Python312\python.exe" (
    set PYTHON=C:\Python312\python.exe
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 set PYTHON=python
)

if "%PYTHON%"=="" (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo Python: %PYTHON%

:: 安装依赖（如果需要）
"%PYTHON%" -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo 安装依赖中 ...
    "%PYTHON%" -m pip install flask flask-login python-dotenv Pillow -q
)

:: 启动
echo 启动服务器: http://127.0.0.1:5000
echo.
"%PYTHON%" app.py

pause
