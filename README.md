# Line Boil

A desktop app that applies a hand-drawn "line boil" effect to video and GIFs — edge-aware displacement, chromatic aberration, and animated grain/noise overlays. Built with Python, OpenCV, Flask, and pywebview.

![screenshot placeholder](docs/screenshot.png)

## Features

- **Line boil**: edge-aware random displacement that mimics the wobble of hand-drawn animation
- **Edge detection**: LAB color-space edge weighting so boil concentrates on color transitions
- **Chromatic aberration**: per-channel RGB offset with optional blur
- **Noise overlays**: fine/medium/coarse grain, TV static, Perlin noise, scanlines
- **Live preview**: scrub frames or play animated preview while tweaking parameters
- **GIF support**: auto-converted to a loopable 5-second video on upload
- **Audio preserved**: ffmpeg re-encode keeps original audio track when available

## Install (macOS desktop app)

Download the latest `Boiler.app.zip` from [Releases](../../releases), unzip, and drag to Applications. First launch: right-click the app → Open (Gatekeeper warning, since the app is not code-signed).

## Run from source

Requires Python 3.11+ and (optionally) ffmpeg on PATH for H.264 output.

```bash
git clone https://github.com/princezoho/lineboil.git
cd lineboil
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option A: web mode (browser tab)
python3 app.py
# → open http://localhost:5050

# Option B: desktop mode (native window)
python3 desktop_app.py
```

## Build the desktop app yourself

```bash
source venv/bin/activate
pip install pyinstaller pywebview
pyinstaller Boiler.spec --noconfirm
# → dist/Boiler.app
```

## Project layout

```
app.py              # Flask server + all video processing
desktop_app.py      # pywebview wrapper for the desktop build
Boiler.spec         # PyInstaller config
requirements.txt    # opencv-python, numpy, scipy, flask, Pillow
```

## License

MIT — see [LICENSE](LICENSE).
