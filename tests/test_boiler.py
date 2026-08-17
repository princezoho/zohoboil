"""Tests for Boiler.

Run with: python -m pytest tests/ -v

These run on macOS, Windows and Linux. The point is not only that the effect
works, but that nothing in the pipeline assumes a platform, which is easy to
regress the moment someone writes a path or a shell command by hand.
"""
import io
import os
import platform
import subprocess
import sys
import time
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as boiler  # noqa: E402


@pytest.fixture(scope="session")
def clip(tmp_path_factory):
    """A tiny video with hard edges, which is what the boil acts on."""
    path = tmp_path_factory.mktemp("media") / "clip.mp4"
    ffmpeg = boiler.FFMPEG_PATH or "ffmpeg"
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc=size=160x120:rate=12:duration=1",
         "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )
    return str(path)


def test_ffmpeg_is_found():
    assert boiler.FFMPEG_PATH, "ffmpeg not found; the encode step cannot run"


def test_sanitize_name_strips_path_separators():
    assert "/" not in boiler.sanitize_name("a/b/c.mp4")
    assert "\\" not in boiler.sanitize_name("a\\b\\c.mp4")
    assert boiler.sanitize_name("") == "video"
    assert boiler.sanitize_name("...") == "video"
    assert len(boiler.sanitize_name("x" * 200)) <= 60


def test_unique_path_does_not_overwrite(tmp_path):
    first = boiler.unique_path(str(tmp_path), "clip.mp4")
    open(first, "w").close()
    second = boiler.unique_path(str(tmp_path), "clip.mp4")
    assert first != second
    assert not os.path.exists(second)


@pytest.mark.parametrize(
    "system,expected",
    [("Darwin", "open"), ("Windows", "explorer"), ("Linux", "xdg-open")],
)
def test_reveal_uses_the_right_command_per_platform(system, expected, tmp_path):
    target = tmp_path / "f.mp4"
    target.write_text("x")
    with mock.patch.object(platform, "system", return_value=system), \
         mock.patch.object(boiler.subprocess, "run") as run:
        assert boiler.reveal_in_file_manager(str(target))
    sent = run.call_args[0][0]
    assert expected in (sent if isinstance(sent, str) else " ".join(sent))


def test_boil_changes_the_frames_and_keeps_them_readable(clip, tmp_path):
    """The whole pipeline: decode, displace, re-encode, still playable."""
    import cv2

    out = str(tmp_path / "out.mp4")
    params = dict(
        shift=3, region=6, random=0.8, hold=2, variations=4,
        edge_weight=0.6, edge_sens=0.7, chunkiness=0.7, wave_type="sine",
        ca_red=0, ca_green=0, ca_blue=0, ca_blur=0,
        noise_type="none", noise_intensity=0, noise_size=1,
        noise_speed=1, noise_random=1,
    )
    boiler.process_video_task("job", clip, out, params)

    status = boiler.processing_status["job"]
    assert status["status"] == "complete", status
    assert os.path.getsize(out) > 0

    cap = cv2.VideoCapture(out)
    ok, frame = cap.read()
    cap.release()
    assert ok and frame is not None, "output is not decodable"

    cap = cv2.VideoCapture(clip)
    _, original = cap.read()
    cap.release()
    assert frame.shape == original.shape, "the boil must not resize the video"
    assert not (frame == original).all(), "the boil did not change anything"


def test_download_is_served_as_an_attachment(clip):
    """The bug that started all this: the browser must save, not play."""
    boiler.DESKTOP_MODE = False
    c = boiler.app.test_client()

    with open(clip, "rb") as f:
        data = {"video": (io.BytesIO(f.read()), "My Clip.mp4")}
    up = c.post("/upload", data=data, content_type="multipart/form-data").get_json()
    job = c.post("/process", json={"upload_id": up["upload_id"]}).get_json()["job_id"]

    for _ in range(600):
        status = c.get(f"/status/{job}").get_json()
        if status["status"] in ("complete", "error"):
            break
        time.sleep(0.2)
    assert status["status"] == "complete", status

    r = c.get(f"/download/{job}")
    assert r.status_code == 200
    assert r.headers["Content-Disposition"].startswith("attachment")
    # video/mp4 invites a web view to play the file inline instead of saving it.
    assert r.headers["Content-Type"] == "application/octet-stream"
    assert "My-Clip_boiled.mp4" in r.headers["Content-Disposition"]


def test_unknown_job_is_not_a_server_error():
    c = boiler.app.test_client()
    assert c.get("/download/nope").status_code == 404
    assert c.post("/save/nope").status_code == 400


def test_bundled_ffmpeg_is_rejected_when_it_cannot_run(tmp_path, monkeypatch):
    """A macOS binary must not be selected on Linux or Windows.

    bin/ffmpeg in this repo is arm64 macOS. Existence plus the executable bit
    is not enough to know it will run.
    """
    fake = tmp_path / "bin" / "ffmpeg"
    fake.parent.mkdir()
    fake.write_bytes(b"\xcf\xfa\xed\xfe not a binary for this platform")
    fake.chmod(0o755)

    monkeypatch.setattr(boiler.os.path, "dirname", lambda _p: str(tmp_path))
    monkeypatch.setattr(boiler.shutil, "which", lambda _n: "/usr/bin/ffmpeg-from-path")
    monkeypatch.setattr(boiler.os.path, "exists", lambda p: True)

    assert not boiler.ffmpeg_runs(str(fake))
    assert boiler.find_ffmpeg() == "/usr/bin/ffmpeg-from-path"
