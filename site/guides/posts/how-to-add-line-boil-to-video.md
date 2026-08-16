title: How to Add Line Boil to a Video on a Mac
desc: A step-by-step method for adding a hand-drawn wobble to any video on macOS, including the settings to start from and the mistakes that make it look wrong.
answer: To add line boil to a video on a Mac, open the clip in Boiler, set Max Shift to 3 pixels and Hold Frames to 2, cycle 4 variations, then process and save the result as an MP4.
date: 2026-08-16
---
The whole job is four numbers and a preview. Here is the order that gets there fastest.

## 1. Start from a clip with clear edges

The effect works on outlines, so it shows up most on footage that has them: animation, line art, logos, high-contrast live action. A soft, low-contrast clip has little for the effect to grab, and the result will look like a mild blur instead of a redraw.

## 2. Set how far the lines wander

Max Shift is the distance in pixels a line can move from where it truly sits.

- 2 to 3 pixels reads as a hand that is trying to be neat
- 4 to 6 pixels reads as a rougher, faster drawing
- Above 8 pixels the shapes start to come apart

Shift scales with resolution. Three pixels on a 4K frame is a quarter the effect of three pixels on a 1080p frame, so a clip that looks right at one size needs a larger shift at a larger size.

## 3. Set how long each drawing is held

Hold Frames is how many frames pass before the wobble changes. This single number decides whether the result looks drawn or looks broken.

| Hold | Result at 24fps |
| --- | --- |
| 1 | Buzzes. Every frame is different, so it reads as noise |
| 2 | The classic look, matching animation drawn on twos |
| 3 to 4 | Slower, heavier, more deliberate |
| 6+ | You start to see individual drawings pop |

Start at 2.

## 4. Set how many drawings cycle

Variations is how many distinct wobbles exist before the sequence loops. Four is enough that the eye cannot find the pattern. Two is noticeably a back-and-forth, which is sometimes exactly what you want for a cheap, scrappy look.

## 5. Decide how tightly it hugs the edges

Edge Weight controls whether the wobble concentrates on detected color edges or ripples across the whole frame.

Push it toward 1.0 and only the outlines move, which is the honest imitation of redrawing. Lower it and the interior of shapes moves too, which turns into a heat-haze effect.

## A starting recipe

These settings are a calm, usable boil. Change one thing at a time from here.

| Setting | Value |
| --- | --- |
| Max Shift | 3 |
| Region Size | 6 |
| Randomness | 0.8 |
| Hold Frames | 2 |
| Variations | 4 |
| Edge Weight | 0.6 |
| Edge Sensitivity | 0.7 |
| Wave Type | Sine |

## 6. Check one frame before you commit

Processing a whole clip takes roughly a second per frame, so a thirty second clip is a few minutes. Judging settings on a single frame first saves most of that time.

## Three mistakes that give it away

- **Hold set to 1.** The most common error. It produces a shimmer that no hand ever made.
- **Shift too large for the resolution.** Lines detach from the shapes they belong to.
- **Applying it to everything.** Boil on an already-noisy clip fights the noise. It works best on clean sources.
