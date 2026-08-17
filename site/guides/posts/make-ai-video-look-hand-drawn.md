title: How to Make AI-Generated Video Look Hand-Drawn
desc: Generated animation comes out too clean and too stable. The specific artifacts that give it away, and the passes that put a hand back into it.
answer: AI-generated animation looks synthetic mostly because its edges are perfectly stable frame to frame, so the fix is to add line boil, hold each drawing for two frames instead of one, and let the color sit slightly out of register.
date: 2026-08-17
---
Generated animation has a particular smell, and it is not usually the drawing. The drawing is often good. It is the motion.

A generated frame sequence interpolates. Every edge moves along a smooth path, arrives exactly where the math says, and never overshoots or wanders. Nothing in it was ever attempted twice.

Hand-drawn animation is the opposite. It is a stack of separate attempts at the same drawing, and the differences between attempts are what the eye reads as life.

## The four artifacts that give it away

**Edges that do not move.** In a hand-drawn cel, an outline that should be identical across two frames never is. In a generated sequence it often is, exactly, to the pixel. That stillness is the loudest tell.

**Everything on ones.** Generated output is one distinct image per frame, twenty-four a second. Traditional animation is usually twelve, each held twice. The extra smoothness reads as video, not drawing.

**Perfect color registration.** No physical process ever landed the color layers exactly on top of the line art. Generated frames do.

**Uniform texture.** Real footage has grain that crawls, and it sits on top of everything at once. Generated frames are clean, or carry a texture that was drawn into the image rather than laid over it.

## What to do, in order

### 1. Boil the lines

Displace the edges a few pixels off their true position, differently in different parts of the frame. This is the single highest-value pass. On a 1080p frame, start at 3 pixels and go up to 6 if the artwork is loose.

Keep it edge-weighted. If the displacement applies evenly to the whole image you get a heat shimmer, not a redraw. The wobble has to concentrate where the lines are.

### 2. Hold each drawing for two frames

This matters as much as the boil itself. If the displacement changes every frame, the result buzzes like static, because twenty-four changes a second is not a rate any hand ever worked at.

Hold for two and you land on twelve drawings a second, the rhythm of animation drawn on twos. The shimmer gets a pulse instead of a hiss.

### 3. Pull the color out of register

Offset red one way and blue the other by two or three pixels, leaving green alone. Green carries most of the perceived detail, so moving it softens the whole image while moving the other two only affects edges.

### 4. Lay grain over the top

Last, and less than feels right on a still frame. Grain that looks correct when paused is far too strong in motion.

## What not to do

**Do not drop the frame rate to fake the hold.** Exporting at 12fps throws away half your frames and makes camera moves stutter. Holding the *effect* for two frames while the video stays at 24 gives the drawn rhythm without wrecking the motion.

**Do not add a paper texture.** Animation cels were photographed, not printed on paper. It is the most common shortcut and the least convincing one.

**Do not stack every effect at maximum.** The goal is a frame that looks like it passed through a physical process, not one that looks like it passed through six filters.

## Why this works

None of this adds information. It removes certainty.

A perfectly stable edge tells the viewer that no hand was involved, because no hand can do that. Reintroducing a small, structured error puts the hand back, and the eye stops asking questions about it.

The error has to be structured, though. Random noise per frame reads as a broken encode. Displacement that follows the edges, held for a beat, cycling through a few variations, reads as drawing.
