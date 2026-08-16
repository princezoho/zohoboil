#!/usr/bin/env python3
"""
Line Boil Effect Web App
Edge-aware line boil with color edge detection and varied randomness.
"""

import os
import platform
import shutil
import sys
import uuid
import threading
import base64
import subprocess
from flask import Flask, render_template_string, request, jsonify, send_file
import cv2
import numpy as np
from PIL import Image


def find_ffmpeg():
    """Locate ffmpeg: bundled binary first, then PATH, then well-known locations."""
    is_windows = platform.system() == 'Windows'
    exe_name = 'ffmpeg.exe' if is_windows else 'ffmpeg'

    candidates = []
    # Bundled inside PyInstaller bundle (_MEIPASS/bin/ffmpeg[.exe])
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        candidates.append(os.path.join(meipass, 'bin', exe_name))
    # Alongside this script (dev mode)
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', exe_name))
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    found = shutil.which('ffmpeg')
    if found:
        return found
    if is_windows:
        well_known = (
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        )
    else:
        well_known = (
            '/opt/homebrew/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/local/bin/ffmpeg',
            '/usr/bin/ffmpeg',
        )
    for path in well_known:
        if os.path.exists(path):
            return path
    return None


FFMPEG_PATH = find_ffmpeg()
if FFMPEG_PATH:
    print(f"ffmpeg: {FFMPEG_PATH}", file=sys.stderr)
else:
    print("WARNING: ffmpeg not found — output will lack audio and may not play in browsers.", file=sys.stderr)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

processing_status = {}
uploaded_videos = {}
job_save_names = {}

# Set to True by desktop_app.py. The browser can force a real download with a
# Content-Disposition header; the WKWebView the desktop app runs in cannot, so
# in desktop mode saving has to happen on this side of the wire.
DESKTOP_MODE = False

DEFAULT_GIF_DURATION = 5.0  # Default output duration for GIFs in seconds


def sanitize_name(name):
    """Reduce an arbitrary upload filename to something safe to write to disk."""
    keep = [c for c in name if c.isalnum() or c in ' ._-']
    cleaned = ''.join(keep).strip().replace(' ', '-')
    return cleaned[:60] or 'video'


