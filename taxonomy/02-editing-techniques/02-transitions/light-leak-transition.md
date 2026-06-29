---
name: light-leak-transition
description: |-
  A transition where a brief burst of light — resembling lens flare, sunlight washing over the lens, or a practical light source — overlays the edit point, temporally bleaching the image to white or warm tones before revealing the next shot.
category: transition
complexity: medium
requires_audio: false
ffmpeg_available: true
source:
  origin: "Accidental in-camera effect from analog film (light hitting the film gate); intentionally stylized in 1990s music videos and 2000s surf/skate culture films"
  first_documented: "Analog film artifacts (1960s–1980s); popularized as a deliberate technique in skate/surf films (Lords of Dogtown, 2005) and music videos"
last_updated: 2026-05-13
---

## Definition

A **light leak transition** uses a flash of light — natural (sunlight sweeping past the lens), artificial (a camera flash), or synthetic (a digitally generated flare) — to mask the cut point between two shots. The light burst creates a momentary "whiteout" (or color-tinted flash) that resets the viewer's visual field, allowing the new shot to emerge from the brightness.

Light leaks are distinct from simple white flashes or dip-to-white transitions in their **texture and character**:

- **Light flare**: A lens flare arcs across the frame — may include ghosting, chromatic aberration, or anamorphic streak artifacts
- **Leak wash**: Light bleeds unevenly into one corner of the frame, gradually washing out the image before clearing
- **Slit-scan light**: A narrow band of bright light sweeps across the frame like a scanner
- **Natural light sweep**: A cloud passes, sunlight floods through a window, or headlights from a passing car wash over the lens

The editorial purpose of light leak transitions is to create an **analog, tactile feel** in an otherwise digital edit. They signal:

1. **Vulnerability / Realism**: The camera is present in the scene — light hitting the lens means the camera is a real object in the real world
2. **Temporal shift**: A light leak can suggest waking up, passing out, or moving through a bright environment (tunnel, sunrise, doorway)
3. **Warmth / Memory**: Warm-toned light leaks (golden, amber) suggest nostalgia or positive emotional states
4. **Energy / Euphoria**: Bright white/golden flares at transition points in action sequences suggest peak excitement

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `duration_s` | float | 0.1 to 1.5 | 0.4 | Total duration from first light onset to full clearance. |
| `leak_type` | enum | `flare` / `wash` / `slit-scan` / `natural` / `flash` | `flare` | Shape and behavior of the light leak. |
| `color_temp` | enum | `warm` / `neutral` / `cool` / `golden` / `magenta` | `warm` | Color tint of the light leak. Warm/golden = sunrise or tungsten; cool = fluorescent or shade; magenta = practical neon. |
| `intensity` | float | 0.0 to 1.0 | 0.7 | Peak brightness/opacity of the leak. 1.0 = completely white frame. |
| `position` | enum | `center` / `top-left` / `top-right` / `bottom` / `anamorphic-horizontal` | `top-left` | Where the light enters the frame. Anamorphic = horizontal streak across center. |
| `chromatic_aberration` | boolean | true / false | false | Whether to add RGB separation at the flare edges for a vintage lens look. |
| `grain_match` | boolean | true / false | true | Whether to add film grain over the leak to match analog texture. |

## Usage Scenarios

- **Euphoric action transitions (Apple "Snowbrawl")**: Sunlight flashes across the lens as a character dives for a snowball — the light leak masks the cut to a closer angle, and the warm flash reinforces the joyful outdoor atmosphere.

- **Time-compression montages (Qmike travel/lifestyle)**: A golden-hour light leak transitions between shots of the same location at different times — the leak suggests the sun moving across the sky and creates a "waking from a dream" temporal bridge between moments.

- **Skate/surf/lifestyle content (Qmike / action sports)**: A light leak as the subject exits a tunnel into sunlight — the flash transitions from the interior shot to the exterior reveal. The light leak is natural (real sunlight hitting the lens during the action).

- **Memory/flashback transitions (narrative content)**: A slow, warm-toned light leak (amber/golden, 0.8–1.2s) signals a shift into a memory or dream sequence. The light builds slowly, peaks at full wash, then clears into the past.

- **Brand openings/closings (Nike / brand content)**: A subtle light leak at the brand logo transition — the logo catches a lens flare that transitions into the first shot of the ad.

