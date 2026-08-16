#!/usr/bin/env python3
"""Run the daily maintenance pipeline independently of the invoking terminal.

Use ``start`` to detach the pipeline, ``status`` to inspect its recorded state,
and ``log`` to read its output.  The child process records success or failure
in ``tmp/maintenance-pipeline.json`` so an automation can safely poll it after
the chat or terminal that started it has ended.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = ROOT / os.getenv("TMP_DIR", "tmp").strip("/")
STATE_PATH = TMP_DIR / "maintenance-pipeline.json"
LOG_PATH = TMP_DIR / "maintenance-pipeline.log"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_state(**values: Any) -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    state = read_state()
    state.update(values)
    temporary = STATE_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def is_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def command_list(force: bool) -> list[list[str]]:
    scrape_command = [sys.executable, "bin/scrape.py"]
    if force:
        scrape_command.append("--force")
    return [
        [sys.executable, ".bin/batch_add_groups.py"],
        scrape_command,
        [sys.executable, "bin/parse.py", "--force"],
    ]


def run(force: bool) -> int:
    write_state(
        pid=os.getpid(),
        status="running",
        started_at=utc_now(),
        finished_at=None,
        failed_command=None,
        return_code=None,
    )
    for command in command_list(force):
        write_state(current_command=command)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            write_state(
                status="failed",
                finished_at=utc_now(),
                failed_command=command,
                return_code=result.returncode,
                current_command=None,
            )
            return result.returncode

    write_state(
        status="succeeded",
        finished_at=utc_now(),
        return_code=0,
        current_command=None,
    )
    return 0


def start(force: bool) -> int:
    state = read_state()
    if is_alive(state.get("pid")) and state.get("status") in {"starting", "running"}:
        print(f"Maintenance pipeline is already running (PID {state['pid']}).")
        return 1

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "_run", *( ["--force"] if force else [] )],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    write_state(
        pid=process.pid,
        status="starting",
        started_at=utc_now(),
        finished_at=None,
        failed_command=None,
        return_code=None,
        current_command=None,
        log_path=str(LOG_PATH),
    )
    print(f"Started maintenance pipeline in background (PID {process.pid}).")
    print(f"State: {STATE_PATH}")
    print(f"Log: {LOG_PATH}")
    return 0


def status() -> int:
    state = read_state()
    if not state:
        print("No maintenance pipeline state has been recorded.")
        return 1
    if state.get("status") in {"starting", "running"} and not is_alive(state.get("pid")):
        state["status"] = "interrupted"
        state["finished_at"] = utc_now()
        write_state(**state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def log(lines: int) -> int:
    if not LOG_PATH.exists():
        print("No maintenance pipeline log has been recorded.")
        return 1
    entries = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\n".join(entries[-lines:]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("start", "_run"):
        subparser = subparsers.add_parser(action)
        subparser.add_argument("--force", action="store_true", help="clear a stale scrape lock before scraping")
    subparsers.add_parser("status")
    log_parser = subparsers.add_parser("log")
    log_parser.add_argument("--lines", type=int, default=80)
    args = parser.parse_args()

    if args.action == "start":
        return start(args.force)
    if args.action == "_run":
        return run(args.force)
    if args.action == "status":
        return status()
    return log(max(args.lines, 1))


if __name__ == "__main__":
    raise SystemExit(main())
