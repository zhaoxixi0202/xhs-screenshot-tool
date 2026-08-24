@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.12，并勾选 Add python.exe to PATH。
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo 未找到 Node.js。请先安装 Node.js 20 或更新版本。
  pause
  exit /b 1
)

set HOST=127.0.0.1
if "%PORT%"=="" set PORT=8788
set HEADLESS=false

start "" "http://127.0.0.1:%PORT%/"
python app.py
pause
