#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import os
import argparse
import sys
if sys.platform != 'win32':
    import fcntl
import traceback
from pathlib import Path
from dotenv import dotenv_values
from shared_utils import stdlog, errlog, screenshot
import time
import threading
# For logging the time
import json
from datetime import datetime
import subprocess
import socket
import psutil


# Load environment variables from ../.env without overriding process env.
script_dir = Path(__file__).resolve().parent
home = script_dir.parent
env_path = home / ".env"
for key, value in dotenv_values(env_path).items():
    if value is not None:
        os.environ.setdefault(key, value)

# Paths from environment variables
TOR_PWD = os.getenv("TOR_PASSWORD")
TOR_AUTO_MANAGE = os.getenv("TOR_AUTO_MANAGE", "false").strip().lower() == "true"
TOR_BINARY_PATH = os.getenv("TOR_BINARY_PATH", "tor")
TOR_TORRC_PATH = os.getenv("TOR_TORRC_PATH")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

tmp_dir = home.joinpath(os.getenv("TMP_DIR").strip('/'))
lock_file_path = tmp_dir / "parse.lock"

execution_time_path = Path(tmp_dir) / "execution_times.json"

# -------------------- MANAGED TOR --------------------
managed_tor_process = None

def start_managed_tor():
    global managed_tor_process
    if TOR_AUTO_MANAGE:
        stdlog(f"Starting managed Tor process: {TOR_BINARY_PATH}")
        try:
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW

            socks_port = "9050"
            if ":" in proxy_address:
                socks_port = proxy_address.split(":")[-1]

            cmd = [TOR_BINARY_PATH]
            if TOR_TORRC_PATH:
                cmd.extend(["-f", TOR_TORRC_PATH])
            cmd.extend(["--ControlPort", "9051", "--SocksPort", socks_port])

            managed_tor_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )

            # Wait for Tor to initialize and bootstrap
            max_retries = 30
            for i in range(max_retries):
                if managed_tor_process.poll() is not None:
                    raise Exception(f"Tor process exited unexpectedly with code {managed_tor_process.poll()}")

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(('127.0.0.1', int(socks_port)))
                    if result == 0:
                        try:
                            with socket.create_connection(("127.0.0.1", 9051)) as s:
                                if TOR_PWD:
                                    s.sendall(f"AUTHENTICATE \"{TOR_PWD}\"\r\n".encode())
                                else:
                                    s.sendall(b"AUTHENTICATE\r\n")
                                s.recv(1024)

                                s.sendall(b"GETINFO status/bootstrap-phase\r\n")
                                response = s.recv(1024).decode()
                                if "PROGRESS=100" in response:
                                    stdlog(f"Tor is fully bootstrapped and ready on SOCKS port {socks_port}")
                                    return
                        except Exception:
                            pass

                if i % 5 == 0 and i > 0:
                    stdlog("Waiting for Tor to initialize...")
                time.sleep(1)

            raise Exception("Timeout waiting for Tor to initialize")

        except Exception as e:
            errlog(f"Failed to start managed Tor: {e}")
            if managed_tor_process:
                managed_tor_process.kill()
            sys.exit(1)

def stop_managed_tor():
    global managed_tor_process
    if managed_tor_process:
        stdlog("Stopping managed Tor process...")
        managed_tor_process.terminate()
        try:
            managed_tor_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            managed_tor_process.kill()
        managed_tor_process = None

def is_process_alive(pid):
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False

def acquire_lock():
    """
    Acquires a lock to prevent simultaneous script execution.
    Includes a check for stale lock files.
    """
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_file_path.exists():
        try:
            with open(lock_file_path, "r") as f:
                content = f.read()
                if "PID" in content:
                    # Content is "PID: <num>\n..."
                    old_pid_line = [line for line in content.splitlines() if line.startswith("PID")][0]
                    old_pid = int(old_pid_line.strip().split(":")[1])
                    if is_process_alive(old_pid):
                        errlog(f"Script already running with PID {old_pid}. Exiting.")
                        sys.exit(1)
                    else:
                        stdlog(f"Stale lock file found (PID {old_pid} not running). Overwriting.")
        except Exception as e:
            errlog(f"Error reading existing lock file: {e}")

    lock_file = open(lock_file_path, "w")
    try:
        if sys.platform != 'win32':
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(f"PID: {os.getpid()}\n")
        lock_file.flush()
        return lock_file
    except BlockingIOError:
        errlog("Another instance of the script is already running (fcntl lock).")
        sys.exit(1)

def release_lock(lock_file):
    """
    Releases the lock file.

    Args:
        lock_file (file): The lock file object.

    Returns:
        None
    """
    if sys.platform != 'win32':
        fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()

