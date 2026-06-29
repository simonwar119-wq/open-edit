---
name: three-fast-one-slow
description: |-
  A rhythm pattern where three rapid cuts are followed by one sustained shot, creating a rhythmic "stutter-stop" punctuation that emphasizes the final held image.
category: rhythm-pattern
complexity: low
requires_audio: false
ffmpeg_available: true
source:
  origin: "Classical editing intuition — a natural extension of musical phrasing (three eighth notes + one quarter note); observed in commercial editing from the 2000s onward"
  first_documented: "Common in MTV-era music videos (1990s); described in editing tutorials as 'stutter edit' or 'triplet pattern'"
last_updated: 2026-05-13
---

## Definition

**Three-fast-one-slow** (also called **stutter-stop**, **triplet release**, or **3+1 pattern**) is a rhythm technique where a cluster of three short, rapid cuts (0.3–0.8s each) is followed by a single longer held shot (1.5–6s). The pattern creates a distinctive "stutter… and land" feel — three quick visual pulses that build micro-tension, then resolve into a sustained image that the viewer can finally absorb.

The pattern can be notated as:

```
X X X — E E E — A A A — HOLD
(0.5s)(0.5s)(0.5s) | (3.0s)
```

The psychological effect is rooted in expectation. After three fast cuts, the viewer's brain anticipates a fourth fast cut. When the fourth shot is instead held significantly longer, it creates a **rhythmic surprise** that makes the held shot feel more significant, more weighty, more "real."

The three fast shots typically show different angles of the same subject/action (e.g., three different close-ups of a food preparation detail), while the held shot is a wider composition that reveals context or a complete action.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `fast_shot_count` | int | 2–5 | 3 | Number of fast shots before the held shot. "Three" is canonical; 2 or 4 also work. |
| `fast_shot_duration_s` | float | 0.2–1.0 | 0.5 | Duration of each fast shot. Shorter = more staccato. |
| `slow_shot_duration_s` | float | 1.0–8.0 | 3.0 | Duration of the held shot after the fast cluster. |
| `fast_shot_relationship` | enum | `same-subject` / `sequence` / `variety` | `same-subject` | Whether the fast shots show the same subject from different angles, a sequential action, or unrelated but thematic images. |
| `pattern_repetitions` | int | 1–10 | 3 | How many times the 3+1 pattern repeats in a sequence. |
| `hold_shot_type` | enum | `wide` / `reaction` / `detail` / `action-complete` | `wide` | Preferred type for the held shot. Wide gives context. Reaction gives emotional weight. Detail invites inspection. |
| `audio_pause_on_hold` | bool | true / false | false | Whether the audio drops (silence or duck) during the held shot to emphasize the rhythmic break. |

## Usage Scenarios

- **Food preparation close-ups (Qmike travel/lifestyle)**: Three fast shots of cooking details — knife chopping (0.5s), ingredients hitting the pan (0.5s), steam rising (0.5s) — followed by a 3-second wide shot of the finished dish on the table. The three fast cuts build sensory anticipation; the held wide shot delivers the satisfaction of seeing the complete dish.

- **Action → reaction pattern (Apple "Snowbrawl")**: Three fast shots of a snowball being thrown, flying through the air, and hitting a target (0.4s each), followed by a 2.5-second held shot of the target child's laughing reaction. The fast shots provide the action; the held shot provides the emotional payoff.

- **Product feature highlight (brand content)**: Three detail shots — screen close-up (0.6s), button press (0.5s), angle change (0.5s) — followed by a 3-second hero shot of the product in its best lighting. The 3+1 pattern makes the hero shot feel like the "answer" to the three feature questions.

- **Travel moment capture (Qmike travel)**: A street performer: three fast shots — performer's hands moving (0.4s), instrument detail (0.5s), audience reaction (0.5s) — followed by a 4-second wide shot of the full scene: performer, instrument, audience, and street ambiance. The held wide shot is where the viewer feels "being there."

## Source Examples

| Source | Usage | Pattern Detail |
|--------|-------|---------------|
| **Qmike样片 (travel/food)** | Signature technique: 3 rapid cooking detail shots → held dish reveal wide shot. Used 4–5 times per video as punctuation between sections. | 3×0.5s fast, 1×3.0s held, 4–5 repetitions per video |
| **Apple "Snowbrawl"** | Snowball action: 3 throw-flight-impact shots (0.4s each) → 1 held reaction shot (2.5s). Repeated for each major snowball exchange. | 3×0.4s fast, 1×2.5s held, 3 repetitions |
| **Qmike travel (landscape)** | Mountain reveal: 3 detail shots of texture (rock, moss, snow) → 1 held wide shot of the mountain peak at golden hour. | 3×0.6s fast, 1×4.0s held |
| **Nike "You Can't Stop Us"** | Certain athlete sequences: 3 fast split-screen match transitions → 1 held single-athlete shot. Not the dominant pattern but used for emphasis. | 3×0.3s fast, 1×1.5s held |

## Related Techniques

- [breath-rhythm](breath-rhythm.md) — Three-fast-one-slow is a specific instance of breath rhythm where the inhale is exactly 3 shots and the exhale is a single held shot.
- [montage-burst](montage-burst.md) — If the three fast shots are shortened to <0.2s and the count increased, it becomes a montage burst.
- [accelerando](accelerating-cut.md) — The three fast shots can accelerate within themselves (0.6→0.4→0.3) before the held shot, combining patterns.
- [pause-and-release](pause-and-release.md) — The held shot in 3+1 acts as a micro-release. If the held shot includes a silent beat before music re-enters, it becomes a pause-and-release structure.
- [beat-sync](beat-sync.md) — The 3+1 pattern maps naturally to a 3+1 beat pattern (triplet + downbeat).

## FFmpeg Notes

**Construct a 3+1 pattern with trim and concat:**
```bash
# Trim three fast shots to 0.5s each
ffmpeg -i detail1.mp4 -t 0.5 -c copy fast1.mp4
ffmpeg -i detail2.mp4 -t 0.5 -c copy fast2.mp4
ffmpeg -i detail3.mp4 -t 0.5 -c copy fast3.mp4

# Trim the held shot to 3.0s
ffmpeg -i wide_shot.mp4 -t 3.0 -c copy slow_shot.mp4

# Concatenate all four
printf "file 'fast1.mp4'\nfile 'fast2.mp4'\nfile 'fast3.mp4'\nfile 'slow_shot.mp4'\n" > 3plus1.txt
ffmpeg -f concat -safe 0 -i 3plus1.txt -c copy output.mp4
```

**Python generator for multi-repetition 3+1 sequences:**
```python
def build_3plus1(fast_shots, held_shot, fast_dur=0.5, held_dur=3.0, output="output.mp4"):
    """
    fast_shots: list of paths to fast-shot video files (at least 3)
    held_shot: path to the held shot video file
    """
    with open("segments.txt", "w") as f:
        for shot in fast_shots[:3]:
            f.write(f"file '{shot}'\n")
            f.write(f"duration {fast_dur}\n")
        f.write(f"file '{held_shot}'\n")
        f.write(f"duration {held_dur}\n")
    
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", "segments.txt", "-c", "copy", output
    ])
```
