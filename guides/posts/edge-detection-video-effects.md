title: How Edge Detection Decides Where an Effect Lands
desc: Why edge-aware effects look deliberate and uniform ones look like a filter, how sensitivity changes what counts as an edge, and why noisy footage breaks it.
answer: Edge detection finds the places in a frame where colour changes sharply, and applying an effect only at those places is what separates a deliberate-looking treatment from a filter smeared over the whole image.
date: 2026-08-17
---
Two clips can use identical settings and land completely differently, because one applied the effect everywhere and the other applied it only where the drawing is.

## What an edge is, to software

An edge is a place where the value of neighbouring pixels changes quickly. Software finds them by measuring the rate of change across the frame in both directions, then keeping the places where that rate is above some threshold.

Everything that follows comes from one consequence: **noise is also a rapid change between neighbouring pixels.** Detectors cannot tell a real outline from a grainy patch, because at the pixel level they look the same.

## Why detecting on colour matters

The simplest detectors convert the frame to greyscale first, then look for changes in brightness. That is fast and it throws away real edges.

Two areas can have the same brightness and completely different colours. A mid-red next to a mid-green reads as a single flat grey once you discard hue, so the boundary between them vanishes and no effect gets applied along it. On flat-coloured animation, where large areas share tone but differ in hue, this failure is constant.

Measuring change across all three channels and combining the results catches those boundaries. It is more work per frame and it is the difference between an effect that follows every outline and one that skips half of them.

## Sensitivity, and what it trades

Sensitivity is the threshold: how much change is enough to count.

- **High sensitivity** catches soft, gradual transitions. It also catches compression blocking, grain, and gradients you did not think of as edges.
- **Low sensitivity** restricts the effect to hard outlines only. Cleaner, but a soft-focus source may end up with almost nothing detected.

The right value depends entirely on the footage, which is why judging it on a single frame first is worth the minute it takes.

## The noise trap

On grainy or heavily compressed footage, high sensitivity finds thousands of edges that are not in the image, only in its artifacts. The effect then decorates the noise.

The result is unmistakable once you know it: a shimmer that has no relationship to the shapes on screen, crawling across flat areas where nothing should be moving. It reads as a broken encode.

Two ways out. Lower the sensitivity until only real outlines survive. Or denoise before detecting, then add grain afterwards if you wanted grain, because grain laid on top is under your control and grain fed into a detector is not.

## Weighting, not switching

Edge detection does not have to be a yes or no decision. The useful version produces a map, where each pixel carries a strength rather than a flag, and the effect scales by that strength.

That gives a dial. At full weight, only the strongest edges move and flat interiors are perfectly still, which reads as redrawing. At low weight, everything moves somewhat, which reads as a warp of the whole image. The interesting settings are usually between, where outlines move a lot and interiors move a little, the way a redrawn cel does.

## The practical order

1. Look at one frame with the effect at an obvious strength, so you can see where it is landing.
2. Adjust sensitivity until the effect covers the outlines you care about and nothing else.
3. Then set the strength.

Doing it in the other order means tuning the amount of an effect while it is still landing in the wrong places.
