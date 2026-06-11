#!/usr/bin/env python3
"""
Ransomware.live GUI launcher
Usage: python gui.py [--port 8080] [--no-browser]
"""
import argparse
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

from aiohttp import web
from gui.app import create_app, PORT as DEFAULT_PORT


def _find_free_port(start: int, attempts: int = 10) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return -1


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    parser = argparse.ArgumentParser(description="Ransomware.live GUI")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open browser automatically")
    parser.add_argument("--no-fallback", action="store_true",
                        help="Fail immediately if port is busy instead of trying the next one")
    args = parser.parse_args()

    port = args.port

    if _port_in_use(port):
        if args.no_fallback:
            print(f"\n  [ERROR] Port {port} is already in use.")
            print(f"  Try:  ./start-gui.sh --port 8081")
            print(f"  Or kill the existing process:  lsof -ti tcp:{port} | xargs kill\n")
            sys.exit(1)

        fallback = _find_free_port(port + 1)
        if fallback == -1:
            print(f"\n  [ERROR] Port {port} is busy and no free port found in "
                  f"{port+1}–{port+10}.")
            print(f"  Kill the existing process:  lsof -ti tcp:{port} | xargs kill\n")
            sys.exit(1)

        print(f"\n  [WARN] Port {port} is already in use — switching to port {fallback}.")
        port = fallback

    app = create_app()
    url = f"http://localhost:{port}"
    print(f"\n  ransomware.live GUI  →  {url}\n  Press Ctrl+C to stop.\n")

    if not args.no_browser:
        def _open():
            time.sleep(0.8)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    web.run_app(app, host="127.0.0.1", port=port, print=lambda _: None)


if __name__ == "__main__":
    main()
