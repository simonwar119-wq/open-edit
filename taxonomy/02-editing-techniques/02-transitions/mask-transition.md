---
name: mask-transition
description: |-
  A transition where one shot is revealed through a traveling matte or geometric shape that moves across the frame, creating a wipe-like effect with custom shapes, logos, or organic forms.
category: transition
complexity: high
requires_audio: false
ffmpeg_available: true
source:
  origin: "Classical optical printing (1920s–1950s); modernized via digital compositing in After Effects (1990s–present)"
  first_documented: "Optical wipes in early cinema; formalized as digital mask transitions in Adobe After Effects (1993)"
last_updated: 2026-05-13
---

## Definition

A **mask transition** — also called **wipe transition**, **shape transition**, or **traveling matte transition** — uses a moving mask or matte to reveal the next shot. Unlike a cross-dissolve where the entire image fades uniformly, a mask transition reveals clip B through a boundary that sweeps, grows, shrinks, or morphs across the frame. The mask can be:

- **Geometric**: A circle expanding from center (iris wipe), a line sweeping across (linear wipe), a square contracting to a point
- **Organic**: A paint splash, a liquid drip, a smoke puff, a leaf vein pattern
- **Content-driven**: A moving element in the footage itself — a passing car, a closing door, a character walking past the camera — serves as the mask boundary
- **Logo/brand**: The brand emblem dissolves into a mask that reveals the next shot (common in commercial editing)

The editorial function of mask transitions is fundamentally **creative punctuation**. They are not invisible — they are meant to be noticed and appreciated. They signal:

1. **Stylistic intent**: The editor is calling attention to the transition as a creative choice
2. **Genre markers**: Wipe transitions are strongly associated with Star Wars (1977) and George Lucas's serialized storytelling
3. **Brand integration**: Custom-shaped wipes using the brand logo make the transition itself a branding moment
4. **Visual rhythm**: The speed and shape of the mask boundary controls how the viewer's eye moves across the frame

Mask transitions occupy the high end of the "visibility" spectrum — they are the most attention-seeking of all transitions and should be used deliberately, not as default.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `duration_s` | float | 0.2 to 2.0 | 0.6 | Time for the mask to fully traverse the frame. |
| `mask_shape` | enum | `circle` / `square` / `diamond` / `heart` / `star` / `custom` / `organic` | `circle` | The shape of the reveal boundary. Custom = user-supplied alpha mask. |
| `mask_edge_feather` | float | 0.0 to 0.5 | 0.05 | Feather/softness of the mask edge. 0 = hard edge, 0.5 = very soft. |
| `direction` | enum | `center-out` / `left-right` / `top-bottom` / `diagonal` / `random` | `center-out` | Direction of the mask sweep. Center-out = expanding circle/iris wipe. |
| `source_footage_mask` | boolean | true / false | false | Whether the mask boundary is driven by a moving element in the source footage (e.g., passing object). |
| `invert` | boolean | true / false | false | Invert the mask: reveal by shrinking instead of expanding, etc. |
| `audio_sync` | enum | `none` / `beat` / `swish` | `none` | Whether to sync the mask motion to audio (beat of music or a custom swish SFX). |

## Usage Scenarios

- **Brand logo reveal (Nike / brand content)**: The Nike swoosh starts as a solid shape, then its boundary becomes the mask edge that reveals the next shot. The swoosh dissolves inward as the new scene emerges. This is a signature technique in sportswear advertising.

- **Passing-object wipe (Qmike travel)**: In a travel vlog, a person walks past the camera (creating a dark silhouette that crosses frame-left to frame-right). The editor uses this passing silhouette as the mask boundary: as the person exits frame-right, the next location is revealed. This creates a natural, in-camera mask transition.

- **Circular iris wipe (narrative / vintage aesthetic)**: A classic iris wipe (circle closing in on a subject, or expanding from a point) signals a deliberate stylistic choice — often used for period pieces, Star Wars homages, or narrative epilogues.

- **Shape-morph transitions (music videos / creative content)**: A heart shape floats over the frame and expands, revealing the next shot. Or a series of geometric shapes (squares, triangles) tile across the frame in a grid reveal.

- **Particle/dissolve mask (Apple "Snowbrawl")**: The snow particles in the snowy environment could theoretically serve as mask elements — as snowflakes cluster and disperse, the transition between shots is masked by the snow particles themselves.

## Source Examples

| Source | Usage | Mask Type |
|--------|-------|-----------|
| **Nike "You Can't Stop Us" (2020)** | Minimal mask transitions — primarily uses hard cuts and split-screen matches. If present, geometric wipes at section transitions. | Geometric / brand |
| **Star Wars (1977, Lucas)** | The definitive cultural reference — all scene transitions use iris wipe masks (closing to center, then opening) | Circle iris wipe |
| **Qmike样片** | Occasional passing-object wipes (subject walks past camera, revealing next location) | Source footage mask |
| **Music videos (general)** | Heavy use of custom-shape masks — logos, hearts, stars, geometric tile reveals | Custom / geometric |
| **Apple "Snowbrawl"** | No mask transitions are central to this ad — consistent with the "shot-on-iPhone" naturalistic approach | N/A |

## Related Techniques

- [cross-dissolve](cross-dissolve.md) — The uniform alternative; mask transitions can be thought of as a "shaped dissolve"
- [light-leak-transition](light-leak-transition.md) — Another creative overlay transition, using light flares instead of shapes
- [whip-pan](whip-pan.md) — Like mask transitions, whip pans are visible transition effects, but driven by camera motion rather than shape boundaries
- [splitscreen-match-cut](../01-cuts/splitscreen-match-cut.md) — Uses a hard vertical line across the frame, which functions like a static mask boundary

## FFmpeg Notes

FFmpeg supports mask transitions through the `gebox` / `geq` filters for geometric masks, or via external alpha mask videos for custom shapes.

**Circle iris wipe (center-out):**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:v]format=rgba,setpts=PTS-STARTPTS[v0]; \
    [1:v]format=rgba,setpts=PTS-STARTPTS[v1]; \
    [v0][v1]blend=all_expr='if(gte(sqrt((X-W/2)^2+(Y-H/2)^2), \
        (W/2)*(T/0.6)),A,B)':shortest=1[vout]" \
  -map "[vout]" output.mp4
```

**Left-to-right linear wipe:**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:v]format=rgba,setpts=PTS-STARTPTS[v0]; \
    [1:v]format=rgba,setpts=PTS-STARTPTS[v1]; \
    [v0][v1]blend=all_expr='if(lte(X, W*T/0.6),B,A)':shortest=1[vout]" \
  -map "[vout]" output.mp4
```

**Using an external alpha mask video:**

```bash
# mask.png is a white shape on black background
# The mask animates (expands/sweeps) and drives the transition
ffmpeg -i clipA.mp4 -i clipB.mp4 -i mask_movement.mp4 \
  -filter_complex "\
    [0:v][2:v]alphamerge[va]; \
    [1:v][2:v]alphamerge[vb]; \
    [va][vb]overlay[vout]" \
  -map "[vout]" output.mp4
```

**Note:** Tested with FFmpeg 7.0+. For complex animated masks (organic shapes, particle reveals, branded logos), use After Effects or DaVinci Resolve Fusion — the full creative flexibility of mask transitions is better served by a compositor than by FFmpeg filter graphs.
