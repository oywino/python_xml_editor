#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import http.server
import os
import socket
import threading
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"


def find_free_port(host: str = HOST) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    port = find_free_port()
    server = http.server.ThreadingHTTPServer((HOST, port), QuietHandler)
    url = f"http://{HOST}:{port}/index.html"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("XML Prompt Editor")
    print(f"Serving: {url}")
    print("Press Ctrl+C to stop.")

    try:
        time.sleep(0.35)
        webbrowser.open(url)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
