#!/usr/bin/env python3
"""Boiler desktop wrapper: pywebview native window + Flask backend."""

import os
import shutil
import socket
import sys
import threading
import time

# Redirect uploads/outputs to a writable user dir BEFORE importing app
DATA_DIR = os.path.expanduser('~/Library/Application Support/ZohoBoil')
os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'outputs'), exist_ok=True)

import app as boiler_app
boiler_app.UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
boiler_app.OUTPUT_FOLDER = os.path.join(DATA_DIR, 'outputs')

import webview


class Api:
    """Exposed to JS as window.pywebview.api."""

    def save_output(self, job_id):
        if job_id not in boiler_app.processing_status:
            return {'ok': False, 'error': 'job not found'}
        job = boiler_app.processing_status[job_id]
        if job.get('status') != 'complete':
            return {'ok': False, 'error': 'not complete'}
        src = job.get('output_path')
        if not src or not os.path.exists(src):
            return {'ok': False, 'error': 'output missing'}

        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=os.path.expanduser('~/Downloads'),
            save_filename='zohoboil_output.mp4',
            file_types=('MP4 video (*.mp4)',),
        )
        if not result:
            return {'ok': False, 'error': 'cancelled'}
        dest = result if isinstance(result, str) else result[0]
        shutil.copy2(src, dest)
        return {'ok': True, 'path': dest}


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
        'ZohoBoil',
        f'http://127.0.0.1:{port}',
        width=1500,
        height=1000,
        resizable=True,
        js_api=Api(),
    )
    # debug=True enables right-click context menu (Inspect, Copy, Paste, etc.)
    webview.start(debug=True)


if __name__ == '__main__':
    main()
