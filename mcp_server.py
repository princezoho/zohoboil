#!/usr/bin/env python3
"""Boiler MCP server: line boil any video from an agent, no GUI.

Wraps the same processing the desktop app uses. Runs over stdio.

    ./venv/bin/python mcp_server.py
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2

import app as boiler
from mcp.server.mcpserver import Image, MCPServer

# The approved smooth-sine look, plus variations worth reaching for. Every
# preset is a complete parameter set so a caller never has to supply all 18.
PRESETS = {
    'default': dict(
        shift=3, region=6, random=0.8, hold=2, variations=4,
        edge_weight=0.6, edge_sens=0.7, chunkiness=0.7, wave_type='sine',
        ca_red=0, ca_green=0, ca_blue=0, ca_blur=0,
        noise_type='none', noise_intensity=0, noise_size=1,
        noise_speed=1, noise_random=1,
    ),
    'subtle': dict(
        shift=2, region=8, random=0.5, hold=3, variations=3,
        edge_weight=0.75, edge_sens=0.7, chunkiness=0.6, wave_type='sine',
        ca_red=0, ca_green=0, ca_blue=0, ca_blur=0,
        noise_type='none', noise_intensity=0, noise_size=1,
        noise_speed=1, noise_random=1,
    ),
    'heavy': dict(
        shift=6, region=6, random=1.0, hold=3, variations=2,
        edge_weight=0.6, edge_sens=0.7, chunkiness=0.7, wave_type='sine',
        ca_red=0, ca_green=0, ca_blue=0, ca_blur=0,
        noise_type='none', noise_intensity=0, noise_size=1,
        noise_speed=1, noise_random=1,
    ),
    'vhs': dict(
        shift=3, region=6, random=0.8, hold=2, variations=4,
        edge_weight=0.6, edge_sens=0.7, chunkiness=0.7, wave_type='sine',
        ca_red=3, ca_green=0, ca_blue=-3, ca_blur=1,
        noise_type='fine', noise_intensity=0.12, noise_size=1,
        noise_speed=1, noise_random=1,
    ),
}

PRESET_NOTES = {
    'default': 'The approved smooth sine boil. Start here.',
    'subtle': 'Barely-there shimmer that clings to edges. For live action.',
    'heavy': 'Wide wander held longer, only two drawings. Rough and hand-made.',
    'vhs': 'Default boil plus a red/blue channel split and fine grain.',
}

mcp = MCPServer(
    name='boiler',
    version='1.0.0',
    instructions=(
        'Applies a hand-drawn "line boil" wobble to video files on this machine. '
        'Use preview_boil to check settings on one frame before committing to '
        'boil_video, which re-encodes the whole clip and can take minutes.'
    ),
)


def resolve_params(preset, overrides):
    """Merge a preset with caller overrides, rejecting unknown keys."""
    if preset not in PRESETS:
        raise ValueError(
            f"unknown preset {preset!r}. Options: {', '.join(sorted(PRESETS))}"
        )
    params = dict(PRESETS[preset])
    for key, value in (overrides or {}).items():
        if key not in params:
            raise ValueError(
                f"unknown parameter {key!r}. Options: {', '.join(sorted(params))}"
            )
        params[key] = value
    return params


def check_input(path):
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        raise ValueError(f'no such file: {path}')
    return path


@mcp.tool(
    description=(
        'List the available boil presets and the parameters each one sets. '
        'Call this before guessing at parameter names.'
    )
)
def list_presets() -> dict:
    return {
        name: {'note': PRESET_NOTES[name], 'params': params}
        for name, params in PRESETS.items()
    }


@mcp.tool(
    description=(
        'Render a single boiled frame as a PNG so you can judge settings '
        'without processing the whole video. Fast, a second or two.'
    )
)
def preview_boil(
    input_path: str,
    frame: int = 0,
    preset: str = 'default',
    overrides: dict | None = None,
) -> Image:
    """Args:
    input_path: Video file to sample.
    frame: Frame number to render.
    preset: One of the names from list_presets.
    overrides: Individual parameters to change, e.g. {"shift": 6}.
    """
    path = check_input(input_path)
    p = resolve_params(preset, overrides)

    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
    ok, img = cap.read()
    cap.release()
    if not ok:
        raise ValueError(f'cannot read frame {frame} from {path}')

    h, w = img.shape[:2]
    edges = boiler.detect_color_edges(img, p['edge_sens'])
    maps = boiler.generate_varied_displacements(
        h, w, p['region'], p['shift'], p['random'],
        p['variations'], p['chunkiness'], p['wave_type'], seed=42,
    )
    dx, dy = maps[(frame // p['hold']) % p['variations']]
    out = boiler.apply_boil(img, dx, dy, edges, p['edge_weight'])
    out = boiler.apply_chromatic_aberration(
        out, p['ca_red'], p['ca_green'], p['ca_blue'], p['ca_blur'])
    noise = boiler.generate_noise_frame(
        h, w, p['noise_type'], p['noise_intensity'], p['noise_size'],
        p['noise_random'], frame, p['noise_speed'])
    out = boiler.apply_noise_overlay(out, noise)

    ok, buf = cv2.imencode('.png', out)
    if not ok:
        raise RuntimeError('failed to encode preview')
    return Image(data=buf.tobytes(), format='png')


@mcp.tool(
    description=(
        'Apply the line boil to an entire video and write a new file. '
        'Re-encodes to H.264 and keeps the original audio. This takes roughly '
        'a second per frame, so a 30 second clip runs a few minutes.'
    )
)
def boil_video(
    input_path: str,
    output_path: str | None = None,
    preset: str = 'default',
    overrides: dict | None = None,
) -> dict:
    """Args:
    input_path: Video file to boil.
    output_path: Where to write the result. Defaults to <input>_boiled.mp4
        beside the input.
    preset: One of the names from list_presets.
    overrides: Individual parameters to change, e.g. {"shift": 6}.
    """
    path = check_input(input_path)
    p = resolve_params(preset, overrides)

    if output_path:
        out_path = os.path.abspath(os.path.expanduser(output_path))
    else:
        stem, _ = os.path.splitext(path)
        out_path = f'{stem}_boiled.mp4'
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

    cap = cv2.VideoCapture(path)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if frames <= 0:
        raise ValueError(f'not a readable video: {path}')

    job = str(uuid.uuid4())
    # Synchronous by design: the caller wants the finished file, and a job
    # handle it has to poll would be a worse deal than simply waiting.
    boiler.process_video_task(job, path, out_path, p)

    status = boiler.processing_status.get(job, {})
    if status.get('status') != 'complete':
        raise RuntimeError(status.get('message', 'processing failed'))

    return {
        'output_path': out_path,
        'frames': frames,
        'size_bytes': os.path.getsize(out_path),
        'preset': preset,
        'params': p,
    }


if __name__ == '__main__':
    mcp.run(transport='stdio')
