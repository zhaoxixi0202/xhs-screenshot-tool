param(
  [string]$Name = "小红书笔记截图工具"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectDir

$AppDir = Join-Path $ProjectDir "dist\$Name"
$MainExe = Join-Path $AppDir "$Name.exe"
if (-not (Test-Path $MainExe)) {
  throw "没有找到 Windows 程序：$MainExe。请先运行 packaging\build_windows_exe.ps1"
}

$IconPath = Join-Path $ProjectDir "assets\app_icon.ico"
$InstallerDir = Join-Path $ProjectDir "dist\installer"
New-Item -ItemType Directory -Force -Path $InstallerDir | Out-Null

$IssPath = Join-Path $InstallerDir "xhs-screenshot-tool.iss"
$OutputBase = "${Name}_Windows安装包"
$EscapedAppDir = $AppDir.Replace("\", "\\")
$EscapedIconPath = $IconPath.Replace("\", "\\")

@"
[Setup]
AppId={{8DE3A0E4-B97B-4A8F-BD69-1B3D45F71F25}
AppName=$Name
AppVersion=1.0.0
AppPublisher=小红书笔记截图工具
DefaultDirName={autopf}\$Name
DefaultGroupName=$Name
DisableProgramGroupPage=yes
OutputDir=$InstallerDir
OutputBaseFilename=$OutputBase
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=$EscapedIconPath
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："; Flags: unchecked

[Files]
Source: "$EscapedAppDir\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\$Name"; Filename: "{app}\$Name.exe"
Name: "{autodesktop}\$Name"; Filename: "{app}\$Name.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\$Name.exe"; Description: "启动 $Name"; Flags: nowait postinstall skipifsilent
"@ | Set-Content -Encoding UTF8 $IssPath

$Iscc = (Get-Command "iscc" -ErrorAction SilentlyContinue)
if (-not $Iscc) {
  $Candidate = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
  if (Test-Path $Candidate) {
    $Iscc = @{ Source = $Candidate }
  }
}
if (-not $Iscc) {
  throw "没有找到 Inno Setup 编译器 iscc。请先安装 Inno Setup 6，或在 GitHub Actions 里用 choco install innosetup。"
}

& $Iscc.Source $IssPath

$InstallerPath = Join-Path $InstallerDir "$OutputBase.exe"
if (-not (Test-Path $InstallerPath)) {
  throw "安装包生成失败：$InstallerPath"
}

Write-Host "已生成 Windows 安装包：$InstallerPath"
