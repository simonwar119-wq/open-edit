---
name: cross-dissolve
description: |-
  A gradual transition where the first shot fades out while the second shot fades in, creating a brief period of superimposed overlap between the two images.
category: transition
complexity: low
requires_audio: false
ffmpeg_available: true
source:
  origin: "Fundamental editing technique dating to early cinema; first used by Georges Méliès (late 1890s) and formalized in classical Hollywood continuity editing"
  first_documented: "Georges Méliès, early trick films (1896–1900); Karel Reisz, The Technique of Film Editing (1953)"
last_updated: 2026-05-13
---

## Definition

A **cross-dissolve** — also called **dissolve**, **lap dissolve**, or simply **mix** — is the most universally recognized transition in film editing. It creates a smooth visual bridge by superimposing the end of clip A over the beginning of clip B. For a brief duration (typically 0.3–0.8 seconds), both images are partially transparent and visible simultaneously, until clip A fully fades to black/transparent and clip B becomes fully opaque.

Cross-dissolves serve several editorial functions:

- **Temporal passage**: A dissolve signals the passage of time — minutes, hours, or years — unlike a hard cut which implies instantaneous continuity
- **Spatial transition**: Moving from one location to another with a dissolve suggests a natural journey or shift in perspective
- **Emotional smoothing**: Dissolves soften the impact of emotionally charged transitions, allowing the viewer to process one moment before receiving the next
- **Montage bonding**: In montage sequences, dissolves connect thematically related images, suggesting a conceptual relationship between otherwise disparate visuals
- **Invisible stitch**: A short dissolve (0.1–0.3s) can conceal a jump cut or a mismatched edit, making the transition imperceptible

The cross-dissolve is the **softest** transition in the editor's toolkit — it signals continuity rather than disruption. It tells the viewer: "these two moments are connected; stay with me."

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `duration_s` | float | 0.1 to 3.0 | 0.5 | Total dissolve duration. <0.3s = practically invisible; >1.0s = deliberate, poetic. |
| `curve` | enum | `linear` / `ease-in` / `ease-out` / `s-curve` | `s-curve` | Dissolve curve shape. S-curve (slow-fast-slow) feels most natural to the human eye. |
| `audio_crossfade` | boolean | true / false | true | Whether to crossfade audio tracks alongside video. False = hard audio cut beneath visual dissolve. |
| `audio_crossfade_curve` | enum | `linear` / `equal-power` / `s-curve` | `equal-power` | Audio crossfade shape. Equal-power maintains consistent perceived volume. |
| `superimpose_opacity_peak` | float | 0.0 to 1.0 | 0.5 | Maximum opacity during the midpoint of the dissolve. 1.0 = both shots fully visible at midpoint; 0.5 = each at 50%. |

## Usage Scenarios

- **Temporal montage connection (Honda "The Cog")**: Cross-dissolves connect the chain reaction sequences where the action is continuous but the camera position changes. A 0.3s dissolve between two shots of the machine hides the fact that different takes were stitched together — the dissolve smooths the seam while the mechanical sound design bridges the audio gap.

- **Time passage in travel content (Qmike travel/lifestyle)**: Cross-dissolves between shots of the same location at different times of day — a dissolve from a bustling midday market to the same street at quiet midnight, signaling the passage of hours. The dissolve duration (0.8–1.2s) gives the viewer time to register the change.

- **Emotional transition in narrative content**: A slow dissolve (1.5–2.0s) from a character's happy memory to their present-day sadness, telling the viewer that time has passed and the emotional landscape has shifted.

- **Montage sequences (sports / brand content)**: Dissolves connect a series of quick shots in a highlight reel — each dissolve signals that these are separate moments united by theme rather than by continuous time.

- **Invisible stitch for two-shot composite (Honda "The Cog")**: The most technically notable use — a very short dissolve (0.1–0.2s) at the seam between two shots that are meant to read as one continuous take. The dissolve is fast enough that the viewer doesn't consciously register it, but present enough to smooth any slight mismatch in motion or exposure.

## Source Examples

| Source | Usage | Dissolve Duration | Notes |
|--------|-------|-------------------|-------|
| **Honda "The Cog" (2003)** | Short dissolves (0.1–0.3s) at stitch points between chain-reaction shots | 0.1–0.3s | The dissolves are invisible on first watch — the ad appears to be one continuous take |
| **Qmike样片** | Time-passage dissolves (0.8–1.5s) between day/night shots; softer transitions between emotional beats | 0.5–1.5s | Signature use of slow dissolves for reflective moments |
| **Nike "You Can't Stop Us" (2020)** | Minimal dissolves used mainly at the very start and end of the split-screen montage; the body uses hard cuts | 0.3s | Dissolves frame the opening and closing segments |
| **Apple "Snowbrawl"** | Not a primary technique — mostly hard cuts and whip pans; dissolves used only in the opening setup | 0.3–0.5s | Contrast: action sequences avoid dissolves entirely |

## Related Techniques

- [whip-pan](whip-pan.md) — A faster, more energetic alternative for action transitions
- [speed-ramp](speed-ramp.md) — Can replace a dissolve by using speed change instead of opacity fade
- [light-leak-transition](light-leak-transition.md) — A creative variant: uses a light leak overlay instead of simple transparency fade
- [mask-transition](mask-transition.md) — Uses a traveling matte instead of a uniform fade
- [dip-to-color](../01-cuts/hard-cut.md) — Related: fade to black/white then fade in, vs. directly overlapping

## FFmpeg Notes

Cross-dissolve is natively supported in FFmpeg via the `xfade` filter (cross-fade), which is the cleanest and most efficient method.

**Basic cross-dissolve (0.5s duration):**

```bash
# Cut occurs at 4.5s into clip A, dissolve lasts 0.5s
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "xfade=transition=fade:duration=0.5:offset=4.5" \
  output.mp4
```

**Multiple cross-dissolve transitions (three clips):**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 -i clipC.mp4 \
  -filter_complex "\
    [0:v][0:a][1:v][1:a]xfade=transition=fade:duration=0.5:offset=4.5[v1][a1]; \
    [v1][a1][2:v][2:a]xfade=transition=fade:duration=0.3:offset=9.0[v2][a2]" \
  -map "[v2]" -map "[a2]" output.mp4
```

**Custom dissolve curve (using blend filter for more control):**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:v]trim=0:4.5,setpts=PTS-STARTPTS[v0]; \
    [1:v]trim=0:2,setpts=PTS-STARTPTS[v1]; \
    [0:a]atrim=0:4.5[a0]; \
    [1:a]atrim=0:2[a1]; \
    [v0][v1]blend=all_expr='A*(1-clip((T)/0.5))+B*clip((T)/0.5)':shortest=1[vout]; \
    [a0][a1]acrossfade=d=0.5:c1=tri:c2=tri[aout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**Note:** Tested with FFmpeg 7.0+. The `xfade` filter supports multiple transition types beyond `fade` (e.g., `fadeblack`, `fadewhite`, `fadegrays`) for dip-to-color variants of the dissolve.
