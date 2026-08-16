title: Chromatic Aberration in Video, and How to Fake It Well
desc: What chromatic aberration actually is, why it shows up in old film and comics, and how to add it to video without it looking like a broken 3D movie.
answer: Chromatic aberration is the colored fringing that appears when a lens or a printing process fails to land the red, green, and blue components of an image in exactly the same place, and it is faked in video by offsetting the color channels two or three pixels apart.
date: 2026-08-16
---
Hold a cheap magnifying glass up to a black line on white paper and look at the edge. You will see a thin band of color, usually orange on one side and blue on the other. The glass bends different wavelengths by different amounts, so the colors land in slightly different places.

That is chromatic aberration. Every lens has some. Cheap lenses have a lot.

## Two different origins, one look

The effect shows up from two unrelated failures, which is why it reads as authentic to so many different eras.

**Lenses.** Glass refracts short wavelengths more than long ones. Blue focuses slightly nearer the lens than red, so a white edge grows colored fringes, strongest toward the corners of the frame.

**Printing.** Color comics and film prints laid down each color as a separate pass. If the paper shifted a fraction of a millimeter between passes, the layers misregistered and every edge got a colored ghost.

Both produce fringing on high-contrast edges. Neither produces it in the middle of a flat area, which is the first thing that gives away a bad fake.

## How to fake it

Offset the color channels relative to each other. Move red a couple of pixels one way, blue the same distance the other way, leave green where it is.

Green stays put because human vision draws most of its detail from the green channel. Displace green and the whole image goes soft. Displace red and blue around a fixed green and the image stays sharp while the edges pick up color.

## Getting the amount right

| Offset | Reads as |
| --- | --- |
| 1 to 2 px | A decent lens. Barely conscious, adds warmth |
| 3 to 4 px | Old film, cheap glass, printed comic |
| 5 to 8 px | Damaged, degraded, deliberate |
| 10+ px | A 3D movie without the glasses |

Nearly every overdone version of this effect is overdone in the same way: the offset is too large and it is applied evenly across the frame.

## The detail most fakes miss

Real lens aberration is not uniform. It is near zero at the center of the frame and increases toward the corners, because that is where light passes through the most curved part of the glass.

An even offset across the whole image is really imitating a printing misregistration rather than a lens. Both are legitimate looks, but they belong to different stories, and mixing them with a heavy vignette produces something that claims to be a lens while behaving like a printing press.

## Add a little blur to the offset channels

A real fringe is not a crisp duplicate of the edge in a different color. It is slightly soft, because the misfocused wavelength is, by definition, out of focus.

A blur of a pixel or so on the offset channels is the difference between a fringe that looks optical and one that looks like a layer was nudged in an editor.

## Order of operations

Apply the channel split after any line work and before any grain. In the physical chain it is imitating, the drawing came first, the lens or press came second, and the film stock came last. Reproducing that order keeps the effects from contaminating each other.

Boiler applies chromatic aberration in this order automatically, with separate red, green, and blue offsets plus a blur on the split.