def unique_path(directory, filename):
    """A path in `directory` that does not collide with an existing file."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}-{counter}{ext}")
        counter += 1
    return candidate


def convert_gif_to_video(gif_path, output_path, target_duration=DEFAULT_GIF_DURATION):
    """
    Convert an animated GIF to a video file.
    Loops the GIF to fill target_duration seconds (default 5s).
    Returns (total_frames, width, height, fps).
    """
    gif = Image.open(gif_path)

    # Extract all frames and their durations
    frames = []
    durations = []

    try:
        while True:
            # Convert frame to RGB (GIFs can have palette mode)
            frame = gif.convert('RGB')
            frames.append(np.array(frame))

            # Get frame duration in ms (default 100ms if not specified)
            duration = gif.info.get('duration', 100)
            if duration == 0:
                duration = 100
            durations.append(duration)

            gif.seek(gif.tell() + 1)
    except EOFError:
        pass

    if not frames:
        raise ValueError("No frames found in GIF")

    # Calculate original GIF duration in seconds
    original_duration = sum(durations) / 1000.0

    # Determine output FPS (use average frame rate from GIF, min 10fps, max 30fps)
    avg_frame_duration = sum(durations) / len(durations)
    gif_fps = 1000.0 / avg_frame_duration
    output_fps = max(10, min(30, gif_fps))

    # Calculate how many times to loop to fill target duration
    if original_duration > 0:
        num_loops = max(1, int(np.ceil(target_duration / original_duration)))
    else:
        num_loops = 1

    # Calculate total output frames
    total_output_frames = int(target_duration * output_fps)

    # Get dimensions
    height, width = frames[0].shape[:2]

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))

    # Build frame timing map (which GIF frame to show at each output frame)
    # Create a timeline of GIF frames looped to fill target duration
    looped_timeline = []  # (time_ms, frame_index)
    current_time = 0
    for loop in range(num_loops):
        for i, duration in enumerate(durations):
            looped_timeline.append((current_time, i))
            current_time += duration
            if current_time >= target_duration * 1000:
                break
        if current_time >= target_duration * 1000:
            break

    # Write frames to video
    for out_frame_idx in range(total_output_frames):
        # Calculate time for this output frame
        frame_time_ms = (out_frame_idx / output_fps) * 1000

        # Find which GIF frame should be shown at this time
        gif_frame_idx = 0
        for time_ms, idx in looped_timeline:
            if time_ms <= frame_time_ms:
                gif_frame_idx = idx
            else:
                break

        # Get the frame and convert RGB to BGR for OpenCV
        frame_rgb = frames[gif_frame_idx]
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()

    return total_output_frames, width, height, output_fps


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZohoBoil</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@700&display=swap');

        * { box-sizing: border-box; }
        body {
            font-family: Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0605;
            color: #e8dcc8;
            min-height: 100vh;
        }
        h1, h2, h3, h4 {
            font-family: 'EB Garamond', Garamond, Georgia, serif;
            font-weight: 700;
        }
        h1 {
            text-align: center;
            color: #e8b84a;
            margin-bottom: 15px;
            font-size: 28px;
        }
        h1 sup { font-size: 12px; vertical-align: super; }

        .main-container {
            display: flex;
            gap: 15px;
            max-width: 1600px;
            margin: 0 auto;
        }

        .controls-panel {
            width: 260px;
            flex-shrink: 0;
        }

        .controls-panel-right {
            width: 260px;
            flex-shrink: 0;
        }

        .drop-zone {
            border: 2px dashed #4a3025;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 12px;
            background: #1e120d;
            font-size: 13px;
        }
        .drop-zone:hover, .drop-zone.dragover { border-color: #e8b84a; background: #2a1a12; }
        .drop-zone.has-file { border-color: #5cb85c; }
        .file-name { color: #5cb85c; font-weight: bold; margin-top: 8px; font-size: 12px; }

        .params {
            background: #1e120d;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 12px;
        }
        .params h3 { margin: 0 0 12px 0; color: #e8b84a; font-size: 14px; }
        .param-row { margin-bottom: 12px; }
        .param-row label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 12px;
        }
        .param-row input[type="range"] { width: 100%; accent-color: #e8b84a; }
        .param-value { color: #e8b84a; font-family: Helvetica, monospace; font-weight: bold; }
        .param-desc { font-size: 10px; color: #8a7560; margin-top: 2px; }

        select {
            width: 100%;
            padding: 8px;
            font-size: 12px;
            font-family: Helvetica, Arial, sans-serif;
            background: #1a0f0a;
            color: #e8dcc8;
            border: 1px solid #4a3025;
            border-radius: 4px;
            cursor: pointer;
        }
        select:hover { border-color: #e8b84a; }
        select:focus { outline: none; border-color: #e8b84a; }

        button {
            width: 100%;
            padding: 10px 16px;
            font-size: 13px;
            font-family: Helvetica, Arial, sans-serif;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 8px;
        }
        button.primary { background: #e8b84a; color: #0a0605; font-weight: bold; }
        button.primary:hover { background: #d4a032; }
        button.secondary { background: #2a1a12; color: #e8dcc8; }
        button.secondary:hover { background: #3a2518; }
        button:disabled { background: #1a100c; color: #4a3a2a; cursor: not-allowed; }

        .progress-container { margin: 12px 0; display: none; }
        .progress-bar {
            height: 16px;
            background: #1a0f0a;
            border-radius: 8px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #e8b84a, #5cb85c);
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text { text-align: center; margin-top: 6px; color: #8a7560; font-size: 11px; }
        .download-btn { display: none; background: #5cb85c; color: #0a0605; font-weight: bold; }
        .download-btn:hover { background: #4a9f4a; }
        .saved-row { display: none; align-items: center; gap: 10px; margin-top: 10px; }
        .saved-path { flex: 1; font-size: 12px; opacity: 0.75; word-break: break-all; }

        .preview-panel {
            flex: 1;
            min-width: 0;
            max-width: 750px;
        }

        .preview-section {
            background: #1e120d;
            padding: 12px;
            border-radius: 10px;
        }
        .preview-section h3 { margin: 0 0 8px 0; color: #e8b84a; font-size: 14px; text-align: center; }

        .preview-stack {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        /* Side-by-side layout for portrait/square videos */
        .preview-stack.horizontal {
            flex-direction: row;
        }
        .preview-stack.horizontal .preview-box {
            width: 50%;
        }

        .preview-box {
            width: 100%;
        }
        .preview-box h4 { margin: 0 0 5px 0; font-size: 12px; color: #8a7560; text-align: center; }
        .preview-box img {
            width: 100%;
            border-radius: 6px;
            background: #0a0605;
            display: block;
        }
        .preview-placeholder {
            width: 100%;
            aspect-ratio: 16/9;
            background: #0a0605;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #5a3d2a;
            font-size: 12px;
        }
        /* Smaller preview panel for portrait videos */
        .preview-panel.portrait {
            max-width: 500px;
        }

        .frame-controls {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 10px;
            padding: 8px;
            background: #0a0605;
            border-radius: 6px;
        }
        .frame-controls label { font-size: 11px; }
        .frame-controls input[type="range"] { flex: 1; accent-color: #e8b84a; }
        .frame-controls span { font-size: 10px; color: #8a7560; min-width: 60px; }

        input[type="file"] { display: none; }
        .loading { opacity: 0.5; pointer-events: none; }
    </style>
</head>
<body>
    <h1>ZohoBoil<sup>TM</sup></h1>

    <div class="main-container">
        <div class="controls-panel">
            <div class="drop-zone" id="dropZone">
                <p>Drag & drop video or GIF<br>or click to browse</p>
                <div class="file-name" id="fileName"></div>
            </div>
            <input type="file" id="fileInput" accept=".mp4,.mov,.avi,.mkv,.gif">

            <div class="params">
                <h3>Line Boil Settings</h3>

                <div class="param-row">
                    <label>
                        <span>Max Shift</span>
                        <span class="param-value" id="shiftVal">3</span><span style="color:#888">px</span>
                    </label>
                    <input type="range" id="shift" min="1" max="10" step="1" value="3">
                    <div class="param-desc">Maximum pixel displacement</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Region Size</span>
                        <span class="param-value" id="regionVal">6</span><span style="color:#888">px</span>
                    </label>
                    <input type="range" id="region" min="2" max="32" step="1" value="6">
                    <div class="param-desc">Base size of displacement chunks</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Randomness</span>
                        <span class="param-value" id="randomVal">0.8</span>
                    </label>
                    <input type="range" id="random" min="0" max="1" step="0.1" value="0.8">
                    <div class="param-desc">Variation in displacement strength</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Hold Frames</span>
                        <span class="param-value" id="holdVal">2</span>
                    </label>
                    <input type="range" id="hold" min="1" max="8" step="1" value="2">
                    <div class="param-desc">Frames before boil changes</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Variations</span>
                        <span class="param-value" id="variationsVal">4</span>
                    </label>
                    <input type="range" id="variations" min="2" max="8" step="1" value="4">
                    <div class="param-desc">Different boil positions</div>
                </div>
            </div>

            <div class="params">
                <h3>Edge Detection</h3>

                <div class="param-row">
                    <label>
                        <span>Edge Weight</span>
                        <span class="param-value" id="edgeWeightVal">0.6</span>
                    </label>
                    <input type="range" id="edgeWeight" min="0" max="1" step="0.1" value="0.6">
                    <div class="param-desc">0 = uniform, 1 = edges only</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Edge Sensitivity</span>
                        <span class="param-value" id="edgeSensVal">0.7</span>
                    </label>
                    <input type="range" id="edgeSens" min="0.1" max="1" step="0.1" value="0.7">
                    <div class="param-desc">Higher = catches subtle color changes</div>
                </div>
            </div>

            <div class="params">
                <h3>Line Quality</h3>

                <div class="param-row">
                    <label>
                        <span>Chunkiness</span>
                        <span class="param-value" id="chunkinessVal">0.7</span>
                    </label>
                    <input type="range" id="chunkiness" min="0" max="1" step="0.1" value="0.7">
                    <div class="param-desc">0 = fine/tight, 1 = blocky chunks</div>
                </div>

                <div class="param-row">
                    <label><span>Edge Blend</span></label>
                    <select id="waveType">
                        <option value="noise">Chunky (original)</option>
                        <option value="sine">Smooth (soft edges)</option>
                        <option value="triangle">Medium (gentle blend)</option>
                        <option value="saw">Linear (clean ramp)</option>
                        <option value="square">Hard (sharp blocks)</option>
                    </select>
                    <div class="param-desc">How displacement transitions at edges</div>
                </div>
            </div>

        </div>

        <div class="preview-panel">
            <div class="preview-section">
                <h3>Preview</h3>
                <div class="preview-stack">
                    <div class="preview-box">
                        <h4>Original</h4>
                        <div class="preview-placeholder" id="originalPlaceholder">Upload a video</div>
                        <img id="originalImg" style="display:none">
                    </div>
                    <div class="preview-box">
                        <h4>With Line Boil</h4>
                        <div class="preview-placeholder" id="effectPlaceholder">Upload a video</div>
                        <img id="effectImg" style="display:none">
                    </div>
                </div>
                <div class="frame-controls">
                    <label>Frame:</label>
                    <input type="range" id="frameSlider" min="0" max="100" value="0" disabled>
                    <span id="frameNum">0</span>
                </div>
            </div>
        </div>

        <div class="controls-panel-right">
            <div class="params">
                <h3>Chromatic Aberration</h3>

                <div class="param-row">
                    <label>
                        <span>R Offset</span>
                        <span class="param-value" id="caRedVal">0</span><span style="color:#888">px</span>
                    </label>
                    <input type="range" id="caRed" min="-10" max="10" step="1" value="0">
                    <div class="param-desc">Red channel shift</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>G Offset</span>
                        <span class="param-value" id="caGreenVal">0</span><span style="color:#888">px</span>
                    </label>
                    <input type="range" id="caGreen" min="-10" max="10" step="1" value="0">
                    <div class="param-desc">Green channel shift</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>B Offset</span>
                        <span class="param-value" id="caBlueVal">0</span><span style="color:#888">px</span>
                    </label>
                    <input type="range" id="caBlue" min="-10" max="10" step="1" value="0">
                    <div class="param-desc">Blue channel shift</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>CA Blur</span>
                        <span class="param-value" id="caBlurVal">0</span>
                    </label>
                    <input type="range" id="caBlur" min="0" max="5" step="1" value="0">
                    <div class="param-desc">Blur on offset channels</div>
                </div>
            </div>

            <div class="params">
                <h3>Noise Overlay</h3>

                <div class="param-row">
                    <label><span>Noise Type</span></label>
                    <select id="noiseType">
                        <option value="none">None</option>
                        <option value="grain_fine">Fine Grain</option>
                        <option value="grain_medium">Medium Grain</option>
                        <option value="grain_coarse">Coarse Grain</option>
                        <option value="static">TV Static</option>
                        <option value="perlin_fine">Perlin Fine</option>
                        <option value="perlin_medium">Perlin Medium</option>
                        <option value="perlin_coarse">Perlin Coarse</option>
                        <option value="scanlines">Scanlines</option>
                    </select>
                    <div class="param-desc">Type of animated noise</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Intensity</span>
                        <span class="param-value" id="noiseIntensityVal">0.00</span>
                    </label>
                    <input type="range" id="noiseIntensity" min="0" max="0.5" step="0.01" value="0">
                    <div class="param-desc">Noise visibility (0-0.5)</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Scale</span>
                        <span class="param-value" id="noiseSizeVal">1.0</span>
                    </label>
                    <input type="range" id="noiseSize" min="0.5" max="4" step="0.1" value="1">
                    <div class="param-desc">Noise scale multiplier</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Speed</span>
                        <span class="param-value" id="noiseSpeedVal">1.0</span><span style="color:#888">x</span>
                    </label>
                    <input type="range" id="noiseSpeed" min="0.25" max="4" step="0.25" value="1">
                    <div class="param-desc">Animation speed</div>
                </div>

                <div class="param-row">
                    <label>
                        <span>Density</span>
                        <span class="param-value" id="noiseRandomVal">1.0</span>
                    </label>
                    <input type="range" id="noiseRandom" min="0.1" max="1" step="0.1" value="1">
                    <div class="param-desc">Grain density/coverage</div>
                </div>
            </div>

            <button class="primary" id="processBtn" disabled>Process Video</button>
            <button class="secondary" id="livePreviewBtn" disabled>▶ Live Preview</button>
            <button class="secondary" id="refreshPreview" disabled>Refresh Frame</button>

            <div class="progress-container" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">Processing...</div>
            </div>

            <button class="download-btn" id="downloadBtn">Download Result</button>
            <div class="saved-row" id="savedRow">
                <span class="saved-path" id="savedPath"></span>
                <button class="secondary" id="revealBtn">Show in Finder</button>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const processBtn = document.getElementById('processBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const downloadBtn = document.getElementById('downloadBtn');
        const savedRow = document.getElementById('savedRow');
        const savedPath = document.getElementById('savedPath');
        const revealBtn = document.getElementById('revealBtn');
        const refreshPreview = document.getElementById('refreshPreview');
        const livePreviewBtn = document.getElementById('livePreviewBtn');
        const frameSlider = document.getElementById('frameSlider');
        const frameNum = document.getElementById('frameNum');

        let uploadId = null;
        let totalFrames = 0;
        let jobId = null;
        let previewTimeout = null;

        // Live preview animation state
        let isAnimating = false;
        let animationFrameId = null;
        let originalFrames = [];
        let effectFrames = [];
        let currentAnimFrame = 0;
        let animFps = 24;
        let lastFrameTime = 0;
        let isLoadingBatch = false;
        let pendingBatchUpdate = false;

        function bindSlider(id, valId, isFloat=false) {
            document.getElementById(id).oninput = (e) => {
                document.getElementById(valId).textContent = isFloat ?
                    parseFloat(e.target.value).toFixed(1) : e.target.value;
                schedulePreviewUpdate();
            };
        }
        bindSlider('shift', 'shiftVal');
        bindSlider('region', 'regionVal');
        bindSlider('random', 'randomVal', true);
        bindSlider('hold', 'holdVal');
        bindSlider('variations', 'variationsVal');
        bindSlider('edgeWeight', 'edgeWeightVal', true);
        bindSlider('edgeSens', 'edgeSensVal', true);
        bindSlider('chunkiness', 'chunkinessVal', true);
        bindSlider('caRed', 'caRedVal');
        bindSlider('caGreen', 'caGreenVal');
        bindSlider('caBlue', 'caBlueVal');
        bindSlider('caBlur', 'caBlurVal');
        bindSlider('noiseIntensity', 'noiseIntensityVal', true);
        bindSlider('noiseSize', 'noiseSizeVal', true);
        bindSlider('noiseSpeed', 'noiseSpeedVal', true);
        bindSlider('noiseRandom', 'noiseRandomVal', true);

        document.getElementById('waveType').onchange = schedulePreviewUpdate;
        document.getElementById('noiseType').onchange = schedulePreviewUpdate;

        frameSlider.oninput = (e) => {
            frameNum.textContent = e.target.value;
            schedulePreviewUpdate();
        };

        function schedulePreviewUpdate() {
            if (previewTimeout) clearTimeout(previewTimeout);
            if (isAnimating) {
                // Update live preview with new parameters
                previewTimeout = setTimeout(fetchBatchFrames, 300);
            } else {
                previewTimeout = setTimeout(updatePreview, 200);
            }
        }

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) handleFile(fileInput.files[0]);
        });

        async function handleFile(file) {
            fileName.textContent = file.name;
            dropZone.classList.add('has-file');

            const formData = new FormData();
            formData.append('video', file);

            try {
                dropZone.classList.add('loading');
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                uploadId = data.upload_id;
                totalFrames = data.total_frames;

                frameSlider.max = totalFrames - 1;
                frameSlider.value = Math.floor(totalFrames / 2);
                frameSlider.disabled = false;
                frameNum.textContent = frameSlider.value;

                // Detect aspect ratio and adjust layout
                const aspectRatio = data.width / data.height;
                const previewStack = document.querySelector('.preview-stack');
                const previewPanel = document.querySelector('.preview-panel');

                if (aspectRatio <= 1.0) {
                    // Portrait or square: side-by-side layout
                    previewStack.classList.add('horizontal');
                    previewPanel.classList.add('portrait');
                } else {
                    // Landscape: stacked layout
                    previewStack.classList.remove('horizontal');
                    previewPanel.classList.remove('portrait');
                }

                processBtn.disabled = false;
                refreshPreview.disabled = false;
                livePreviewBtn.disabled = false;
                dropZone.classList.remove('loading');

                updatePreview();
            } catch (error) {
                alert('Error uploading: ' + error.message);
                dropZone.classList.remove('loading');
            }
        }

        async function updatePreview() {
            if (!uploadId) return;

            const params = new URLSearchParams({
                upload_id: uploadId,
                frame: frameSlider.value,
                shift: document.getElementById('shift').value,
                region: document.getElementById('region').value,
                random: document.getElementById('random').value,
                hold: document.getElementById('hold').value,
                variations: document.getElementById('variations').value,
                edge_weight: document.getElementById('edgeWeight').value,
                edge_sens: document.getElementById('edgeSens').value,
                chunkiness: document.getElementById('chunkiness').value,
                wave_type: document.getElementById('waveType').value,
                ca_red: document.getElementById('caRed').value,
                ca_green: document.getElementById('caGreen').value,
                ca_blue: document.getElementById('caBlue').value,
                ca_blur: document.getElementById('caBlur').value,
                noise_type: document.getElementById('noiseType').value,
                noise_intensity: document.getElementById('noiseIntensity').value,
                noise_size: document.getElementById('noiseSize').value,
                noise_speed: document.getElementById('noiseSpeed').value,
                noise_random: document.getElementById('noiseRandom').value
            });

            try {
                const response = await fetch('/preview?' + params);
                const data = await response.json();

                document.getElementById('originalPlaceholder').style.display = 'none';
                document.getElementById('effectPlaceholder').style.display = 'none';

                document.getElementById('originalImg').src = 'data:image/jpeg;base64,' + data.original;
                document.getElementById('originalImg').style.display = 'block';

                document.getElementById('effectImg').src = 'data:image/jpeg;base64,' + data.effect;
                document.getElementById('effectImg').style.display = 'block';
            } catch (error) {
                console.error('Preview error:', error);
            }
        }

        refreshPreview.addEventListener('click', updatePreview);

        // Live Preview Functions
        async function fetchBatchFrames() {
            if (!uploadId || isLoadingBatch) {
                pendingBatchUpdate = true;
                return;
            }

            isLoadingBatch = true;
            livePreviewBtn.textContent = '⏳ Loading...';

            const params = new URLSearchParams({
                upload_id: uploadId,
                num_frames: totalFrames,
                shift: document.getElementById('shift').value,
                region: document.getElementById('region').value,
                random: document.getElementById('random').value,
                hold: document.getElementById('hold').value,
                variations: document.getElementById('variations').value,
                edge_weight: document.getElementById('edgeWeight').value,
                edge_sens: document.getElementById('edgeSens').value,
                chunkiness: document.getElementById('chunkiness').value,
                wave_type: document.getElementById('waveType').value,
                ca_red: document.getElementById('caRed').value,
                ca_green: document.getElementById('caGreen').value,
                ca_blue: document.getElementById('caBlue').value,
                ca_blur: document.getElementById('caBlur').value,
                noise_type: document.getElementById('noiseType').value,
                noise_intensity: document.getElementById('noiseIntensity').value,
                noise_size: document.getElementById('noiseSize').value,
                noise_speed: document.getElementById('noiseSpeed').value,
                noise_random: document.getElementById('noiseRandom').value
            });

            try {
                const response = await fetch('/preview_batch?' + params);
                const data = await response.json();

                originalFrames = data.original_frames;
                effectFrames = data.effect_frames;
                animFps = data.fps || 24;
                currentAnimFrame = 0;

                document.getElementById('originalPlaceholder').style.display = 'none';
                document.getElementById('effectPlaceholder').style.display = 'none';
                document.getElementById('originalImg').style.display = 'block';
                document.getElementById('effectImg').style.display = 'block';

                livePreviewBtn.textContent = '⏸ Pause';

                if (!isAnimating) {
                    isAnimating = true;
                    lastFrameTime = performance.now();
                    animatePreview();
                }
            } catch (error) {
                console.error('Batch preview error:', error);
                livePreviewBtn.textContent = '▶ Live Preview';
            }

            isLoadingBatch = false;

            if (pendingBatchUpdate) {
                pendingBatchUpdate = false;
                fetchBatchFrames();
            }
        }

        function animatePreview() {
            if (!isAnimating || effectFrames.length === 0) return;

            const now = performance.now();
            const elapsed = now - lastFrameTime;
            const frameInterval = 1000 / animFps;

            if (elapsed >= frameInterval) {
                lastFrameTime = now - (elapsed % frameInterval);

                document.getElementById('originalImg').src = 'data:image/jpeg;base64,' + originalFrames[currentAnimFrame];
                document.getElementById('effectImg').src = 'data:image/jpeg;base64,' + effectFrames[currentAnimFrame];

                currentAnimFrame = (currentAnimFrame + 1) % effectFrames.length;
            }

            animationFrameId = requestAnimationFrame(animatePreview);
        }

        function stopAnimation() {
            isAnimating = false;
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                animationFrameId = null;
            }
            livePreviewBtn.textContent = '▶ Live Preview';
        }

        function scheduleBatchUpdate() {
            if (isAnimating) {
                if (previewTimeout) clearTimeout(previewTimeout);
                previewTimeout = setTimeout(fetchBatchFrames, 300);
            }
        }

        livePreviewBtn.addEventListener('click', () => {
            if (isAnimating) {
                stopAnimation();
            } else {
                fetchBatchFrames();
            }
        });

        processBtn.addEventListener('click', async () => {
            if (!uploadId) return;

            const params = {
                upload_id: uploadId,
                shift: document.getElementById('shift').value,
                region: document.getElementById('region').value,
                random: document.getElementById('random').value,
                hold: document.getElementById('hold').value,
                variations: document.getElementById('variations').value,
                edge_weight: document.getElementById('edgeWeight').value,
                edge_sens: document.getElementById('edgeSens').value,
                chunkiness: document.getElementById('chunkiness').value,
                wave_type: document.getElementById('waveType').value,
                ca_red: document.getElementById('caRed').value,
                ca_green: document.getElementById('caGreen').value,
                ca_blue: document.getElementById('caBlue').value,
                ca_blur: document.getElementById('caBlur').value,
                noise_type: document.getElementById('noiseType').value,
                noise_intensity: document.getElementById('noiseIntensity').value,
                noise_size: document.getElementById('noiseSize').value,
                noise_speed: document.getElementById('noiseSpeed').value,
                noise_random: document.getElementById('noiseRandom').value
            };

            processBtn.disabled = true;
            progressContainer.style.display = 'block';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting...';
            downloadBtn.style.display = 'none';
            savedRow.style.display = 'none';

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                const data = await response.json();
                jobId = data.job_id;
                checkProgress();
            } catch (error) {
                progressText.textContent = 'Error: ' + error.message;
                processBtn.disabled = false;
            }
        });

        // Whether we are inside the desktop app's web view. Answered by the
        // server, so it does not depend on the pywebview bridge being injected.
        let isDesktop = false;
        fetch('/config')
            .then(r => r.json())
            .then(cfg => { isDesktop = !!cfg.desktop; })
            .catch(() => {});

        // The pywebview bridge is injected after load, so a click that lands
        // early would otherwise fall through to the browser download path.
        function pywebviewApi(timeoutMs) {
            const deadline = Date.now() + (timeoutMs || 0);
            return new Promise(resolve => {
                (function poll() {
                    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_output) {
                        resolve(window.pywebview.api);
                    } else if (Date.now() >= deadline) {
                        resolve(null);
                    } else {
                        setTimeout(poll, 50);
                    }
                })();
            });
        }

        async function saveResult(jobId) {
            downloadBtn.disabled = true;
            const label = downloadBtn.textContent;
            downloadBtn.textContent = 'Saving...';
            try {
                if (isDesktop) {
                    // Preferred: a real macOS Save dialog, so the user picks the folder.
                    const api = await pywebviewApi(3000);
                    if (api) {
                        const res = await api.save_output(jobId);
                        if (res && res.ok) {
                            showSaved(res.path);
                            return;
                        }
                        if (res && res.error === 'cancelled') return;
                    }
                    // Bridge unavailable: drop it in ~/Downloads rather than
                    // navigating the web view to the video (which just plays it).
                    const res = await fetch('/save/' + jobId, { method: 'POST' }).then(r => r.json());
                    if (res.ok) {
                        showSaved(res.path);
                    } else {
                        alert('Save failed: ' + res.error);
                    }
                } else {
                    // Browser: Content-Disposition on /download does the work.
                    window.location.assign('/download/' + jobId);
                }
            } catch (e) {
                alert('Save error: ' + e.message);
            } finally {
                downloadBtn.disabled = false;
                downloadBtn.textContent = label;
            }
        }

        function showSaved(path) {
            savedRow.style.display = 'flex';
            savedPath.textContent = 'Saved to ' + path;
            revealBtn.onclick = () => fetch('/reveal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
        }

        async function checkProgress() {
            try {
                const response = await fetch('/status/' + jobId);
                const data = await response.json();

                progressFill.style.width = data.progress + '%';
                progressText.textContent = data.message;

                if (data.status === 'complete') {
                    downloadBtn.style.display = 'block';
                    downloadBtn.onclick = () => saveResult(jobId);
                    processBtn.disabled = false;
                } else if (data.status === 'error') {
                    processBtn.disabled = false;
                } else {
                    setTimeout(checkProgress, 500);
                }
            } catch (error) {
                progressText.textContent = 'Error checking status';
                processBtn.disabled = false;
            }
        }
    </script>
</body>
</html>
'''


def detect_color_edges(frame, sensitivity):
    """
    Detect edges across all color channels to catch all color transitions.
    Works on dark blue to medium blue, medium to light, etc.
    """
    # Convert to LAB color space for perceptual color differences
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)

    # Detect edges in each channel
    edge_maps = []
    for i in range(3):
        channel = lab[:, :, i]
        grad_x = cv2.Sobel(channel, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(channel, cv2.CV_32F, 0, 1, ksize=3)
        edge_mag = cv2.magnitude(grad_x, grad_y)
        edge_maps.append(edge_mag)

    # Combine all channels - take max edge from any channel
    combined = np.maximum(np.maximum(edge_maps[0], edge_maps[1]), edge_maps[2])

    # Normalize
    combined = combined / (combined.max() + 1e-6)

    # Apply sensitivity - higher sensitivity catches more subtle edges
    # Use a power curve to enhance sensitivity
    edge_weight = np.power(combined, 1.0 / (sensitivity + 0.1))
    edge_weight = np.clip(edge_weight, 0, 1)

    # Slight blur for smoother transitions
    edge_weight = cv2.GaussianBlur(edge_weight.astype(np.float32), (3, 3), 0.5)

    return edge_weight


def generate_varied_displacements(h, w, region_size, max_shift, randomness, num_variations, chunkiness=0.7, blend_type='noise', seed=0):
    """
    Generate displacement maps with varying strength across the image.
    blend_type controls how displacement transitions at region edges:
    - 'noise': random with chunky edges
    - 'sine': very smooth blended transitions
    - 'saw': linear ramp transitions
    - 'square': hard blocky edges
    - 'triangle': soft linear blend
    """
    np.random.seed(seed)
    variations = []

    # Chunkiness affects effective region size - higher = bigger blocks
    effective_region = int(region_size * (1 + chunkiness * 3))

    for v in range(num_variations):
        # Base grid
        regions_h = max(2, (h + effective_region - 1) // effective_region)
        regions_w = max(2, (w + effective_region - 1) // effective_region)

        # Always generate random displacement values per region
        dx_regions = np.random.uniform(-1, 1, (regions_h, regions_w)).astype(np.float32)
        dy_regions = np.random.uniform(-1, 1, (regions_h, regions_w)).astype(np.float32)

        # Random STRENGTH per region
        if randomness > 0:
            strength_map = np.random.uniform(0.2, 1.0, (regions_h, regions_w)).astype(np.float32)
            zero_mask = np.random.random((regions_h, regions_w)) < (randomness * 0.3)
            strength_map[zero_mask] = 0
        else:
            strength_map = np.ones((regions_h, regions_w), dtype=np.float32)

        # Apply strength to displacement
        dx_regions *= strength_map * max_shift
        dy_regions *= strength_map * max_shift

        # Upscale based on blend type - this controls edge smoothness
        if blend_type == 'square':
            # Hard blocky edges - nearest neighbor
            interp = cv2.INTER_NEAREST
            dx = cv2.resize(dx_regions, (w, h), interpolation=interp)
            dy = cv2.resize(dy_regions, (w, h), interpolation=interp)
        elif blend_type == 'saw':
            # Sharp linear transitions
            interp = cv2.INTER_LINEAR
            dx = cv2.resize(dx_regions, (w, h), interpolation=interp)
            dy = cv2.resize(dy_regions, (w, h), interpolation=interp)
        elif blend_type == 'triangle':
            # Soft linear blend with slight smoothing
            dx = cv2.resize(dx_regions, (w, h), interpolation=cv2.INTER_LINEAR)
            dy = cv2.resize(dy_regions, (w, h), interpolation=cv2.INTER_LINEAR)
            # Light blur for softer edges
            blur_size = max(3, effective_region // 4) | 1  # ensure odd
            dx = cv2.GaussianBlur(dx, (blur_size, blur_size), 0)
            dy = cv2.GaussianBlur(dy, (blur_size, blur_size), 0)
        elif blend_type == 'sine':
            # Very smooth sinusoidal transitions - cubic + heavy blur
            dx = cv2.resize(dx_regions, (w, h), interpolation=cv2.INTER_CUBIC)
            dy = cv2.resize(dy_regions, (w, h), interpolation=cv2.INTER_CUBIC)
            # Heavy blur for smooth sine-like transitions
            blur_size = max(5, effective_region // 2) | 1  # ensure odd
            dx = cv2.GaussianBlur(dx, (blur_size, blur_size), 0)
            dy = cv2.GaussianBlur(dy, (blur_size, blur_size), 0)
        else:  # 'noise' - original behavior based on chunkiness
            if chunkiness >= 0.5:
                interp = cv2.INTER_NEAREST
            else:
                interp = cv2.INTER_LINEAR
            dx = cv2.resize(dx_regions, (w, h), interpolation=interp)
            dy = cv2.resize(dy_regions, (w, h), interpolation=interp)
            # Per-pixel jitter for noise mode
            jitter_strength = (1.0 - chunkiness) * randomness
            if jitter_strength > 0.2:
                jitter = max_shift * 0.15 * jitter_strength
                dx += np.random.uniform(-jitter, jitter, (h, w)).astype(np.float32)
                dy += np.random.uniform(-jitter, jitter, (h, w)).astype(np.float32)

        variations.append((dx, dy))

    return variations


def apply_chromatic_aberration(frame, r_offset, g_offset, b_offset, blur_amount):
    """Apply chromatic aberration by shifting RGB channels."""
    if r_offset == 0 and g_offset == 0 and b_offset == 0 and blur_amount == 0:
        return frame

    h, w = frame.shape[:2]
    b, g, r = cv2.split(frame)

    def shift_channel(channel, offset_x, offset_y=0):
        if offset_x == 0 and offset_y == 0:
            return channel
        M = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
        return cv2.warpAffine(channel, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    r_shifted = shift_channel(r, r_offset)
    g_shifted = shift_channel(g, g_offset)
    b_shifted = shift_channel(b, b_offset)

    if blur_amount > 0:
        ksize = int(blur_amount) * 2 + 1
        r_shifted = cv2.GaussianBlur(r_shifted, (ksize, ksize), 0)
        g_shifted = cv2.GaussianBlur(g_shifted, (ksize, ksize), 0)
        b_shifted = cv2.GaussianBlur(b_shifted, (ksize, ksize), 0)

    return cv2.merge([b_shifted, g_shifted, r_shifted])


def generate_noise_frame(h, w, noise_type, intensity, scale, density, frame_idx, speed):
    """Generate a noise overlay frame with fine control."""
    if noise_type == 'none' or intensity == 0:
        return None

    # Seed based on frame for animation
    seed = int(frame_idx * speed * 1000) % (2**31)
    np.random.seed(seed)

    # Fine grain - per-pixel noise
    if noise_type == 'grain_fine':
        noise = np.random.normal(0, 1, (h, w)).astype(np.float32)
        # Apply density (sparse out the grain)
        if density < 1:
            mask = np.random.random((h, w)) < density
            noise = noise * mask
        # Scale affects the blur/softness
        if scale > 1:
            ksize = int(scale * 2) | 1  # ensure odd
            noise = cv2.GaussianBlur(noise, (ksize, ksize), 0)

    # Medium grain - slight upscaling
    elif noise_type == 'grain_medium':
        base_size = max(1, int(2 * scale))
        small_h, small_w = max(1, h // base_size), max(1, w // base_size)
        noise = np.random.normal(0, 1, (small_h, small_w)).astype(np.float32)
        noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_LINEAR)
        if density < 1:
            mask = np.random.random((h, w)) < density
            noise = noise * mask

    # Coarse grain - larger clumps
    elif noise_type == 'grain_coarse':
        base_size = max(1, int(4 * scale))
        small_h, small_w = max(1, h // base_size), max(1, w // base_size)
        noise = np.random.normal(0, 1, (small_h, small_w)).astype(np.float32)
        noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_LINEAR)
        # Slight blur for softer clumps
        noise = cv2.GaussianBlur(noise, (3, 3), 0)
        if density < 1:
            mask = np.random.random((h, w)) < density
            noise = noise * mask

    # TV static - harsh random
    elif noise_type == 'static':
        base_size = max(1, int(scale))
        if base_size > 1:
            small_h, small_w = max(1, h // base_size), max(1, w // base_size)
            noise = np.random.uniform(-1, 1, (small_h, small_w)).astype(np.float32)
            noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            noise = np.random.uniform(-1, 1, (h, w)).astype(np.float32)
        if density < 1:
            mask = np.random.random((h, w)) < density
            noise = noise * mask

    # Perlin fine - small smooth waves
    elif noise_type == 'perlin_fine':
        base_scale = max(8, int(16 / scale))
        small_h, small_w = max(2, h // base_scale), max(2, w // base_scale)
        noise = np.random.uniform(-1, 1, (small_h, small_w)).astype(np.float32)
        noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)
        blur_size = max(3, int(8 / scale)) | 1
        noise = cv2.GaussianBlur(noise, (blur_size, blur_size), 0)
        noise = noise * density

    # Perlin medium - medium smooth waves
    elif noise_type == 'perlin_medium':
        base_scale = max(16, int(32 / scale))
        small_h, small_w = max(2, h // base_scale), max(2, w // base_scale)
        noise = np.random.uniform(-1, 1, (small_h, small_w)).astype(np.float32)
        noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)
        blur_size = max(5, int(16 / scale)) | 1
        noise = cv2.GaussianBlur(noise, (blur_size, blur_size), 0)
        noise = noise * density

    # Perlin coarse - large smooth waves
    elif noise_type == 'perlin_coarse':
        base_scale = max(32, int(64 / scale))
        small_h, small_w = max(2, h // base_scale), max(2, w // base_scale)
        noise = np.random.uniform(-1, 1, (small_h, small_w)).astype(np.float32)
        noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_CUBIC)
        blur_size = max(11, int(32 / scale)) | 1
        noise = cv2.GaussianBlur(noise, (blur_size, blur_size), 0)
        noise = noise * density

    # Scanlines
    elif noise_type == 'scanlines':
        noise = np.zeros((h, w), dtype=np.float32)
        line_spacing = max(2, int(4 * scale))
        offset = int((frame_idx * speed) % line_spacing)
        for y in range(offset, h, line_spacing):
            line_intensity = np.random.uniform(0.5, 1.0) * density
            noise[y:y+1, :] = line_intensity
        noise = noise - 0.5  # center around 0

    else:
        return None

    # Normalize and scale by intensity
    noise = np.clip(noise, -1, 1) * intensity * 255

    return noise


def apply_noise_overlay(frame, noise):
    """Apply noise as an overlay to the frame."""
    if noise is None:
        return frame

    # Convert noise to 3 channels
    noise_3ch = np.stack([noise, noise, noise], axis=-1)

    # Add noise to frame
    result = frame.astype(np.float32) + noise_3ch
    result = np.clip(result, 0, 255).astype(np.uint8)

    return result


def apply_boil(frame, dx, dy, edge_weight_map, edge_blend):
    """Apply displacement weighted by edges."""
    h, w = frame.shape[:2]

    if edge_blend > 0:
        base_weight = 1.0 - edge_blend
        weight = base_weight + edge_blend * edge_weight_map
        dx_weighted = dx * weight
        dy_weighted = dy * weight
    else:
        dx_weighted = dx
        dy_weighted = dy

    grid_x, grid_y = np.meshgrid(
        np.arange(w, dtype=np.float32),
        np.arange(h, dtype=np.float32)
    )

    map_x = grid_x + dx_weighted
    map_y = grid_y + dy_weighted

    result = cv2.remap(
        frame,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    return result


def process_video_task(job_id, input_path, output_path, params):
    """Process video with line boil effect."""
    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            processing_status[job_id] = {'status': 'error', 'message': 'Cannot open video', 'progress': 0}
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)

        shift = params['shift']
        region = params['region']
        randomness = params['random']
        hold = params['hold']
        variations = params['variations']
        edge_weight = params['edge_weight']
        edge_sens = params['edge_sens']
        chunkiness = params.get('chunkiness', 0.7)
        wave_type = params.get('wave_type', 'noise')
        # Chromatic aberration
        ca_red = params.get('ca_red', 0)
        ca_green = params.get('ca_green', 0)
        ca_blue = params.get('ca_blue', 0)
        ca_blur = params.get('ca_blur', 0)
        # Noise
        noise_type = params.get('noise_type', 'none')
        noise_intensity = params.get('noise_intensity', 0)
        noise_size = params.get('noise_size', 1)
        noise_speed = params.get('noise_speed', 1)
        noise_random = params.get('noise_random', 1)

        boil_maps = generate_varied_displacements(height, width, region, shift, randomness, variations, chunkiness, wave_type, seed=42)

        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Apply line boil
            edge_map = detect_color_edges(frame, edge_sens)
            variation_idx = (frame_count // hold) % variations
            dx, dy = boil_maps[variation_idx]
            result = apply_boil(frame, dx, dy, edge_map, edge_weight)

            # Apply chromatic aberration
            result = apply_chromatic_aberration(result, ca_red, ca_green, ca_blue, ca_blur)

            # Apply noise overlay
            noise = generate_noise_frame(height, width, noise_type, noise_intensity, noise_size, noise_random, frame_count, noise_speed)
            result = apply_noise_overlay(result, noise)

            out.write(result)

            frame_count += 1
            progress = int((frame_count / total_frames) * 100)
            processing_status[job_id] = {
                'status': 'processing',
                'progress': progress,
                'message': f'Frame {frame_count}/{total_frames}'
            }

        cap.release()
        out.release()

        # Re-encode to H.264 for web compatibility + add audio
        processing_status[job_id]['message'] = 'Encoding for web...'

        temp_video = output_path
        final_output = output_path.replace('.mp4', '_final.mp4')

        try:
            # Use ffmpeg to re-encode to H.264 (web compatible) and add audio
            cmd = [
                FFMPEG_PATH or 'ffmpeg', '-y',
                '-i', temp_video,       # processed video (mp4v codec)
                '-i', input_path,       # original video (has audio)
                '-c:v', 'libx264',      # H.264 codec - web compatible
                '-preset', 'fast',
                '-crf', '18',           # high quality
                '-pix_fmt', 'yuv420p',  # compatibility
                '-c:a', 'aac',          # AAC audio
                '-b:a', '192k',
                '-map', '0:v:0',        # video from processed
                '-map', '1:a:0?',       # audio from original (optional)
                '-shortest',
                '-movflags', '+faststart',  # web streaming optimization
                final_output
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Replace temp with final
            os.remove(temp_video)
            os.rename(final_output, output_path)

        except subprocess.CalledProcessError as e:
            # If ffmpeg fails, try without audio
            try:
                cmd_no_audio = [
                    FFMPEG_PATH or 'ffmpeg', '-y',
                    '-i', temp_video,
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    final_output
                ]
                subprocess.run(cmd_no_audio, capture_output=True, check=True)
                os.remove(temp_video)
                os.rename(final_output, output_path)
            except:
                pass  # Keep original if all else fails
        except FileNotFoundError:
            # ffmpeg not installed - warn but keep video
            pass

        processing_status[job_id] = {
            'status': 'complete',
            'progress': 100,
            'message': 'Complete!',
            'output_path': output_path
        }

    except Exception as e:
        processing_status[job_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    upload_id = str(uuid.uuid4())
    original_filename = video.filename.lower()

    # Check if it's a GIF
    is_gif = original_filename.endswith('.gif')

    if is_gif:
        # Save GIF temporarily
        gif_path = os.path.join(UPLOAD_FOLDER, f"{upload_id}_input.gif")
        video.save(gif_path)

        # Convert GIF to video (loops to fill 5 seconds by default)
        input_path = os.path.join(UPLOAD_FOLDER, f"{upload_id}_input.mp4")
        try:
            total_frames, vid_width, vid_height, fps = convert_gif_to_video(
                gif_path, input_path, DEFAULT_GIF_DURATION
            )
        except Exception as e:
            os.remove(gif_path)
            return jsonify({'error': f'Failed to process GIF: {str(e)}'}), 400

        # Clean up original GIF
        os.remove(gif_path)
    else:
        # Regular video file
        input_filename = f"{upload_id}_input.mp4"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        video.save(input_path)

        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

    uploaded_videos[upload_id] = {
        'path': input_path,
        'total_frames': total_frames,
        'width': vid_width,
        'height': vid_height,
        'source_name': os.path.splitext(os.path.basename(video.filename))[0] or 'video'
    }

    return jsonify({
        'upload_id': upload_id,
        'total_frames': total_frames,
        'width': vid_width,
        'height': vid_height
    })


@app.route('/preview')
def preview():
    upload_id = request.args.get('upload_id')
    frame_num = int(request.args.get('frame', 0))
    shift = int(request.args.get('shift', 3))
    region = int(request.args.get('region', 6))
    randomness = float(request.args.get('random', 0.8))
    hold = int(request.args.get('hold', 2))
    variations = int(request.args.get('variations', 4))
    edge_weight = float(request.args.get('edge_weight', 0.6))
    edge_sens = float(request.args.get('edge_sens', 0.7))
    chunkiness = float(request.args.get('chunkiness', 0.7))
    wave_type = request.args.get('wave_type', 'noise')
    # Chromatic aberration params
    ca_red = int(request.args.get('ca_red', 0))
    ca_green = int(request.args.get('ca_green', 0))
    ca_blue = int(request.args.get('ca_blue', 0))
    ca_blur = int(request.args.get('ca_blur', 0))
    # Noise params
    noise_type = request.args.get('noise_type', 'none')
    noise_intensity = float(request.args.get('noise_intensity', 0))
    noise_size = float(request.args.get('noise_size', 1))
    noise_speed = float(request.args.get('noise_speed', 1))
    noise_random = float(request.args.get('noise_random', 1))

    if upload_id not in uploaded_videos:
        return jsonify({'error': 'Video not found'}), 404

    video_info = uploaded_videos[upload_id]
    cap = cv2.VideoCapture(video_info['path'])
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({'error': 'Cannot read frame'}), 400

    h, w = frame.shape[:2]

    # Apply line boil
    edge_map = detect_color_edges(frame, edge_sens)
    boil_maps = generate_varied_displacements(h, w, region, shift, randomness, variations, chunkiness, wave_type, seed=42)
    variation_idx = (frame_num // hold) % variations
    dx, dy = boil_maps[variation_idx]
    result = apply_boil(frame, dx, dy, edge_map, edge_weight)

    # Apply chromatic aberration
    result = apply_chromatic_aberration(result, ca_red, ca_green, ca_blue, ca_blur)

    # Apply noise overlay
    noise = generate_noise_frame(h, w, noise_type, noise_intensity, noise_size, noise_random, frame_num, noise_speed)
    result = apply_noise_overlay(result, noise)

    _, orig_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    _, effect_buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 85])

    return jsonify({
        'original': base64.b64encode(orig_buf).decode('utf-8'),
        'effect': base64.b64encode(effect_buf).decode('utf-8')
    })


@app.route('/preview_batch')
def preview_batch():
    """Return multiple processed frames for animated preview."""
    upload_id = request.args.get('upload_id')
    num_frames = int(request.args.get('num_frames', 30))
    shift = int(request.args.get('shift', 3))
    region = int(request.args.get('region', 6))
    randomness = float(request.args.get('random', 0.8))
    hold = int(request.args.get('hold', 2))
    variations = int(request.args.get('variations', 4))
    edge_weight = float(request.args.get('edge_weight', 0.6))
    edge_sens = float(request.args.get('edge_sens', 0.7))
    chunkiness = float(request.args.get('chunkiness', 0.7))
    wave_type = request.args.get('wave_type', 'noise')
    ca_red = int(request.args.get('ca_red', 0))
    ca_green = int(request.args.get('ca_green', 0))
    ca_blue = int(request.args.get('ca_blue', 0))
    ca_blur = int(request.args.get('ca_blur', 0))
    noise_type = request.args.get('noise_type', 'none')
    noise_intensity = float(request.args.get('noise_intensity', 0))
    noise_size = float(request.args.get('noise_size', 1))
    noise_speed = float(request.args.get('noise_speed', 1))
    noise_random = float(request.args.get('noise_random', 1))

    if upload_id not in uploaded_videos:
        return jsonify({'error': 'Video not found'}), 404

    video_info = uploaded_videos[upload_id]
    total_frames = video_info['total_frames']
    cap = cv2.VideoCapture(video_info['path'])

    if not cap.isOpened():
        return jsonify({'error': 'Cannot open video'}), 400

    fps = cap.get(cv2.CAP_PROP_FPS) or 24

    # Limit frames to what's available, loop if needed
    frames_to_fetch = min(num_frames, total_frames)

    # Read first frame to get dimensions and generate boil maps
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        return jsonify({'error': 'Cannot read frames'}), 400

    h, w = first_frame.shape[:2]
    boil_maps = generate_varied_displacements(h, w, region, shift, randomness, variations, chunkiness, wave_type, seed=42)

    original_frames = []
    effect_frames = []

    # Process first frame
    edge_map = detect_color_edges(first_frame, edge_sens)
    variation_idx = 0 // hold % variations
    dx, dy = boil_maps[variation_idx]
    result = apply_boil(first_frame, dx, dy, edge_map, edge_weight)
    result = apply_chromatic_aberration(result, ca_red, ca_green, ca_blue, ca_blur)
    noise = generate_noise_frame(h, w, noise_type, noise_intensity, noise_size, noise_random, 0, noise_speed)
    result = apply_noise_overlay(result, noise)

    _, orig_buf = cv2.imencode('.jpg', first_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    _, effect_buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 80])
    original_frames.append(base64.b64encode(orig_buf).decode('utf-8'))
    effect_frames.append(base64.b64encode(effect_buf).decode('utf-8'))

    # Process remaining frames
    for frame_idx in range(1, frames_to_fetch):
        # Loop back if we've reached the end
        actual_frame = frame_idx % total_frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, actual_frame)
        ret, frame = cap.read()
        if not ret:
            break

        edge_map = detect_color_edges(frame, edge_sens)
        variation_idx = (frame_idx // hold) % variations
        dx, dy = boil_maps[variation_idx]
        result = apply_boil(frame, dx, dy, edge_map, edge_weight)
        result = apply_chromatic_aberration(result, ca_red, ca_green, ca_blue, ca_blur)
        noise = generate_noise_frame(h, w, noise_type, noise_intensity, noise_size, noise_random, frame_idx, noise_speed)
        result = apply_noise_overlay(result, noise)

        _, orig_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        _, effect_buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 80])
        original_frames.append(base64.b64encode(orig_buf).decode('utf-8'))
        effect_frames.append(base64.b64encode(effect_buf).decode('utf-8'))

    cap.release()

    return jsonify({
        'original_frames': original_frames,
        'effect_frames': effect_frames,
        'fps': fps
    })


@app.route('/process', methods=['POST'])
def process():
    data = request.json
    upload_id = data.get('upload_id')

    if upload_id not in uploaded_videos:
        return jsonify({'error': 'Video not found'}), 404

    job_id = str(uuid.uuid4())
    video_info = uploaded_videos[upload_id]

    output_filename = f"{job_id}_lineboil.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    params = {
        'shift': int(data.get('shift', 3)),
        'region': int(data.get('region', 6)),
        'random': float(data.get('random', 0.8)),
        'hold': int(data.get('hold', 2)),
        'variations': int(data.get('variations', 4)),
        'edge_weight': float(data.get('edge_weight', 0.6)),
        'edge_sens': float(data.get('edge_sens', 0.7)),
        'chunkiness': float(data.get('chunkiness', 0.7)),
        'wave_type': data.get('wave_type', 'noise'),
        # Chromatic aberration
        'ca_red': int(data.get('ca_red', 0)),
        'ca_green': int(data.get('ca_green', 0)),
        'ca_blue': int(data.get('ca_blue', 0)),
        'ca_blur': int(data.get('ca_blur', 0)),
        # Noise
        'noise_type': data.get('noise_type', 'none'),
        'noise_intensity': float(data.get('noise_intensity', 0)),
        'noise_size': float(data.get('noise_size', 1)),
        'noise_speed': float(data.get('noise_speed', 1)),
        'noise_random': float(data.get('noise_random', 1))
    }

    processing_status[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'Starting...'
    }
    # Kept outside processing_status: process_video_task replaces that dict wholesale.
    job_save_names[job_id] = f"{sanitize_name(video_info.get('source_name', 'video'))}_boiled.mp4"

    thread = threading.Thread(
        target=process_video_task,
        args=(job_id, video_info['path'], output_path, params)
    )
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in processing_status:
        return jsonify({'status': 'error', 'message': 'Job not found', 'progress': 0})
    return jsonify(processing_status[job_id])


@app.route('/config')
def config():
    """Tells the front end which save path to use."""
    return jsonify({'desktop': DESKTOP_MODE})


def finished_job(job_id):
    """(output_path, save_name) for a completed job, or (None, error_message)."""
    if job_id not in processing_status:
        return None, 'Job not found'
    job = processing_status[job_id]
    if job.get('status') != 'complete':
        return None, 'Processing not complete'
    path = job.get('output_path')
    if not path or not os.path.exists(path):
        return None, 'Output file is missing'
    return path, job_save_names.get(job_id, 'boiled.mp4')


@app.route('/download/<job_id>')
def download(job_id):
    path, name = finished_job(job_id)
    if path is None:
        return name, 404 if name == 'Job not found' else 400

    # octet-stream, not video/mp4: a mp4 mimetype invites the browser (and any
    # embedded web view) to play the file inline instead of saving it.
    return send_file(
        path,
        as_attachment=True,
        download_name=name,
        mimetype='application/octet-stream',
    )


@app.route('/save/<job_id>', methods=['POST'])
def save(job_id):
    """Desktop fallback: copy the finished video into ~/Downloads."""
    path, name = finished_job(job_id)
    if path is None:
        return jsonify({'ok': False, 'error': name}), 400

    downloads = os.path.expanduser('~/Downloads')
    try:
        os.makedirs(downloads, exist_ok=True)
        dest = unique_path(downloads, name)
        shutil.copy2(path, dest)
    except OSError as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    return jsonify({'ok': True, 'path': dest})


def reveal_in_file_manager(path):
    """Select a file in the OS file manager. Returns False if unsupported."""
    system = platform.system()
    try:
        if system == 'Darwin':
            subprocess.run(['open', '-R', path], check=False)
        elif system == 'Windows':
            # explorer wants the argument glued to the switch, and it returns
            # a non-zero exit code even when it succeeds.
            subprocess.run(f'explorer /select,"{path}"', shell=True, check=False)
        else:
            # No portable "select the file" on Linux, so open the folder.
            subprocess.run(['xdg-open', os.path.dirname(path)], check=False)
        return True
    except OSError:
        return False


@app.route('/reveal', methods=['POST'])
def reveal():
    """Show a saved file in the OS file manager. Desktop only."""
    if not DESKTOP_MODE:
        return jsonify({'ok': False, 'error': 'not available'}), 400
    path = (request.json or {}).get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'ok': False, 'error': 'file missing'}), 400
    if not reveal_in_file_manager(path):
        return jsonify({'ok': False, 'error': 'could not open file manager'}), 500
    return jsonify({'ok': True})


if __name__ == '__main__':
    print("\n" + "="*50)
    print("ZohoBoil")
    print("="*50)
    print("\nOpen: http://localhost:5050\n")
    app.run(host='0.0.0.0', port=5050, debug=False)
