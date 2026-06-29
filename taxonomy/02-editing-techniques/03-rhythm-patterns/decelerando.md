---
name: decelerando
description: |-
  A rhythm pattern where shot duration progressively increases, creating a sense of slowing tempo, settling calm, or contemplative resolution.
category: rhythm-pattern
complexity: medium
requires_audio: false
ffmpeg_available: true
source:
  origin: "Musical term decelerando (Italian: 'slowing down'); applied to film editing as the inverse of Eisenstein's accelerando montage"
  first_documented: "Sergei Eisenstein, 'Methods of Montage' in Film Form (1949); common in European art cinema of the 1960s (Tarkovsky, Antonioni)"
last_updated: 2026-05-13
---

## Definition

**Decelerando** (also called **decelerating-cut**, **progressive lengthening**, or **diminuendo editing**) is a rhythm pattern where each successive shot in a sequence is longer than the one before it. The effect is a palpable deceleration — the viewer feels the edit pulse slow down, creating a sense of settling, completion, or contemplative resolution.

While accelerando builds toward a climax, decelerando builds away from one. It's the visual equivalent of a long exhale. The technique is particularly powerful after an intense sequence: the progressive lengthening of shots signals to the viewer that the danger has passed, the action is over, and it's time to process the emotional aftermath.

A typical decelerando sequence:

```
Shot 1: 0.3s → Shot 2: 0.5s → Shot 3: 1.0s → Shot 4: 1.8s → Shot 5: 3.0s → Shot 6: 5.0s
```

The rate of deceleration shapes the emotional tone:
- **Gentle decelerando**: Duration increases by ~20–40% per shot. Feels like natural calming.
- **Drastic decelerando**: Duration doubles each shot. Feels like time stretching, almost dreamlike.
- **Plateau decelerando**: After a few steps, duration stabilizes at a long held shot. The "settling" effect.

**Honda "The Cog"** uses decelerando as its core structural rhythm. The ad opens with rapid match-cuts of mechanical parts (0.5–1.0s per shot in the first 30 seconds), then progressively lengthens as the chain reaction becomes more complex. By the final 20 seconds, shots are held for 3–5 seconds, culminating in a 10-second held wide shot of the completed Accord rolling off the ramp. The decelerando mirrors the chain reaction itself: initial chaos of many small parts gradually settling into the final coherent whole.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `initial_duration_s` | float | 0.1–2.0 | 0.5 | Duration of the first (shortest) shot. Typically follows a climax or fast section. |
| `final_duration_s` | float | 1.0–15.0 | 4.0 | Duration of the last (longest) shot. Longer = more contemplative. |
| `shot_count` | int | 3–15 | 6 | Number of shots in the decelerating sequence. |
| `deceleration_curve` | enum | `linear` / `exponential` / `logarithmic` / `custom` | `exponential` | How the duration increases across shots. Exponential feels most natural for a "settling" effect. |
| `deceleration_rate` | float | 0.1–1.0 | 0.35 | For exponential: multiplier applied each step (e.g., 1.35x duration each shot). |
| `final_hold_s` | float | 2.0–20.0 | 5.0 | The final held shot after deceleration ends. Can include music fade-out or silence. |
| `audio_sync` | bool | true / false | true | Whether the audio also decelerates (ritardando in music, or ambient sound expanding). |

## Usage Scenarios

- **Chain reaction climax (Honda "The Cog")**: The entire 2-minute ad is structured as a single decelerando arc. Rapid mechanical part match-cuts (0.5–0.8s each) in the first 30 seconds gradually lengthen to wider shots of the machine in motion (2–3s) by the middle, and culminate in a 10-second locked-off wide shot of the completed Accord. The decelerando mirrors the mechanical chain reaction settling into its final state.

- **Post-action emotional resolution (Qmike travel/lifestyle)**: After a fast-paced city walking sequence (accelerando), the editor transitions to decelerando: sunset shot (0.5s from the final fast cut), then a cafe exterior (1.5s), then a cup of tea being poured (3s), then the subject sitting at the window looking out (5s held). The decelerando gives the viewer permission to relax and absorb the location's atmosphere.

