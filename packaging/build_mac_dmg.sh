#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-$(command -v node || true)}"
DMG_PATH="${DMG_PATH:-$PROJECT_DIR/../小红书笔记截图工具_Mac可分发安装包.dmg}"

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  echo "找不到可用的 node。请先安装 Node.js 22+，或设置 NODE_BIN=/path/to/node"
  exit 1
fi

cd "$PROJECT_DIR"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --windowed \
  --name "小红书笔记截图工具" \
  --icon assets/app_icon.icns \
  --add-data static:static \
  --add-data cdp_screenshot.mjs:. \
  --add-data sample_links.xlsx:. \
  --add-data assets/app_icon.icns:. \
  --add-binary "$NODE_BIN":node \
  app.py

STAGE_DIR="$(mktemp -d /private/tmp/xhs-dmg.XXXXXX)"
cp -R "dist/小红书笔记截图工具.app" "$STAGE_DIR/"
ln -s /Applications "$STAGE_DIR/Applications"

hdiutil create \
  -volname "小红书笔记截图工具" \
  -srcfolder "$STAGE_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "已生成：$DMG_PATH"
