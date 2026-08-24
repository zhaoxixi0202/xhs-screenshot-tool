@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.12，并勾选 Add python.exe to PATH。
  pause
  exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo 依赖安装完成。现在可以双击 启动截图工具.bat。
pause
