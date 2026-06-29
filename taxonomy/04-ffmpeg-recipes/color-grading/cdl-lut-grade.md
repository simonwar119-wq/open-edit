---
name: cdl-lut-grade
for_technique: color-grading/asc-cdl-plus-3d-lut
ffmpeg_version_tested: "8.1.2"
platform_tested: macOS
complexity: medium
ffmpeg_available: true
last_updated: 2026-06-27
---

## Purpose

Apply a two-stage color pipeline that matches the `color` block of a
`style-profile/v2.json`: first an **ASC CDL primary grade** (per-channel
`slope * in + offset`, then `^power`, then `saturation`), then a **creative 3D
LUT** (`.cube`). This is the exact order the render engine expects:

```
input normalization  →  CDL slope/offset  →  CDL power  →  CDL saturation  →  lut3d
```

> Note: the filter chain below is authored against the published FFmpeg filter
> semantics and is internally consistent, but it still needs a **real-machine
> test pass** before it can be marked verified. Treat the numbers as a starting
> point, not a signed-off grade.

## Stage mapping (profile → FFmpeg)

| Profile field | Meaning | FFmpeg filter |
|---|---|---|
| `input_normalization.auto_detect_log` / `target_space` | Bring log/wide-gamut footage into rec709 | `lut3d` (a log→rec709 LUT) or `colorspace` |
| `asc_cdl.slope`  `[R,G,B]` | Per-channel gain (multiply) | `eq=gamma_r/g/b` is NOT gain — use `lutrgb` / `colorchannelmixer` for slope |
| `asc_cdl.offset` `[R,G,B]` | Per-channel lift (add) | `colorbalance` (shadows/mids/highs) or `lutrgb` |
| `asc_cdl.power`  `[R,G,B]` | Per-channel gamma (`in^power`) | `eq=gamma=`, or per-channel `lutrgb` with `pow()` |
| `asc_cdl.saturation` | Global saturation | `eq=saturation=` |
| `creative_lut.ref` | Creative `.cube` look | `lut3d=file=...` |
| `creative_lut.intensity` | LUT blend amount (0..1) | `blend` the graded-with-LUT over graded-without |

The cleanest way to honor true ASC CDL math (`out = (slope*in + offset)^power`,
saturation in linear-ish space) is a single `lutrgb`/`lut3d` expression, but for
a readable, editable approximation the `lutrgb` + `eq` + `lut3d` chain below is
practical.

## Concrete example (Fincher-inspired bleach-bypass)

Values pulled from `engine/profiles/fincher-inspired.json`:
`slope=[0.95,1.0,1.02]`, `offset=[-0.02,0.0,0.01]`, `power=[1.05,1.0,0.98]`,
`saturation=0.55`, LUT `engine/luts/bleach-bypass.cube` at `intensity=0.7`.

```bash
ffmpeg -i input.mov -vf "
  # ── 1. input normalization: log/wide-gamut → rec709 ──────────────
  #    (swap in the correct log→709 LUT for the source; remove if already 709)
  lut3d=file=engine/luts/_norm_slog3_to_rec709.cube,

  # ── 2. ASC CDL: per-channel  slope*in + offset  +  power (gamma) ──
  #    lutrgb encodes one channel's full  (slope*val + offset*255)^power
  #    255-scaled offset:  -0.02*255≈-5.1 , 0.0 , +0.01*255≈2.55
  #    NOTE: clip()/pow keep values in 0..255
  lutrgb='
    r=clip(pow((0.95*val-5.1),1.05/1.0)*pow(255,1-1.05),0,255):
    g=clip((1.0*val+0.0),0,255):
    b=clip(pow((1.02*val+2.55),0.98/1.0)*pow(255,1-0.98),0,255)
  ',

  # ── 3. CDL saturation (global) ───────────────────────────────────
  eq=saturation=0.55,

  # ── 4. creative 3D LUT (bleach-bypass look) ──────────────────────
  lut3d=file=engine/luts/bleach-bypass.cube
" -c:a copy graded_full.mp4
```

### Honoring `creative_lut.intensity` (0.7, not full strength)

`lut3d` applies the look at 100%. To blend it back to 70%, run two branches and
mix — the graded-with-LUT over the graded-without:

```bash
ffmpeg -i input.mov -filter_complex "
  [0:v]lutrgb='r=clip(0.95*val-5.1,0,255):b=clip(1.02*val+2.55,0,255)',
       eq=saturation=0.55,split=2[base][forlut];
  [forlut]lut3d=file=engine/luts/bleach-bypass.cube[lutd];
  [base][lutd]blend=all_mode=normal:all_opacity=0.7[out]
" -map "[out]" -map 0:a? -c:a copy graded_07.mp4
```

`all_opacity=0.7` is the `intensity` knob: `0.0` = CDL only, `1.0` = full LUT.

## Notes & gotchas

- **Offset is 0..255-scaled here.** ASC CDL offset is defined in normalized
  0..1; multiply by 255 for the 8-bit `lutrgb` domain (e.g. `offset 0.01 → 2.55`).
- **Power is gamma on a normalized signal.** Doing `pow()` directly on a 0..255
  `val` needs the `*pow(255,1-power)` re-normalization shown above, or compute on
  `val/255` and scale back. For exactness prefer a baked CDL `.cube`.
- **Skin protection** (`palette_descriptor.target_skin_protect`) is not expressed
  here; do it in the creative LUT or with a qualifier in DaVinci, not in this
  primary chain.
- **10-bit:** add `-pix_fmt yuv420p10le` and feed 10-bit `.cube` LUTs to avoid
  banding in the crushed shadows of high-contrast looks.
- For a fully faithful CDL, bake `slope/offset/power/sat` into a single 3D LUT
  upstream and reduce this chain to `lut3d (norm) , lut3d (cdl) , lut3d (look)`.

## Related

- `engine/profiles/fincher-inspired.json` — consumes `luts/bleach-bypass.cube`
- `engine/profiles/wes-anderson-inspired.json` — consumes `luts/pastel-highkey.cube`
- `../transitions/cross-dissolve.md` — companion transition recipe
