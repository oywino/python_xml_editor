#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import http
import http.server
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
import shlex
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - Windows-only helper
    winreg = None

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
HEARTBEAT_PATH = "/__heartbeat"
STARTUP_TIMEOUT_SECONDS = 45
HEARTBEAT_TIMEOUT_SECONDS = 12


def find_free_port(host: str = HOST) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


class AppServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.started_at = time.monotonic()
        self.last_activity_at = self.started_at
        self.seen_browser_client = False

    def note_browser_activity(self) -> None:
        self.last_activity_at = time.monotonic()
        self.seen_browser_client = True


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path != HEARTBEAT_PATH:
            self.server.note_browser_activity()
        super().do_GET()

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path != HEARTBEAT_PATH:
            self.send_error(http.HTTPStatus.NOT_FOUND)
            return

        self.server.note_browser_activity()
        self.send_response(http.HTTPStatus.NO_CONTENT)
        self.end_headers()


def monitor_browser_activity(server: AppServer) -> None:
    while True:
        time.sleep(1)
        now = time.monotonic()

        if server.seen_browser_client:
            if now - server.last_activity_at > HEARTBEAT_TIMEOUT_SECONDS:
                print("Browser window closed. Stopping server.")
                server.shutdown()
                return
        elif now - server.started_at > STARTUP_TIMEOUT_SECONDS:
            print("No browser connection detected. Stopping server.")
            server.shutdown()
            return


def get_default_browser_command() -> str | None:
    if os.name != "nt" or winreg is None:
        return None

    candidates = (
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
    )

    prog_id = None
    for subkey in candidates:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey) as key:
                prog_id = winreg.QueryValueEx(key, "ProgId")[0]
                break
        except OSError:
            continue

    if not prog_id:
        return None

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, fr"{prog_id}\shell\open\command") as key:
            return str(winreg.QueryValueEx(key, None)[0])
    except OSError:
        return None


def open_in_new_browser_window(url: str) -> bool:
    command = get_default_browser_command()
    if not command:
        return webbrowser.open_new(url)

    try:
        parts = shlex.split(command, posix=False)
    except ValueError:
        return webbrowser.open_new(url)

    if not parts:
        return webbrowser.open_new(url)

    executable = parts[0].strip('"')
    browser_name = Path(executable).name.lower()

    if browser_name == "firefox.exe":
        extra_args = ["-new-window"]
    elif browser_name in {"chrome.exe", "msedge.exe", "brave.exe", "opera.exe", "vivaldi.exe"}:
        extra_args = ["--new-window"]
    else:
        return webbrowser.open_new(url)

    try:
        subprocess.Popen([executable, *extra_args, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return webbrowser.open_new(url)


def main() -> None:
    port = find_free_port()
    server = AppServer((HOST, port), QuietHandler)
    url = f"http://{HOST}:{port}/index.html"

    monitor = threading.Thread(target=monitor_browser_activity, args=(server,), daemon=True)
    monitor.start()

    print("XML Prompt Editor")
    print(f"Serving: {url}")

    try:
        time.sleep(0.35)
        open_in_new_browser_window(url)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
