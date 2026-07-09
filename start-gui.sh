#!/usr/bin/env bash
# Ransomware.live GUI launcher (macOS / Linux)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON=".venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
  PYTHON="python3"
fi

exec "$PYTHON" gui.py "$@"
