---
name: accelerando
description: |-
  A rhythm pattern where shot duration progressively decreases, creating a sense of accelerating tempo and rising intensity toward a climax.
category: rhythm-pattern
complexity: medium
requires_audio: false
ffmpeg_available: true
source:
  origin: "Musical term accelerando (Italian: 'speeding up'); adopted in film editing theory via Sergei Eisenstein's metric montage (1920s)"
  first_documented: "Sergei Eisenstein, 'Methods of Montage' in Film Form (1949); Carol Vernallis on music video pacing (2004)"
last_updated: 2026-05-13
---

## Definition

**Accelerando** (also called **accelerating-cut**, **progressive shortening**, or **rising-tempo editing**) is a rhythm pattern where each successive shot in a sequence is shorter than the one before it. The effect is a palpable sense of quickening tempo — the viewer feels the edit pulse accelerate even without a musical cue.

The technique works because the brain interprets progressively shorter intervals as increasing urgency or approaching climax. It's the editing equivalent of a drum roll: the closer you get to the crash, the faster the hits.

A typical accelerando sequence:

```
Shot 1: 2.0s → Shot 2: 1.5s → Shot 3: 1.0s → Shot 4: 0.7s → Shot 5: 0.4s → Shot 6: 0.3s → CLIMAX
```

The rate of acceleration (how much shorter each shot gets) determines the emotional arc:
- **Gentle accelerando**: Duration decreases by ~10–20% per shot. Feels like natural quickening.
- **Aggressive accelerando**: Duration decreases by ~30–50% per shot. Feels like panic or explosive energy.
- **Exponential accelerando**: Duration halves each cut (2.0 → 1.0 → 0.5 → 0.25). Used for extreme tension.

The climax after an accelerando sequence is typically a **smash cut** to a held wide shot, a slow-motion moment, or a sudden silence — the visual equivalent of reaching the top of a roller coaster.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `initial_duration_s` | float | 0.5–5.0 | 2.0 | Duration of the first (longest) shot in the sequence. |
| `final_duration_s` | float | 0.1–2.0 | 0.3 | Duration of the last (shortest) shot before the climax. |
| `shot_count` | int | 3–20 | 6 | Number of shots in the accelerating sequence. |
| `acceleration_curve` | enum | `linear` / `exponential` / `logarithmic` / `custom` | `linear` | How the duration decreases across shots. Linear = equal decrement. Exponential = multiplicative. |
| `acceleration_rate` | float | 0.1–1.0 | 0.25 | For linear: fraction of initial_duration removed each step. For exponential: multiplier applied each step. |
| `climax_duration_s` | float | 0.5–8.0 | 2.0 | Duration of the climax shot after acceleration. Longer = more release. |
| `climax_type` | enum | `held-wide` / `slowmo` / `blackout` / `smash-cut` / `quiet-moment` | `held-wide` | What follows the acceleration peak. |

## Usage Scenarios

- **Intensity-building climax (Nike "You Can't Stop Us")**: In the final 15 seconds of the ad, the split-screen transition rate accelerates — initially changing every 2 seconds, then every 1 second, then every 0.5 seconds — culminating in the unified single-screen shot of multiple athletes in parallel. Rapinoe's voiceover reaches its peak line ("You can't stop us") at the exact moment of the climax.

- **Emotional build in travel content (Qmike travel/lifestyle)**: A sunset time-lapse sequence: first shot 3s (wide of sky), 2.5s (clouds moving), 2s (color changing), 1.5s (golden light), 1s (sun dipping), 0.5s (last sliver of light) → smash cut to black → reveal of the city at night (4s held shot). The acceleration mirrors the sun's own speed as it nears the horizon.

- **Action sequence climax (Apple "Snowbrawl")**: The final snowball exchange accelerates: wide shot (1.5s), medium of thrower (1.0s), close-up of ball in air (0.7s), impact close-up (0.4s), reaction (0.3s) → slow-motion laughter (3s). The acceleration brings the action to a peak before the emotional resolution.

- **Brand product launch (brand content)**: Features accelerating reveal: product in box (2s), product emerging (1.5s), product 3/4 angle (1.0s), product detail (0.7s), product hero shot with animation (0.4s) → product in hand, real-world use (3s held).

## Source Examples

| Source | Usage | Acceleration Pattern |
|--------|-------|---------------------|
| **Nike "You Can't Stop Us" (2020)** | Final 15s: split-screen transition rate accelerates from ~2s intervals to ~0.3s intervals over 8 transitional beats. Climax: unified single-screen hero shot. | exponential, 2.0→0.3 over 8 shots |
| **Qmike样片 (travel)** | Sunset time-lapse: shot durations decrease from 3.0s to 0.5s over 6 shots. Climax: night city wide shot, 4s held. | linear, 3.0→0.5 over 6 shots |
| **Apple "Snowbrawl"** | Final snowball volley: 1.5→0.3s over 5 shots. Climax: slow-motion child laughter, 3s. | exponential, 1.5→0.3 over 5 shots |
| **Edgar Wright (Scott Pilgrim)** | Battle sequences: each successive hit during a combo accelerates. The editing tempo mirrors the fighting tempo. | aggressive, custom per scene |

## Related Techniques

- [decelerando](decelerando.md) — The inverse: progressively longer shots create a slowing-down effect. Often paired with accelerando for a "rise and fall" arc.
- [montage-burst](montage-burst.md) — An extreme form of accelerando where the final shots reach <0.3s duration, creating a visual "explosion."
- [breath-rhythm](breath-rhythm.md) — If you set cycle_acceleration < 1.0, each breath cycle speeds up, combining breath rhythm with accelerando.
- [beat-sync](beat-sync.md) — Accelerando sequences are typically beat-synced: each progressively shorter shot aligns with an accelerating beat pattern.
- [smash-cut](smash-cut.md) — The climax of an accelerando sequence is often a smash cut to a contrasting moment.

## FFmpeg Notes

Accelerando is a timeline construction technique, but FFmpeg can execute it programmatically.

**Generate an accelerando sequence with dynamic duration scaling:**
```python
import subprocess

shots = [
    ("intro.mp4", 2.0),
    ("build1.mp4", 1.5),
    ("build2.mp4", 1.0),
    ("build3.mp4", 0.7),
    ("build4.mp4", 0.4),
    ("climax.mp4", 3.0),
]

# Generate a concat file with trim directives
with open("accelerando.txt", "w") as f:
    for clip, dur in shots:
        f.write(f"file '{clip}'\n")
        f.write(f"duration {dur}\n")

# Or use select filter for precise per-shot durations
# ffmpeg -f concat -safe 0 -i accelerando.txt -c copy output.mp4
```

**Using FFmpeg trim for duration control:**
```bash
# Trim each clip to its designated duration
ffmpeg -i shot1.mp4 -t 2.0 -c copy trim1.mp4
ffmpeg -i shot2.mp4 -t 1.5 -c copy trim2.mp4
# ... then concat all trimmed clips
ffmpeg -f concat -safe 0 -i trimmed.txt -c copy output.mp4
```
