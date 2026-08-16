title: Every Line Boil Setting, Explained
desc: What Max Shift, Region Size, Randomness, Hold Frames, Variations, Edge Weight, Chunkiness, and Wave Type each change, with the range worth using for each.
answer: The six settings that matter in a line boil are Max Shift (how far edges move), Region Size (how large the moving areas are), Hold Frames (how long each drawing lasts), Variations (how many drawings cycle), Randomness (how uneven the movement is), and Edge Weight (how tightly the effect follows outlines).
date: 2026-08-16
---
Every line boil is the same idea with different numbers: push the edges off their true position, hold that push for a moment, then push them somewhere else. These are the numbers.

## Max Shift

The furthest a line can travel from where it actually sits, in pixels.

This is the volume knob. Everything else shapes the character of the movement, but this decides how much of it there is.

Useful range is 2 to 6. Remember it is measured in pixels, not as a percentage, so the same value is a much weaker effect on a larger frame.

## Region Size

How large each independently-moving area is.

Small regions mean the displacement changes rapidly across the frame, so a single long line can bend in several directions at once. Large regions move whole sections together, which reads as the entire drawing being redrawn slightly off rather than as a wobbly pen.

Small values produce chatter. Large values produce drift.

## Randomness

How much the strength of the movement varies between regions.

At 0 every region moves by the same amount, which is regular enough that the eye finds the pattern. At 1.0 some regions barely move while others take the full shift, which is closer to how an actual hand misses.

0.8 is a good default. It is uneven without being chaotic.

## Hold Frames

How many frames a single displacement stays on screen before it is replaced.

This is the most important setting after Max Shift, and the one most often left wrong. At 1, every frame gets a new displacement and the result buzzes like television static. At 2, you get the rhythm of animation drawn on twos.

| Hold | Effective drawing rate at 24fps |
| --- | --- |
| 1 | 24 drawings per second |
| 2 | 12 drawings per second |
| 3 | 8 drawings per second |
| 4 | 6 drawings per second |

## Variations

How many distinct displacements exist before the cycle repeats.

With 2, the image alternates between two states, a visible back-and-forth. It is the cheapest-looking option and occasionally the right one. With 4, the eye stops being able to predict the sequence. Above 6 there is little visible gain.

## Edge Weight

How much the effect concentrates on detected color edges rather than the whole frame.

Near 1.0, only outlines move and flat areas stay perfectly still, which is the faithful imitation of redrawing. Near 0, everything moves equally, which is a warp rather than a redraw and looks like heat rising off a road.

## Edge Sensitivity

How much of a color change counts as an edge.

Raise it to catch soft, low-contrast transitions. Lower it to restrict the effect to hard outlines only. On noisy footage, high sensitivity will find edges in the noise and boil the noise, which is rarely what anyone wants.

## Chunkiness

How sharply the displacement changes from one region to the next.

Low values blend smoothly between regions, so lines bend. High values snap between regions, so lines break into segments that shift as blocks. Chunky settings suit rough, scratchy artwork.

## Wave Type

The shape of the underlying displacement field.

Sine produces smooth, rounded wandering. Noise produces an irregular field with no discernible rhythm. Sine is the safer choice for anything that should look drawn by a person, since a person's hand moves in arcs.

## A note on how these interact

Max Shift and Region Size are not independent. A large shift inside a small region tears the line, because neighboring pixels get pulled in very different directions across a short distance. If lines start breaking apart, either reduce the shift or increase the region size.