def remove_lock_file():
    """
    Removes the lock file if it exists.

    Returns:
        None
    """
    if lock_file_path.exists():
        lock_file_path.unlink()
        stdlog("Previous lock removed.")

def execute_main(file_path, execution_data, run_date):
    """
    Dynamically imports a Python file, executes its `main` function, and logs execution time.

    Args:
        file_path (str): Path to the Python script to execute.
        execution_data (dict): Dictionary storing execution times.
        run_date (str): Date of script execution (YYYY-MM-DD).
    """
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Update lock file with script details
        with open(lock_file_path, "w") as lock_file:
            lock_file.write(f"PID: {os.getpid()}\n")
            lock_file.write(f"SCRIPT: {module_name}\n")
            stdlog(f"Update lock file {lock_file_path} with module {module_name}")

        # Measure execution time
        start_time = time.time()

        # Load and execute the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "main") and callable(module.main):
            module.main()
        else:
            errlog(f"File {file_path} does not have a callable main() function.")

        end_time = time.time()
        execution_duration = round(end_time - start_time, 2)  # Time in seconds

        # Store execution time
        if run_date not in execution_data:
            execution_data[run_date] = {}

        execution_data[run_date][module_name] = execution_duration

    except Exception as e:
        errlog(f"Error executing {file_path}: {e}")

def main():
    """
    Parses arguments and executes `main` functions in ./parsers/ directory.
    Logs execution times in JSON.
    """
    print(
    r'''
       _______________                        |*\_/*|________
      |  ___________  |                      ||_/-\_|______  |
      | |           | |                      | |           | |
      | |   0   0   | |                      | |   0   0   | |
      | |     -     | |                      | |     -     | |
      | |   \___/   | |                      | |   \___/   | |
      | |___     ___| |                      | |___________| |
      |_____|\_/|_____|                      |_______________|
        _|__|/ \|_|_.............X.............._|________|_
       / ********** \                          / ********** \
     /  ************  \   ransomware.live     /  ************  \
    --------------------                    --------------------
    '''
    )
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Execute all main functions in ./parsers/ or a specific one.")
    parser.add_argument("-G", "--group", help="Specify the group (parser's filename without .py) to execute.", default=None)
    parser.add_argument("-F", "--force", help="Force remove previous lock and run the script", action="store_true")
    args = parser.parse_args()

    # Generate execution date (static for the entire run)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Handle lock mechanism
    lock_file = None
    if args.force:
        remove_lock_file()
    lock_file = acquire_lock()

    # Load previous execution times from JSON (if exists)
    if execution_time_path.exists():
        with open(execution_time_path, "r") as json_file:
            try:
                execution_data = json.load(json_file)
            except json.JSONDecodeError:
                execution_data = {}  # Reset if file is corrupted
    else:
        execution_data = {}

    try:
        if TOR_AUTO_MANAGE:
            start_managed_tor()

        parsers_dir = "bin/_parsers"
        if not os.path.isdir(parsers_dir):
            errlog(f"The directory {parsers_dir} does not exist.")
            return

        if args.group:
            # Execute only the specified group
            file_path = os.path.join(parsers_dir, f"{args.group}.py")
            if os.path.isfile(file_path):
                stdlog(f"Parsing {Path(file_path).stem}...")
                execute_main(file_path, execution_data, run_date)
            elif os.path.isfile(os.path.join(parsers_dir, f"{args.group}-api.py")):
                stdlog(f"Parsing {Path(file_path).stem} with API Parser...")
                execute_main(os.path.join(parsers_dir, f"{args.group}-api.py"), execution_data, run_date)
            else:
                errlog(f"No file named {args.group}.py found in {parsers_dir}.")
        else:
            # Get all .py files in the directory
            parsers = [
                file_name for file_name in sorted(os.listdir(parsers_dir))
                if file_name.endswith(".py") and os.path.isfile(os.path.join(parsers_dir, file_name))
            ]
            total_parsers = len(parsers)

            # Run each parser with counter
            for index, file_name in enumerate(parsers, start=1):
                stdlog(f"[{index}/{total_parsers}] Parsing {Path(file_name).stem}...")
                execute_main(os.path.join(parsers_dir, file_name), execution_data, run_date)

    finally:
        if TOR_AUTO_MANAGE:
            stop_managed_tor()

        # Save execution times to JSON file
        with open(execution_time_path, "w") as json_file:
            json.dump(execution_data, json_file, indent=4)

        if lock_file:
            release_lock(lock_file)
        remove_lock_file()
        end_time = time.time()
        runtime_minutes = (end_time - start_time) / 60
        stdlog(f"Script finished. Total runtime: {runtime_minutes:.2f} minutes.")

if __name__ == "__main__":
    main()
