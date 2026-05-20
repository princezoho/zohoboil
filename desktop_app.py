#!/usr/bin/env python3
"""Boiler desktop wrapper: pywebview native window + Flask backend."""

import os
import sys
import threading
import socket
import time

# Redirect uploads/outputs to a writable user dir BEFORE importing app
DATA_DIR = os.path.expanduser('~/Library/Application Support/Boiler')
os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'outputs'), exist_ok=True)

import app as boiler_app
boiler_app.UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
boiler_app.OUTPUT_FOLDER = os.path.join(DATA_DIR, 'outputs')

import webview


def find_free_port(start=5050):
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port")


def run_flask(port):
    boiler_app.app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)


def wait_for_server(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main():
    port = find_free_port()
    t = threading.Thread(target=run_flask, args=(port,), daemon=True)
    t.start()
    if not wait_for_server(port):
        print("Server failed to start", file=sys.stderr)
        sys.exit(1)
    webview.create_window(
        'Boiler',
        f'http://127.0.0.1:{port}',
        width=1500,
        height=1000,
        resizable=True,
    )
    webview.start()


if __name__ == '__main__':
    main()