## Source Examples

| Source | Usage | Leak Type |
|--------|-------|-----------|
| **Apple "Snowbrawl"** | Subtle warm light leaks at action peaks, reinforcing the bright snowy outdoor setting | Natural wash / flare |
| **Nike "You Can't Stop Us" (2020)** | Minimal — occasional flare at major section breaks (every 20–30s) | Flare, neutral-temp |
| **Qmike样片** | Golden-hour light leaks at sunset transitions; natural light sweep through windows at location entries | Natural / warm |
| **Surf/skate films (Lords of Dogtown, 2005)** | Signature aesthetic — heavy use of lens flares and light leaks as transitions | Flare / natural |
| **Music videos (indie / lo-fi)** | Deliberate stylized light leaks — often with chromatic aberration and grain | Slit-scan / wash / colored |

## Related Techniques

- [cross-dissolve](cross-dissolve.md) — A dissolve achieves a similar "soft transition" feel without the textural light element
- [mask-transition](mask-transition.md) — Another creative overlay transition; light leaks are essentially "light-shaped masks"
- [whip-pan](whip-pan.md) — Can be combined: a whip pan through a bright window creates a natural light leak + motion blur transition
- [dip-to-color](../01-cuts/hard-cut.md) — A dip to white is the "maximal" version: full white frame vs. textured light leak

## FFmpeg Notes

Light leaks are best created with **pre-recorded light leak overlay footage** or **generated flare effects**. FFmpeg can composite these overlays using blend or overlay filters. Pure filter-graph generation (without external assets) is limited — the `geq` filter can create basic light gradients but lacks the organic texture of real lens flares.

**Using a light leak overlay clip:**

```bash
# light_leak_overlay.mp4 is a pre-recorded light leak (alpha channel or black background)
ffmpeg -i clipA.mp4 -i clipB.mp4 -i light_leak_overlay.mp4 \
  -filter_complex "\
    [0:v]trim=0:4,setpts=PTS-STARTPTS[v0]; \
    [1:v]trim=2:6,setpts=PTS-STARTPTS[v1]; \
    [v0][v1]xfade=transition=fade:duration=0.3:offset=3.8[vxfade]; \
    [vxfade][2:v]overlay=0:0:enable='between(t,3.7,4.3)'[vout]" \
  -map "[vout]" output.mp4
```

**Generating a synthetic light wash (warm gradient flash):**

```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    color=c=#FFE4B5:s=1920x1080:d=0.5,format=rgba[flash]; \
    [0:v]trim=0:3.7,setpts=PTS-STARTPTS[v0]; \
    [1:v]trim=0:4,setpts=PTS-STARTPTS[v1]; \
    [v0][flash]overlay=0:0:enable='between(t,3.5,3.7)':format=auto, \
        setpts=PTS-STARTPTS[v0a]; \
    [flash]setpts=PTS-STARTPTS[flashB]; \
    [flashB][v1]overlay=0:0:enable='between(t,0,0.3)':format=auto, \
        setpts=PTS-STARTPTS+3.7/TB[v1a]; \
    [v0a][v1a]concat=n=2:v=1:a=0[vout]" \
  -map "[vout]" output.mp4
```

**Generating a lens flare (basic multi-point flare):**

```bash
# Uses geq for a simple radial gradient burst
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    color=c=black:s=1920x1080:d=1.0, \
      geq=r='255*exp(-((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/(5000*(1-T)*10+100))': \
          g='200*exp(-((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/(5000*(1-T)*10+100))': \
          b='100*exp(-((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2))/(5000*(1-T)*10+100))' \
      [flare_gen]; \
    ..."
```

**Recommended asset approach:**
Download free light leak overlays (e.g., from Mixkit, Artgrid, or stock footage sites) as ProRes 4444 with alpha channels. Composite them in DaVinci Resolve Fusion or After Effects for best control. FFmpeg can composite them at the cost of some color precision.

**Note:** Tested with FFmpeg 7.0+. For professional light leak transitions, DaVinci Resolve Fusion is strongly recommended — the fusion node tree allows precise color grading of the leak (warm/cool mix, gamma adjustment, glow falloff) that FFmpeg filter graphs cannot match.
