#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import hashlib
import subprocess
import socket
import psutil
from pathlib import Path
from dotenv import load_dotenv
from shared_utils import stdlog, errlog

# Import capture function from libcapture
# Note: libcapture.capture_victim is a sync wrapper around an async function
from libcapture import capture_victim

# -------------------- ENV LOADING --------------------
script_dir = Path(__file__).resolve().parent
home = script_dir.parent
env_path = home / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
TOR_PWD = os.getenv("TOR_PASSWORD")
TOR_AUTO_MANAGE = os.getenv("TOR_AUTO_MANAGE", "false").strip().lower() == "true"
TOR_BINARY_PATH = os.getenv("TOR_BINARY_PATH", "tor")
TOR_TORRC_PATH = os.getenv("TOR_TORRC_PATH")
proxy_address = os.getenv("TOR_PROXY_SERVER", "socks5://127.0.0.1:9050")

db_dir = Path(home / os.getenv("DB_DIR", "db").strip("/"))
img_dir = Path(home / os.getenv("IMAGES_DIR", "images").strip("/"))
victim_img_dir = img_dir / "victims"
lock_file_path = Path(home / os.getenv("TMP_DIR", "tmp").strip("/") / "capture.lock")

# -------------------- LOCKING --------------------
def is_process_alive(pid):
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False

def acquire_lock():
    if lock_file_path.exists():
        try:
            with open(lock_file_path, "r") as f:
                content = f.read()
                if "PID" in content:
                    old_pid = int(content.strip().split(":")[1])
                    if is_process_alive(old_pid):
                        errlog(f"Script already running with PID {old_pid}. Exiting.")
                        sys.exit(1)
                    else:
                        stdlog(f"Stale lock file found (PID {old_pid} not running). Overwriting.")
        except Exception as e:
            errlog(f"Error reading existing lock file: {e}")

    lock_file = open(lock_file_path, "w")
    try:
        # On Windows, we don't have fcntl, so we rely on PID check above
        lock_file.write(f"PID: {os.getpid()}\n")
        lock_file.flush()
        return lock_file
    except Exception:
        errlog("Could not create lock file.")
        sys.exit(1)

def release_lock(lock_file):
    lock_file.close()
    if lock_file_path.exists():
        lock_file_path.unlink()

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
            max_retries = 60
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

# -------------------- MAIN LOGIC --------------------

def get_url_md5(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def main():
    start_time = time.time()
    victims_file = db_dir / "victims.json"
    
    if not victims_file.exists():
        errlog(f"File not found: {victims_file}")
        return

    with open(victims_file, 'r', encoding='utf-8') as f:
        victims = json.load(f)

    # Filter victims that have a URL and don't have a screenshot yet
    targets = []
    for v in victims:
        url = v.get('post_url')
        if url and url.startswith('http'):
            md5 = get_url_md5(url)
            screenshot_path = victim_img_dir / f"{md5}.png"
            if not screenshot_path.exists():
                targets.append(v)

    if not targets:
        stdlog("No new screenshots to capture.")
        return

    stdlog(f"Found {len(targets)} victims needing screenshots.")

    lock_file = acquire_lock()

    try:
        if TOR_AUTO_MANAGE:
            start_managed_tor()
        
        for i, v in enumerate(targets, start=1):
            victim_name = v.get('post_title', 'Unknown')
            url = v.get('post_url')
            stdlog(f"[{i}/{len(targets)}] Capturing: {victim_name} ({url})")
            
            try:
                # capture_victim handles the browser lifecycle internally
                capture_victim(url)
                # Success - wait a bit to be gentle on Tor
                time.sleep(2)
            except Exception as e:
                errlog(f"Failed to capture {victim_name}: {str(e).splitlines()[0]}")
                # Wait longer on failure
                time.sleep(5)

    finally:
        if TOR_AUTO_MANAGE:
            stop_managed_tor()
        
        if lock_file:
            release_lock(lock_file)
        
        end_time = time.time()
        stdlog(f"Mass capture finished. Runtime: {(end_time - start_time)/60:.2f} minutes.")

if __name__ == "__main__":
    main()
