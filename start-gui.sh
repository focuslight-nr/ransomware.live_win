#!/usr/bin/env bash
# Ransomware.live GUI launcher (macOS / Linux)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x ".venv-py314/bin/python" ]; then
  PYTHON=".venv-py314/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PYTHON=".venv/bin/python3"
else
  PYTHON="python3"
fi

exec "$PYTHON" gui.py "$@"
