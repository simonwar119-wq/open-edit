---
name: cross-dissolve
for_technique: transitions/cross-dissolve
ffmpeg_version_tested: "8.1.2"
platform_tested: macOS
complexity: low
ffmpeg_available: true
last_updated: 2026-06-27
---

## Purpose

Implement a **cross-dissolve** (lap dissolve / mix): clip A fades out while clip
B fades in over a fixed overlap window. This is the FFmpeg realization of the
`transitions` rule `{ "use": "dissolve", "duration_ms": 500 }` and the
`ffmpeg_xfade_map: { "dissolve": "fade" }` entry in a `style-profile/v2.json`.

Video uses `xfade=transition=fade`; audio uses `acrossfade` so the sound bridges
the same overlap instead of hard-cutting under the picture.

> Note: this recipe is authored against documented `xfade`/`acrossfade`
> semantics and is internally consistent, but it still needs a **real-machine
> test pass** before being marked verified.

## Key parameters

| Param | Meaning | Profile source |
|---|---|---|
| `duration` (D) | Length of the overlap, seconds | `duration_ms / 1000` (e.g. `500ms → 0.5`) |
| `offset` (O) | When the dissolve starts in the **first** stream, seconds | `clipA_length − D` |
| `transition=fade` | The xfade mode mapped from `dissolve` | `ffmpeg_xfade_map.dissolve` |

`offset` is measured from the start of clip A. To place the dissolve so it ends
exactly at A's tail: `offset = durationA − D`.

## Concrete example (two clips, 0.5s dissolve)

Clip A is 5.0s, so the 0.5s dissolve starts at `offset = 5.0 − 0.5 = 4.5`:

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 -filter_complex "
  # ── video: cross-dissolve, 0.5s, starting 4.5s into clip A ──
  [0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v];
  # ── audio: equal-power crossfade of the same 0.5s overlap ──
  #    c1/c2=tri keeps perceived loudness steady across the blend
  [0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a]
" -map "[v]" -map "[a]" -c:v libx264 -c:a aac output.mp4
```

### Chaining three clips

Each subsequent `offset` is measured on the **already-faded** stream, so it is
`(running length so far) − D`:

```bash
# A=5.0s, B=4.0s, D=0.5s  → second dissolve at (5.0+4.0-0.5) - 0.5 = 8.0
ffmpeg -i clipA.mp4 -i clipB.mp4 -i clipC.mp4 -filter_complex "
  [0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v01];
  [v01][2:v]xfade=transition=fade:duration=0.5:offset=8.0[v];
  [0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a01];
  [a01][2:a]acrossfade=d=0.5:c1=tri:c2=tri[a]
" -map "[v]" -map "[a]" -c:v libx264 -c:a aac output.mp4
```

## Notes & gotchas

- **Total length shrinks by D per transition.** Two clips dissolved by 0.5s →
  `lenA + lenB − 0.5`. Budget this when matching music beats.
- **`xfade` needs matching size/fps/format.** Pre-normalize:
  `scale=1080:1920,fps=24,format=yuv420p,setsar=1` on each input before the
  xfade, or it will error or stutter.
- **`offset` must be < durationA.** If `offset ≥ lenA` the second clip never
  appears; if too small, the dissolve eats into earlier action.
- **`fadeblack` / `fadewhite`** are dip-to-color variants of the same filter if a
  profile ever wants a harder beat than a straight mix.
- Keep dissolves to `max_per_minute` from the profile rule (e.g. Fincher = 2/min)
  — overuse reads as soft/dated rather than controlled.

## Related

- `../color-grading/cdl-lut-grade.md` — companion color recipe
- `engine/profiles/fincher-inspired.json` — `dissolve` at scene changes, 500ms
- `engine/profiles/wes-anderson-inspired.json` — `dissolve` allowed alongside
  `whip_pan` / `snap_zoom`
