#!/usr/bin/env python3
"""Compatibility entry point for the real batch_add_groups script."""

from pathlib import Path
import os
import runpy
import sys


repo_root = Path(__file__).resolve().parents[1]
script = repo_root / "bin" / "batch_add_groups.py"

os.chdir(repo_root)
sys.argv[0] = str(script)
runpy.run_path(str(script), run_name="__main__")
