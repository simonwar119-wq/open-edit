---
name: speed-ramp
description: |-
  A dynamic speed change applied to a clip — typically slowing to normal or ramping up to fast — used at transition points to emphasize impact moments, compress downtime, or sync action to music.
category: transition
complexity: medium
requires_audio: true
ffmpeg_available: true
source:
  origin: "Pioneered in 1990s action cinema (The Matrix, 1999); widespread adoption in sports and action advertising through the 2000s"
  first_documented: "The Matrix (1999) — 'bullet time' variant; popularized in advertising by Nike and Apple (2000s)"
last_updated: 2026-05-13
example_videos:
  - url: "https://www.youtube.com/watch?v=85bb-oveozc"
    duration: "2:40"
    title: "My SECRET To Smooth Speed Ramp Transitions"
  - url: "https://www.youtube.com/watch?v=W8T_MEmvQDA"
    duration: "0:14"
    title: "SPEED RAMPING IN 2024"
---

## Definition

A **speed ramp** — also called **time remapping** or **time-ramp transition** — is a technique where the playback speed of a video clip changes non-uniformly at or near a transition point. The most common pattern is:

1. **Normal speed** → **fast/slow** leading into the cut → **cut** → **fast/slow exiting the cut** → **normal speed**

The speed change can go in either direction:
- **Slow → Fast**: A slow-motion moment snap-ramps to real-time or fast-forward, often used to land a punchline or impact point
- **Fast → Slow**: A fast action sequence decelerates into slow motion for dramatic emphasis, typically landing on a key visual moment

Speed ramps serve three primary editorial functions:

