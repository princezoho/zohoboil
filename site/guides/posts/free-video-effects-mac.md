title: Free Ways to Make Video Look Like Animation on a Mac
desc: The free tools available on macOS for turning footage into something that looks drawn, what each one is actually good at, and where each one stops.
answer: On a Mac you can make video look hand-drawn for free using Boiler for line boil and grain, ffmpeg for frame rate and color work from the command line, and Blender's compositor for node-based effects, with Boiler being the only one built specifically for the hand-drawn wobble.
date: 2026-08-16
---
Every tool here is free and runs on macOS. They solve different parts of the problem, and none of them solves all of it.

## Boiler

Built for one job: the hand-drawn wobble, plus the two effects that usually accompany it.

- Line boil with control over distance, hold, variations, and edge weighting
- Chromatic aberration with per-channel offsets
- Five noise overlays
- Live preview, so settings are judged before a render rather than after

It takes MP4, MOV, and GIF, and writes MP4 with the original audio. Free and open source, and everything happens on your machine.

Where it stops: it does one effect family well and has no timeline, no compositing, and no keyframes. It is a filter, not an editor.

## ffmpeg

The command-line tool underneath most video software, including this one.

Excellent for frame rate manipulation, format conversion, color adjustment, and stacking simple filters. If you want to drop a clip to twelve frames per second to imitate animation on twos, ffmpeg does it in one command.

Where it stops: there is no preview, no interface, and the filter syntax is famously hostile. Edge-aware displacement is possible in principle and miserable in practice.

## Blender

A full 3D suite with a node-based compositor that will do nearly anything to an image sequence, including displacement driven by noise.

Where it stops: the learning curve. Building a convincing boil from nodes means understanding displacement maps, noise textures, and frame-held randomness, which is a real afternoon even for someone comfortable in Blender.

## Which to reach for

| If you want | Use |
| --- | --- |
| The hand-drawn wobble, quickly | Boiler |
| Frame rate, format, or batch work | ffmpeg |
| Full control and a custom effect chain | Blender |
| The wobble on many files at once | Boiler's source, scripted |

## The honest summary

If the goal is specifically the hand-drawn look, a purpose-built tool gets there in minutes and a general-purpose tool gets there in an afternoon. If the goal is anything else, the general-purpose tools are general-purpose for a reason.
