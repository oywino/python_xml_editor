#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import http
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
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
GITHUB_LATEST_RELEASE_URL = "https://api.github.com/repos/oywino/python_xml_editor/releases/latest"
UPDATE_CHECK_TIMEOUT_SECONDS = 4
UPDATE_USER_AGENT = "XML-Prompt-Editor-Updater"

if os.name == "nt":
    try:
        import ctypes
    except ImportError:  # pragma: no cover - Windows-only helper
        ctypes = None
else:  # pragma: no cover - Windows-only helper
    ctypes = None


def find_free_port(host: str = HOST) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


def read_current_version() -> str:
    app_js_path = BASE_DIR / "app.js"
    if not app_js_path.exists():
        return "v0.0.0"

    try:
        content = app_js_path.read_text(encoding="utf-8")
    except OSError:
        return "v0.0.0"

    marker = "const APP_VERSION = '"
    start = content.find(marker)
    if start == -1:
        return "v0.0.0"

    start += len(marker)
    end = content.find("'", start)
    if end == -1:
        return "v0.0.0"
    return content[start:end]


def parse_version(version: str) -> tuple[int, ...]:
    cleaned = version.strip().lstrip("vV")
    number_part = cleaned.split("-", 1)[0]
    parts = []
    for token in number_part.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer_version(latest: str, current: str) -> bool:
    latest_parts = parse_version(latest)
    current_parts = parse_version(current)
    max_len = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (max_len - len(latest_parts))
    current_parts += (0,) * (max_len - len(current_parts))
    return latest_parts > current_parts


def fetch_latest_release() -> dict | None:
    request = urllib.request.Request(
        GITHUB_LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": UPDATE_USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=UPDATE_CHECK_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except Exception:
        return None


def ask_yes_no(title: str, message: str) -> bool:
    if os.name != "nt" or ctypes is None:
        return False

    mb_yesno = 0x00000004
    mb_iconquestion = 0x00000020
    id_yes = 6
    result = ctypes.windll.user32.MessageBoxW(None, message, title, mb_yesno | mb_iconquestion)
    return result == id_yes


def show_error_dialog(title: str, message: str) -> None:
    if os.name != "nt" or ctypes is None:
        return

    mb_ok = 0x00000000
    mb_iconerror = 0x00000010
    ctypes.windll.user32.MessageBoxW(None, message, title, mb_ok | mb_iconerror)


def get_latest_release_asset(release: dict) -> tuple[str, str] | None:
    tag = str(release.get("tag_name") or "").strip()
    assets = release.get("assets") or []
    expected_name = f"XML_Prompt_Editor_{tag}.exe"

    for asset in assets:
        if asset.get("name") == expected_name:
            download_url = asset.get("browser_download_url")
            if download_url:
                return tag, str(download_url)
    return None


def download_update(download_url: str, version_tag: str) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="xml_editor_update_"))
    temp_path = temp_dir / f"XML_Prompt_Editor_{version_tag}.exe"
    request = urllib.request.Request(download_url, headers={"User-Agent": UPDATE_USER_AGENT})

    with urllib.request.urlopen(request, timeout=30) as response:
        with temp_path.open("wb") as fh:
            fh.write(response.read())

    return temp_path


def create_update_script(current_exe: Path, downloaded_exe: Path) -> Path:
    script_path = downloaded_exe.parent / "apply_update.cmd"
    lines = [
        "@echo off",
        "setlocal",
        f'set "TARGET={current_exe}"',
        f'set "SOURCE={downloaded_exe}"',
        f'set "PID={os.getpid()}"',
        ":waitloop",
        'tasklist /FI "PID eq %PID%" | find "%PID%" >nul',
        "if not errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto waitloop",
        ")",
        'move /Y "%SOURCE%" "%TARGET%" >nul',
        'if errorlevel 1 goto end',
        'start "" "%TARGET%"',
        ":end",
        'del "%~f0"',
    ]
    script_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return script_path


def maybe_apply_update() -> bool:
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return False

    current_exe = Path(sys.executable).resolve()
    if current_exe.suffix.lower() != ".exe":
        return False

    current_version = read_current_version()
    latest_release = fetch_latest_release()
    if not latest_release:
        return False

    asset_info = get_latest_release_asset(latest_release)
    if not asset_info:
        return False

    latest_version, download_url = asset_info
    if not is_newer_version(latest_version, current_version):
        return False

    prompt = (
        f"A newer version of XML Prompt Editor is available.\n\n"
        f"Current version: {current_version}\n"
        f"Latest version: {latest_version}\n\n"
        f"Do you want to download and install the update now?"
    )
    if not ask_yes_no("XML Prompt Editor Update", prompt):
        return False

    try:
        downloaded_exe = download_update(download_url, latest_version)
        update_script = create_update_script(current_exe, downloaded_exe)
        subprocess.Popen(
            ["cmd.exe", "/c", str(update_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return True
    except Exception:
        show_error_dialog(
            "XML Prompt Editor Update",
            "The update could not be downloaded or installed. The current version will continue to start normally.",
        )
        return False


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
    if maybe_apply_update():
        return

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
