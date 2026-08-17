title: Why Generated Video Looks Uncanny Even When Each Frame Looks Fine
desc: Pause a generated clip and it holds up. Play it and something is wrong. The reason is in the motion, not the images, and it is specific.
answer: Generated video looks uncanny because each frame is produced independently or interpolated smoothly, so surfaces drift and edges hold perfectly still in ways no camera or hand ever produced, and the eye reads that inconsistency as motion rather than as image quality.
date: 2026-08-17
---
Take a still from a generated clip. It usually survives inspection. Composition, lighting, detail, all plausible.

Play the clip and something is wrong within a second, and most people cannot say what. They reach for words like plastic, floaty, dreamlike.

The images are not the problem. The relationship between them is.

## The eye is a motion instrument first

Human vision devotes enormous resources to change over time. Detecting that something moved, and how, runs earlier and faster than working out what the thing is.

That means a viewer evaluates temporal consistency before they consciously evaluate a picture. A sequence can be made of individually excellent frames and still fail, because it is being judged on a channel the frames were never optimised for.

## The four specific failures

**Surfaces that drift.** A brick wall in real footage keeps the same bricks. In generated footage the texture often reorganises slightly from frame to frame: detail appears, migrates, dissolves. Each frame has plausible bricks. They are not the same bricks.

**Edges that are too stable.** The opposite failure, and just as telling. Where an outline should shift by a pixel from natural camera movement or a redrawn line, it sits exactly still. Perfect stability is not something a physical process produces.

**Motion without weight.** Real movement obeys mass. Things accelerate, overshoot, settle. Interpolated movement travels a smooth path at an even rate and arrives exactly, with no overshoot and no settle. It looks like an object being carried by something invisible.

**Identity that slips.** Over a few seconds a face subtly becomes a slightly different face. Any single pair of adjacent frames looks continuous. Frame one and frame ninety do not match.

## Why this is a harder problem than image quality

Improving a single frame is a well-defined target. Consistency across frames is a constraint between outputs, and the number of pairs to keep consistent grows with the length of the clip.

Which is why generated video improved in resolution and detail faster than it improved in coherence, and why a longer clip degrades in a way a longer still image cannot.

## What can be done in post

You cannot repair drifting texture or slipping identity after the fact. Those need a different generation.

But the stability problem is fixable, and it is often the dominant tell in animated content.

Adding a structured wobble to the edges, holding each variation for a couple of frames, and cycling through a handful of them reintroduces the frame-to-frame variation that a hand produces and a model does not. It does not add information. It removes the impossible perfection.

There is a real risk of talking yourself into this as a cure-all. It is not. It addresses one artifact. If the clip also has drifting surfaces and weightless motion, a boil on top will make it look like drifting, weightless animation.

## The useful test

Play a clip and watch one small feature, not the whole frame. A button. A single brick. The corner of a mouth.

If it stays itself for the length of the shot, the sequence is coherent. If it quietly becomes a different button, no amount of post will fix it, and no viewer will be able to tell you that is what bothered them.
