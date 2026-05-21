# bin/

Bundled native binaries shipped inside the Boiler `.app`.

## ffmpeg

- **Binary:** `ffmpeg` (macOS arm64)
- **Source:** [osxexperts.net](https://www.osxexperts.net/) — static build of FFmpeg 8.1
- **License:** FFmpeg is released under the **GNU LGPL 2.1+**, with some components under **GPL 2+** (this build includes GPL components, so the binary as a whole is GPL). See <https://ffmpeg.org/legal.html>.
- **How it's used:** Boiler invokes `ffmpeg` via `subprocess` to re-encode processed video to H.264 and copy the original audio track. The Boiler source code itself remains MIT-licensed; ffmpeg is distributed as a separate, unmodified binary alongside it ("mere aggregation").

If you redistribute Boiler with this binary, you must comply with FFmpeg's license — that means providing access to the corresponding source code (link to <https://ffmpeg.org/download.html> is sufficient for the official source).

To replace this binary with your own LGPL-only build, drop a different `ffmpeg` executable in this folder before running `pyinstaller Boiler.spec`.
