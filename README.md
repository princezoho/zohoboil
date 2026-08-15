# Boiler

> A Mac app that gives video the wobbling line of hand-drawn animation. Drop a clip in, move a few sliders, save it out.

**[boiler.jejestudios.com](https://boiler.jejestudios.com)**

![The Boiler window: preview on the left, line boil sliders on the right.](docs/screenshot.png)

---

## Download

**[Download Boiler 1.0.0 for Mac](https://github.com/princezoho/zohoboil/releases/latest/download/Boiler-1.0.0.dmg)** (106 MB)

Open the DMG, drag Boiler into Applications, open it. The app is signed and
notarized by Apple, so it opens on a double-click with no security warning.

Requires macOS 12 or later on Apple Silicon. Intel Macs are not supported yet.

No Python, no Terminal, no Homebrew. ffmpeg ships inside the app, and your
video never leaves your machine.

---

## What it does

In hand-drawn animation, lines "boil": every frame is redrawn by hand and never
quite matches the last one, so edges shimmer and crawl. Digital video has none
of that. Boiler puts it back.

- **The boil.** Wobble that follows the edges in the frame, from a faint shimmer
  to a full tremor. Choose how far edges wander, how big the wobbling regions
  are, and how many frames each drawing is held before it shifts.
- **Chromatic aberration.** Offset the red, green, and blue channels, with a
  blur for softness, for old film and worn tape.
- **Noise overlays.** Fine grain, coarse grain, TV static, Perlin, scanlines.
- **Live preview.** Scrub a single frame or play the loop while you work. Move a
  slider and the preview refreshes.
- **Video or GIF in, MP4 out.** Original audio is preserved.

---

## Walkthrough

**1. Drop a video in.** Drag an `.mp4`, `.mov`, or `.gif` onto the dashed box in
the top left. The original sits on top, the boiled version below it.

**2. Set the wobble.** Under **Line Boil Settings**:

| Slider | What it does |
| --- | --- |
| Max Shift | How many pixels each edge can wander |
| Region Size | How big the wobbling chunks are |
| Randomness | Variation in wobble strength |
| Hold Frames | How long each drawing is held before the boil shifts |
| Variations | How many distinct boil positions cycle through |

**3. Focus the edges.** Under **Edge Detection**, push *Edge Weight* toward 1.0
to make the boil cling to color edges only. Lower it for a uniform ripple across
the whole frame.

**4. Add color split and grain.** The right panel has **Chromatic Aberration**
and **Noise Overlay**.

**5. Preview.** Click **▶ Live Preview** to see it animated.

**6. Export.** Click **Process Video**, then **Download Result**. Pick a folder
and the file lands there, named after your clip.

### A good starting point

These settings are a calm, usable boil. Start here and push from there.

| Setting | Value |
| --- | --- |
| Max Shift | 3 |
| Region Size | 6 |
| Randomness | 0.8 |
| Hold Frames | 2 |
| Variations | 4 |
| Edge Weight | 0.6 |
| Edge Sensitivity | 0.7 |
| Chunkiness | 0.7 |
| Wave Type | Sine |

---

## MCP server

Boiler ships an MCP server, so an AI agent can boil video without the GUI. It
exposes three tools:

| Tool | What it does |
| --- | --- |
| `list_presets` | The available looks and every parameter each one sets |
| `preview_boil` | Renders one boiled frame as a PNG, in about a second |
| `boil_video` | Boils a whole clip and writes an MP4, audio intact |

Presets are `default` (the smooth sine boil), `subtle`, `heavy`, and `vhs`. Any
individual parameter can be overridden:

```json
{ "input_path": "~/Desktop/clip.mp4", "preset": "vhs", "overrides": { "shift": 6 } }
```

Add it to Claude Code:

```bash
claude mcp add boiler --scope user -- \
  /path/to/zohoboil/venv/bin/python /path/to/zohoboil/mcp_server.py
```

Or in any MCP client's config:

```json
{
  "mcpServers": {
    "boiler": {
      "command": "/path/to/zohoboil/venv/bin/python",
      "args": ["/path/to/zohoboil/mcp_server.py"]
    }
  }
}
```

Check settings with `preview_boil` before calling `boil_video`. A full boil runs
about a second per frame, so a 30 second clip takes a few minutes.

---

## Build from source

You need this only to modify the code or compile the app yourself. Requires
Python 3.11+.

```bash
git clone https://github.com/princezoho/zohoboil.git
cd zohoboil
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 app.py           # web mode, http://localhost:5050
python3 desktop_app.py   # native window
```

To build the app bundle and a DMG:

```bash
pip install pyinstaller pywebview
./build_dmg.sh 1.0.0
```

That produces `dist/Boiler.app` and an unnotarized `dist/Boiler-1.0.0.dmg`,
signed with a Developer ID if one is in your keychain and ad-hoc otherwise.

To notarize, staple the ticket to the app first, then repackage. Stapling the
app before it goes in the DMG is what lets Gatekeeper clear it offline:

```bash
export ASC_KEY_ID=...  ASC_ISSUER=...
xcrun notarytool submit dist/Boiler-1.0.0.dmg \
  --key ~/.appstoreconnect/private_keys/AuthKey_$ASC_KEY_ID.p8 \
  --key-id "$ASC_KEY_ID" --issuer "$ASC_ISSUER" --wait
xcrun stapler staple dist/Boiler.app
./package_dmg.sh 1.0.0
```

### Project layout

```
app.py            Flask server and all video processing
mcp_server.py     MCP server exposing the boil as agent tools
desktop_app.py    pywebview wrapper for the desktop build
Boiler.spec       PyInstaller build config
build_dmg.sh      Builds the .app and a DMG
package_dmg.sh    Wraps a stapled .app into a notarized DMG
bin/ffmpeg        Bundled ffmpeg binary (arm64)
site/             The boiler.jejestudios.com landing page
docs/             Screenshots and release notes
```

---

## License

[MIT](LICENSE). Do whatever you want, just keep the copyright notice.

The bundled `ffmpeg` binary is distributed under the GNU GPL 2+ (see
[`bin/README.md`](bin/README.md)). The Boiler source stays MIT.

---

Built by [Jeje Studios](https://www.jejestudios.com).
