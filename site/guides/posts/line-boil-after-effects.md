title: How to Make a Line Boil in After Effects
desc: The Turbulent Displace method for boiling lines in After Effects, why the default settings look wrong, and the one expression that fixes the frame rate.
answer: In After Effects, a line boil is made with Turbulent Displace set to a small amount and a large size, with the Evolution property driven by an expression that changes only every second or third frame instead of animating smoothly.
date: 2026-08-17
---
After Effects will do this, and the technique is worth understanding whether or not you use it, because it shows exactly what the effect is made of.

## The effect to reach for

**Turbulent Displace.** It generates a fractal noise field and pushes pixels around according to it, which is the whole mechanism of a line boil.

Starting points, for a 1080p comp:

| Property | Value | Why |
| --- | --- | --- |
| Displacement | Turbulent Smoother | Less tearing than the default |
| Amount | 8 to 15 | Roughly 2 to 4 pixels of actual movement |
| Size | 40 to 80 | Large regions drift; small regions chatter |
| Complexity | 1 | Higher values add detail you cannot see at this amount |

Note that Amount is not measured in pixels. A value of 10 at Size 60 moves edges a few pixels; the same Amount at Size 5 tears them apart. The two properties are not independent, which is the most common source of confusion with this effect.

## Why it looks wrong out of the box

Animate Evolution linearly and you get a smooth, continuous churn. It looks like the image is underwater.

Real animation does not churn. It changes, holds, changes again. Each drawing is a discrete event.

## The fix, which is one expression

Put this on Evolution:

```
hold = 2;
seed = 40;
Math.floor(time * (1 / thisComp.frameDuration) / hold) * seed
```

That takes the current frame, divides by how many frames you want to hold, floors it, and multiplies by an arbitrary step. The result is a value that jumps to a new number every second frame and sits perfectly still in between.

Change `hold` to 3 or 4 for a slower, heavier feel. The `seed` value only needs to be large enough that consecutive steps land on visibly different parts of the noise field; 40 works, so does 100.

Without the floor, you have a wobble. With it, you have a redraw. That single function is the difference.

## Two refinements

**Confine it to the edges.** Turbulent Displace hits the whole layer, so flat interiors move along with the outlines. Duplicate the layer, run Find Edges on the copy, blur it slightly, and use it as a luma matte on an adjustment layer holding the displace. Now only the lines move.

**Vary it across the frame.** A single displace applies one noise field to everything, so distant parts of the image move in a correlated way. Two instances at different Sizes, or a slight Offset animation, breaks that up.

## What it costs

Turbulent Displace with a matte is not cheap, and the edge-detection pass doubles the layer count. On a long sequence, expect to prerender.

This is also the honest reason a dedicated tool exists. The After Effects route gives you a boil inside a comp where you can composite it against everything else, which is the right call when the shot needs that. If you only want a clip boiled and exported, a pass with edge weighting, hold, and variation as four numbers is faster.

[Boiler](/) does exactly that pass, free and open source, and you can compare settings on a single frame before committing to a render. The After Effects method is better when the boil is one layer in a larger composite. Neither replaces the other.

## If you use another tool

The same three ingredients apply anywhere: a noise field, a displacement driven by it, and a step function on the noise so it changes on twos instead of continuously. In Blender it is a Displace node fed by a noise texture with a stepped Value node. In Nuke it is IDistort with a noise input. The names change; the floor function does not.
