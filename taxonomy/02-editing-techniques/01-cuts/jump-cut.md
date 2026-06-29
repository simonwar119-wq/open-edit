---
name: jump-cut
description: |-
  An abrupt cut between two sequential shots of the same subject, where the camera position changes only slightly — creating a noticeable discontinuity in time, space, or posture.
category: cut
complexity: low
requires_audio: false
ffmpeg_available: true
source:
  origin: "Jean-Luc Godard, Breathless (À bout de souffle, 1960) — famously used jump cuts as a stylistic rejection of continuity editing rules"
  first_documented: "André Bazin, What Is Cinema? (1967); widely analyzed in film studies since the 1960s"
last_updated: 2026-05-13
---

## Definition

A **jump cut** is a cut between two consecutive shots of the same subject where the framing varies only slightly, causing the subject to appear to "jump" abruptly from one position to another. This creates a noticeable discontinuity that violates classical continuity editing rules (which mandate at least a 30° change in camera angle or a significant change in shot scale between takes of the same subject).

Jump cuts deliberately break the illusion of continuous time and space. They are used for:

- **Pacing compression**: Removing dead time within a single take (e.g., cutting out pauses in a monologue)
- **Stylistic emphasis**: Creating a jarring, energetic, or self-aware tone
- **Time ellipsis**: Showing the passage of time within the same location without a dissolve or other transition
- **Disorientation**: Intentionally unsettling the viewer to reflect a character's psychological state

Jump cuts were historically considered amateur mistakes (the "jump cut rule" was a hallmark of professional Hollywood editing). Godard's *Breathless* (1960) transformed them into a deliberate artistic device, and they became central to the French New Wave aesthetic. Today, jump cuts are ubiquitous in YouTube vlogs, TikTok content, and modern digital-first video — where they serve primarily as a pacing tool to condense talking-head content.

## Parameters

| Parameter | Type | Range | Default | Notes |
|---|---|---|---|---|
| `frame_change_pct` | float | 1.0 to 50.0 | 10.0 | Percentage of frame dimension by which the subject's position changes. 1% = subtle jump, 50% = completely different composition. |
| `time_jump_s` | float | 0.1 to 30.0 | 1.0 | Amount of time removed between the two shots. Longer jumps create more noticeable discontinuity. |
| `cut_count` | integer | 1 to 20 | 1 | Number of consecutive jump cuts applied to the same footage stretch (creates a staccato effect). |
| `transition` | enum | `hard-cut` / `cross-dissolve` / `none` | `hard-cut` | Most jump cuts are hard cuts; dissolve jump cuts create a dreamier discontinuity. |
| `audio_continuity` | enum | `continuous` / `split` / `reverb` | `continuous` | How the audio handles the time jump. Continuous = no audio cut (just video jumps). Split = audio also jumps. Reverb = audio crossfade with artificial reverb. |
| `intensity` | enum | `subtle` / `moderate` / `aggressive` | `moderate` | Overall perceptual impact. Subtle = short time jump, minimal frame change. Aggressive = large jump, visible stutter. |

## Usage Scenarios

- **Talking-head compression (Qmike vlog/lifestyle)**: The most common modern use. A person speaking to camera has pauses, hesitations, or filler words removed by jump-cutting between nearly identical frames. The result is a tighter, faster-paced monologue. Qmike's travel vlogs use this heavily for sit-down narration segments.

- **Energetic montage sequences (Nike / Qmike)**: Series of jump cuts on the same action (a runner's stride, a chef's knife chop) to create rhythmic, staccato visual energy. Often synchronized to a musical beat.

- **Stylized opening sequences (Apple "Snowbrawl")**: Jump cuts on characters' faces or actions to establish chaotic energy before settling into the main narrative. Less common in Apple's polished aesthetic, but used occasionally for emphasis.

- **Time compression within a scene**: A person packing a suitcase shown in 3 rapid jump cuts: shirt, shoes, jacket — condensing 2 minutes of real time into 3 seconds.

## Source Examples

| Source | Usage | Notes |
|--------|-------|-------|
| **Qmike样片** (travel/lifestyle) | Heavy use in talking-head sections; occasional jump-cut montages for packing/preparation sequences | Most extensive use among the 4 analyzed sources |
| **Nike "You Can't Stop Us"** | Subtle jump cuts within individual athlete sequences to compress time while maintaining rhythmic pacing | Secondary technique — split-screen matching is primary |
| **Apple "Snowbrawl"** | Minimal use — Apple's continuity-editing aesthetic mostly avoids jump cuts | Occasional use for comic effect in character reactions |
| **Honda "The Cog"** | Not used — the single-take illusion requires continuous action across cuts | Incompatible with the match-cut-heavy approach |

## Related Techniques

- [hard-cut](hard-cut.md) — Jump cuts are a specific type of hard cut with a discontinuous subject
- [smash-cut](smash-cut.md) — Similar abruptness but different intent: smash cuts contrast tone, jump cuts compress time
- [match-cut](match-cut.md) — Opposite philosophy: match cuts seek seamlessness, jump cuts seek visibility

## FFmpeg Notes

Jump cuts are straightforward to implement in FFmpeg by trimming sections from a single clip and concatenating the remaining segments.

**Basic jump cut (remove 1s from the middle):**
```bash
# Extract segments before and after the jump
ffmpeg -i input.mp4 -filter_complex "\
  [0:v]trim=start=0:end=2,setpts=PTS-STARTPTS[v1]; \
  [0:v]trim=start=3:end=10,setpts=PTS-STARTPTS[v2]; \
  [v1][v2]concat=n=2:v=1:a=0[vout]; \
  [0:a]atrim=0:2[a1]; \
  [0:a]atrim=3:10[a2]; \
  [a1][a2]concat=n=2:v=0:a=1[aout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**Multi-jump cut (remove multiple sections — staccato effect):**
```bash
# Remove 0.5s segments every 2s throughout a clip
# Use a script to generate the complex filter dynamically
```

**Python helper concept for detecting jump-cut candidates:**
```python
# Placeholder — would use ssim or histogram differences to find similar frames
# def find_jump_cut_candidates(video_path, similarity_threshold=0.95):
#     # Detect consecutive frames with minimal visual change
#     # Return timestamps where jump cuts are possible
```