1. **Emphasis**: Slowing down at the exact moment of highest visual interest (a ball hitting a racket, a snowball impact, a dancer's peak extension)
2. **Pacing**: Fast-forwarding through less interesting sections (setup shots, transitions between locations) to maintain energy
3. **Beat-sync**: Aligning speed changes with musical downbeats or lyrical accents, creating a choreographed relationship between audio and visual

The transition aspect of a speed ramp is that the **speed change itself** — not a dissolve or a wipe — bridges the gap between two clips. The viewer feels the transition through the velocity shift rather than seeing a traditional transition effect.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `pre_ramp_duration_s` | float | 0.1 to 2.0 | 0.4 | Duration of speed change leading into the cut point (from clip A's end). |
| `post_ramp_duration_s` | float | 0.1 to 2.0 | 0.4 | Duration of speed change exiting the cut point (from clip B's start). |
| `pre_ramp_speed` | float | 0.1 to 10.0 | 2.0 | Speed multiplier at the end of clip A. <1 = slow motion, >1 = fast motion. |
| `post_ramp_speed` | float | 0.1 to 10.0 | 2.0 | Speed multiplier at the start of clip B. <1 = slow motion, >1 = fast motion. |
| `ramp_curve` | enum | `linear` / `ease-in` / `ease-out` / `s-curve` / `sudden` | `s-curve` | Acceleration curve of the speed change. Sudden = instant flip from slow to fast. |
| `motion_blur` | boolean | true / false | true | Whether to add motion blur during fast segments to simulate realistic speed. |
| `frame_blending` | enum | `none` / `blend` / `optical-flow` | `blend` | Interpolation method for slow-motion segments. Optical flow gives smoothest results. |

## Usage Scenarios

- **Impact emphasis (Apple "Snowbrawl")**: A snowball is thrown at normal speed, then the video ramps into slow motion just before impact, showing the snowball's trajectory and the expression on the target's face. After impact, the speed ramps back to normal for the next action beat. Each ramp is synced to the soundtrack's percussion.

- **Action-to-action transitions (Nike "You Can't Stop Us")**: A soccer player's kick starts in slow motion, then speed-ramps to fast-forward as the ball crosses the split-screen seam into the next athlete's scene. The speed change masks the transition and maintains kinetic energy.

- **Setup compression (Qmike travel/lifestyle)**: A travel vlog shows the subject walking to a destination at 2x speed (ramped down from normal), then decays to real-time as they arrive at the scenic viewpoint. The speed ramp compresses the boring walking segment and signals the arrival with a pace change.

- **Dramatic reveal (Honda "The Cog")**: A chain reaction component starts moving at normal speed, time-ramps to slow motion at the exact moment it contacts the next component (showing the precision engineering), then ramps back to normal for the next reaction phase.

## Source Examples

| Source | Usage | Speed Pattern |
|--------|-------|---------------|
| **Apple "Snowbrawl"** | Multiple speed ramps on snowball impacts and dodges, synced to music | Normal → slow (impact) → normal |
| **Nike "You Can't Stop Us" (2020)** | Speed ramps across split-screen seams to maintain action continuity | Slow → fast (seam crossing) → normal |
| **Honda "The Cog" (2003)** | Subtle speed changes at mechanical contact points to emphasize engineering precision | Normal → slow (contact) → normal |
| **Qmike样片** | Fast ramps at location transitions, slow ramps on scenic reveals | Fast → slow (arrival) or normal → fast (departure) |
| **The Matrix (1999)** | Speed ramps used throughout action sequences — the definitive cinematic reference | Sudden slow-mo during action, fast normal after |

## Related Techniques

- [whip-pan](whip-pan.md) — Often combined with speed ramps; the whip pan provides visual blur while the speed ramp controls pacing
- [cross-dissolve](cross-dissolve.md) — Alternative: cross-dissolve at the transition point instead of a speed change
- [beat-sync](../03-rhythm-patterns/beat-sync.md) — Speed ramps are frequently beat-synced; the speed change occurs on a musical downbeat
- [accelerando](../03-rhythm-patterns/accelerating-cut.md) — A broader rhythm pattern where shot durations progressively decrease; speed ramps can be the mechanism

## FFmpeg Notes

FFmpeg's `setpts` filter handles speed changes. Motion blur during fast segments requires `minterpolate` or `tmix` for frame blending. Slow-motion segments with optical flow interpolation use `minterpolate=fps=60:mi_mode=mci`.

**Basic speed ramp (slow → fast at transition):**

```bash
# Clip A: normal speed for 3.5s, then ramps to 3x speed over 0.5s
# Clip B: 3x speed for 0.5s, then ramps to normal over 0.5s

ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:v]setpts='if(between(T,3.5,4),PTS+1.5-(T-3.5)*1.5,PTS)'[v0]; \
    [1:v]setpts='if(between(T,0,0.5),PTS+1.0+T*2.0,PTS+2.0)'[v1]; \
    [v0][v1]concat=n=2:v=1:a=0[vout]" \
  -map "[vout]" \
  output.mp4
```

**With motion blur (tmix for fast segments):**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:v]setpts='if(between(T,3.5,4),PTS+1.5-(T-3.5)*1.5,PTS)', \
        split[v0a][v0b]; \
    [v0b]tmix=frames=3:weights='1 1 1'[v0blur]; \
    ..."
```

**Optical flow slow-motion (for the slow-mo segments):**

```bash
# Convert a 1-second segment at normal speed to 3-second slow motion
ffmpeg -i input.mp4 \
  -vf "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=3*PTS" \
  slowmo_output.mp4
```

**DaVinci Resolve approach (recommended for professional work):**
- Apply Retime Speed > Change Speed to clip
- Right-click clip > Retime Curve to add speed points
- Drag speed points to create the ramp shape
- Enable Retime Process > Optical Flow (Speed Warp) for smooth slo-mo
- Add Motion Blur > On (set to 0.5 for natural feel)

**Note:** Tested with FFmpeg 7.0+. For multi-point speed curves (not just linear ramps), use DaVinci Resolve or Premiere Pro — FFmpeg's `setpts` handles linear/continuous ramps well but complex multi-segment curves are easier in a GUI timeline.