- **Commercial ending (brand content)**: A brand's feature demonstration ends. The final shots slow down: product in use (0.8s), product detail (1.5s), product in hero lighting (3s), product in lifestyle setting (5s with slow push-in). The decelerando invites the viewer to appreciate the product rather than just see it.

- **Music video outro**: After an energetic chorus with rapid cuts, the bridge/outro uses decelerando: each shot gets progressively longer as the music strips down to a single instrument, ending on a held close-up of the artist.

## Source Examples

| Source | Usage | Deceleration Pattern |
|--------|-------|---------------------|
| **Honda "The Cog" (2003)** | The entire 2-min ad: 0.5–0.8s match-cuts in the first 30s → 2–3s shots in the middle → 5–10s shots in the final 20s. The decelerando is the structural backbone. | exponential, 0.5→10.0 over ~40 shot sequences |
| **Qmike样片 (travel)** | Post-walk cafe scene: 0.5s (street->cafe transition) → 1.5s (cafe exterior) → 3s (tea poured) → 5s (subject looking out window). Linear deceleration. | linear, 0.5→5.0 over 4 shots |
| **Nike "You Can't Stop Us" (end)** | The final 10 seconds after Rapinoe's last line: rapid split-screen transitions slow to a held single-screen wide of athletes in silence. Brief but effective decelerando. | plateau, 0.3→3.0→held |
| **Apple "Snowbrawl" (end)** | After the slow-motion laughter climax, the final seconds decelerate: one wide shot of kids playing (held), one shot of a parent watching (held longer). Only 2 shots but the shift is dramatic. | exponential, 2.0→6.0 over 2 shots |

## Related Techniques

- [accelerando](accelerating-cut.md) — The inverse: progressively shorter shots. The two are often paired (accelerando → climax → decelerando) for a complete arc.
- [pause-and-release](pause-and-release.md) — Decelerando can lead to a pause (held silence), which then releases. The pause is the extreme end of deceleration.
- [breath-rhythm](breath-rhythm.md) — If cycle_acceleration > 1.0, each breath cycle slows down, creating a decelerando effect across cycles.
- [montage-burst](montage-burst.md) — A montage burst followed by decelerando is a classic structure: visual explosion → settling calm.
- [reveal-payoff](reveal-payoff.md) — Decelerando often accompanies the reveal phase: as the subject is fully revealed, the edit slows down to let the viewer appreciate it.

## FFmpeg Notes

**Generate a decelerando sequence with progressively longer durations:**
```python
shots = [
    ("detail1.mp4", 0.5),
    ("detail2.mp4", 0.8),
    ("mid_shot.mp4", 1.5),
    ("wide_shot.mp4", 3.0),
    ("hero_shot.mp4", 5.0),
]

with open("decelerando.txt", "w") as f:
    for clip, dur in shots:
        f.write(f"file '{clip}'\n")
        f.write(f"duration {dur}\n")
```

**Trim each clip to its designated decelerando duration:**
```bash
for i in 0 1 2 3 4; do
  durations=("0.5" "0.8" "1.5" "3.0" "5.0")
  ffmpeg -i "shot$i.mp4" -t "${durations[$i]}" -c copy "trim$i.mp4"
done
# Then concat all trimmed clips
```

**Analyze decelerando in existing footage:**
```bash
# Extract scene change timestamps, compute durations, detect progressive lengthening
ffprobe -v quiet -print_format json -show_entries frame=pts_time \
  -vf "select=gt(scene\\,0.3)" input.mp4 | python -c "
import json, sys
data = json.load(sys.stdin)
times = [f['pts_time'] for f in data['frames']]
durations = [times[i+1]-times[i] for i in range(len(times)-1)]
is_decelerando = all(durations[i] <= durations[i+1]*1.1 for i in range(len(durations)-1))
print('Decelerando detected:', is_decelerando)
"
```
