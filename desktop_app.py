#!/usr/bin/env python3
"""Boiler desktop wrapper: pywebview native window + Flask backend."""

import json
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
boiler_app.DESKTOP_MODE = True

import subprocess

import webview

PREFS_PATH = os.path.join(DATA_DIR, 'prefs.json')


def last_save_dir():
    """Reopen the Save dialog wherever the user last saved."""
    try:
        with open(PREFS_PATH) as f:
            path = json.load(f).get('last_save_dir', '')
        if path and os.path.isdir(path):
            return path
    except (OSError, ValueError):
        pass
    return os.path.expanduser('~/Downloads')


def remember_save_dir(path):
    try:
        with open(PREFS_PATH, 'w') as f:
            json.dump({'last_save_dir': path}, f)
    except OSError:
        pass


class Api:
    """Exposed to JS as window.pywebview.api."""

    def save_output(self, job_id):
        src, name = boiler_app.finished_job(job_id)
        if src is None:
            return {'ok': False, 'error': name}

        try:
            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=last_save_dir(),
                save_filename=name,
                file_types=('MP4 video (*.mp4)',),
            )
        except Exception as e:
            # A broken dialog must not strand the user with no way to save.
            return self._save_to_downloads(src, name, note=str(e))

        if not result:
            return {'ok': False, 'error': 'cancelled'}
        dest = result if isinstance(result, str) else result[0]
        if not dest.lower().endswith('.mp4'):
            dest += '.mp4'
        try:
            shutil.copy2(src, dest)
        except OSError as e:
            return self._save_to_downloads(src, name, note=str(e))
        remember_save_dir(os.path.dirname(dest))
        return {'ok': True, 'path': dest}

    def _save_to_downloads(self, src, name, note=''):
        dest = boiler_app.unique_path(os.path.expanduser('~/Downloads'), name)
        try:
            shutil.copy2(src, dest)
        except OSError as e:
            return {'ok': False, 'error': note or str(e)}
        return {'ok': True, 'path': dest}

    def reveal(self, path):
        if os.path.exists(path):
            subprocess.run(['open', '-R', path], check=False)
        return {'ok': True}


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
