title: What Is Line Boil in Animation?
desc: Line boil is the shimmer you see in hand-drawn animation, caused by every frame being drawn slightly differently. Where it comes from, why it reads as alive, and how to add it to digital video.
answer: Line boil is the constant shimmer along the outlines in hand-drawn animation, caused by an artist redrawing every frame slightly differently so no line ever lands in exactly the same place twice.
date: 2026-08-16
---
Watch any hand-inked cartoon and hold your eye on a single outline. It will not sit still. It creeps, swells a hair, drifts a pixel or two and comes back. Animators call this boiling lines, or line boil.

It is not a technique anyone set out to invent. It is a byproduct of the work. An artist drawing twenty-four pictures for one second of film cannot place every line in exactly the same spot twenty-four times, so the edges wander. The eye reads that wandering as the presence of a hand.

## Why the wobble reads as alive

A digital shape is the same shape in frame 1 and frame 400. It is mathematically stable, and stability is exactly what makes it feel manufactured. There is no evidence of a person in it.

A hand-drawn shape carries a record of the effort it took. Every frame is a fresh attempt at the same drawing, and every attempt misses slightly. That miss is the signature.

> Line boil is what an error looks like when it happens twenty-four times a second on purpose.

## Boil is not the same as shake

Camera shake moves the whole frame. Boil moves the edges inside a frame that is otherwise still. That distinction matters, because faking boil with a jitter on the whole clip produces something that reads as a bad tripod rather than as a drawing.

The wobble has to happen at the level of the line, and it has to be different in different parts of the frame at the same time.

## The three numbers that define a boil

Any convincing boil comes down to three decisions.

| Decision | What it controls |
| --- | --- |
| How far | The distance a line can wander from its true position, usually 2 to 6 pixels |
| How long | How many frames a single drawing is held before it changes |
| How many | How many distinct drawings cycle before the sequence repeats |

Hold is the one people get wrong. If every frame gets a fresh wobble, the result buzzes like static. Real animation is often drawn on twos, meaning each drawing is held for two frames of a twenty-four frame second, which is why the shimmer has a visible rhythm instead of a hiss.

## Adding it to footage that never had it

The effect can be applied after the fact. The method is to detect the edges in each frame, displace those edges by a small random amount, hold that displacement for a few frames, then swap to a different one.

Because the displacement follows detected edges, flat areas stay put and only the outlines move, which is what separates it from a general warp of the whole image.

Boiler does this on a Mac with a few sliders. Drop in an MP4, MOV, or GIF, set how far and how long, and export an MP4 with the original audio.
