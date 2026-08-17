title: How to Make a Convincing VHS Effect
desc: Tape did specific things to an image. Which artifacts matter, which are overused, and the order to apply them so the result reads as a recording rather than a filter.
answer: A convincing VHS look comes from horizontal color bleed, a red and blue channel offset of two or three pixels, soft focus, and a small amount of static, applied in that order, with the color signal degraded more than the brightness.
date: 2026-08-17
---
Most VHS filters fail in the same way. They add scanlines and heavy static and call it done, and the result looks like a screen, not a tape.

Tape did something specific, and it is worth knowing what.

## What VHS actually did to an image

VHS recorded brightness and color as separate signals with wildly different bandwidth. Luminance got about 3 MHz. Chrominance got around 0.4 MHz.

That single fact explains most of the look. **Color was recorded at roughly a tenth the horizontal detail of brightness.** Edges stayed reasonably crisp in black and white while color smeared sideways across them.

So the defining artifact is not static. It is color bleeding horizontally while the underlying image stays sharper than the color suggests.

## The artifacts, in order of how much they matter

**1. Horizontal color bleed.** Blur the color channels horizontally, several pixels wide, while leaving brightness alone. If your tool separates luma and chroma, blur chroma only, on the horizontal axis only. This is the one that sells it.

**2. Channel offset.** Two or three pixels of red and blue separation. Tape heads and the color-under encoding scheme left the color slightly displaced from the luminance it belonged to.

**3. Soft focus.** VHS was never sharp. A small overall blur, less than a pixel, before anything else.

**4. Noise, in the right places.** Tape noise is not TV static. It is fine, it sits mostly in the darker parts of the image, and it has a slight horizontal streak to it. Uniform white static across the whole frame is a broadcast artifact, not a tape one.

**5. Head switching noise.** The band of torn signal at the very bottom of the frame, a few lines tall, where the video head switched. Usually cropped off in playback, which is why it reads as authentic when present.

## What to leave out

**Scanlines.** These come from a CRT displaying the image, not from the tape storing it. If your footage is meant to look like a tape playing on a modern screen, scanlines are wrong. If it is meant to look like a tape playing on a CRT that someone filmed, they belong, and so does screen curvature and glow.

**Constant rolling and tracking errors.** A tape with continuous tracking problems is a broken tape. Real VHS was mostly stable, with occasional disruption. Intermittent is convincing; constant is a filter.

**Timecode burn-in and date stamps.** Fine if you want the camcorder look, but that is a different thing from a commercial tape, and mixing the two signals is a common error.

## Order of operations

| Order | Step | Reason |
| --- | --- | --- |
| 1 | Soften slightly | The lens and the tape were both soft; this happened first |
| 2 | Bleed the color horizontally | The recording stage |
| 3 | Offset red and blue | Also the recording stage |
| 4 | Add tape noise | Present in the signal as recorded |
| 5 | Crop or add head switching noise | The playback stage |

Anything imitating the display, if you want it, goes after all of this.

## Combining it with drawn footage

If the source is animation, boil the lines first. In the real chain the drawing existed before the camera, the camera before the tape, and the tape before the television. Reproducing that order keeps the effects from contaminating each other.

Skip that order and the giveaway is specific: a channel offset applied before a displacement gets dragged along by the displacement, so the color fringe follows the wobble instead of sitting square on the edge. It reads as a bad encode rather than a bad tape.

[Boiler](/) does the boil, the channel offsets with a blur on the split, and five kinds of noise overlay, in that order, in one pass. It is free and open source.
