param(
  [string]$Python = "python",
  [string]$Node = "node",
  [string]$Name = "小红书笔记截图工具"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectDir

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python -m pip install pyinstaller

$IconPath = Join-Path $ProjectDir "assets\app_icon.ico"
if (-not (Test-Path $IconPath)) {
  & $Python -c "from PIL import Image; Image.open('assets/app_icon_1024.png').save('assets/app_icon.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
}

$NodePath = (Get-Command $Node).Source

& $Python -m PyInstaller `
  --clean `
  --noconfirm `
  --windowed `
  --name $Name `
  --icon $IconPath `
  --add-data "static;static" `
  --add-data "cdp_screenshot.mjs;." `
  --add-data "sample_links.xlsx;." `
  --add-data "assets\app_icon.ico;." `
  --add-binary "$NodePath;node" `
  native_app.py

$OutDir = Join-Path $ProjectDir "dist\$Name"
if (-not (Test-Path $OutDir)) {
  throw "没有找到打包输出目录：$OutDir"
}

Write-Host "已生成 Windows 程序：$OutDir\$Name.exe"
