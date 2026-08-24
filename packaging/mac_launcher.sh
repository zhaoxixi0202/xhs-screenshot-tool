#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL_ROOT="$APP_ROOT/Resources/xhs_screenshot_tool"

PYTHON_BIN="/Users/zhaoxixi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
NODE_BIN="/Users/zhaoxixi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [ -x "$NODE_BIN" ]; then
  export NODE_PATH="$NODE_BIN"
fi

export HOST="127.0.0.1"
export PORT="${PORT:-8788}"
export HEADLESS="false"

cd "$TOOL_ROOT"
open "http://127.0.0.1:${PORT}/" >/dev/null 2>&1 || true
exec "$PYTHON_BIN" app.py
