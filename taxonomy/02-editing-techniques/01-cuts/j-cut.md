---
name: j-cut
description: |-
  A split edit where the audio from the next shot begins before its corresponding video, creating a smooth auditory bridge that primes the viewer for the incoming visual.
category: cut
complexity: medium
requires_audio: true
ffmpeg_available: true
source:
  origin: "Classical continuity editing, formalized in Hollywood's studio era (1930s–1950s)"
  first_documented: "Karel Reisz, The Technique of Film Editing (1953)"
last_updated: 2026-05-13
example_videos:
  - url: "https://www.youtube.com/watch?v=VqmEwEfOVE0"
    duration: "0:20"
    author: "av college"
    title: "J-Cuts"
  - url: "https://www.youtube.com/watch?v=VDHRpDIB1Uc"
    duration: "2:59"
    author: "Calvisions"
    title: "Video Editing 101"
  - url: "https://www.youtube.com/watch?v=7w8iQK5AnNk"
    duration: "1:02"
    author: "Danny Molyneux"
    title: "Danny & Molly learn about J-Cuts and L-Cuts"
---

## Definition

A **J-cut** (also called **audio lead** or **L-cut** in some overlapping terminology — though strict usage distinguishes them) is a split edit technique where the audio track of clip B starts playing **before** the video track of clip B appears on screen. The viewer hears the next scene's dialogue, sound effect, or music while still watching the current scene's visuals. This overlap psychologically prepares the audience for the transition, making the cut feel less abrupt and more organic.

The name "J-cut" comes from the shape the two clips form on a timeline when the audio track extends backward relative to the video — resembling the letter **J**.

J-cuts are fundamental to dialogue scenes (hearing the next speaker before seeing them), narrative transitions (hearing the next location's ambient sound while still on the current shot), and music-driven sequences (music crossfading before the visual cut).

## Parameters

| Parameter | Type | Range | Default | Notes |
|---|---|---|---|---|
| `audio_offset_s` | float | -10.0 to -0.1 | -0.5 | How many seconds the audio of clip B precedes the video cut. Negative values mean audio starts before video. |
| `crossfade_duration_s` | float | 0.0 to 2.0 | 0.1 | Overlap duration between clip A's audio fade-out and clip B's audio fade-in at the J-cut point. |
| `audio_type` | enum | `dialogue` / `ambient` / `music` / `sfx` | `ambient` | The type of audio leading the transition. Affects how jarring or natural the J-cut feels. |
| `video_transition` | enum | `hard-cut` / `cross-dissolve` / `none` | `hard-cut` | Visual transition applied at the video cut point while the audio lead is active. |
| `mix_strategy` | enum | `crossfade` / `duck` / `hard-switch` | `crossfade` | How clip A's audio transitions to clip B's audio at the video cut point. |
| `fade_in_s` | float | 0.0 to 3.0 | 0.0 | Optional fade-in duration for the leading audio of clip B (smoother entry). |

## Usage Scenarios

- **Dialogue scene transitions (Qmike travel/lifestyle)**: In a vlog-style travel video, the subject's voice-over starts while the previous b-roll is still playing. For example: viewer watches a slow-motion shot of a street market, hears the narrator say "And then I found this tiny ramen shop..." — then the video cuts to the shop. This keeps pacing tight while maintaining narrative flow.

- **Location atmosphere preview (Qmike lifestyle)**: Ambient sound of the next location (ocean waves, city traffic, café chatter) enters before the visual cut. This builds spatial anticipation — the viewer's ears tell them where they're going before their eyes confirm it.

- **Music-driven sequence transitions (Nike / Qmike)**: The next track's beat or melody begins during the final seconds of the current visual sequence, aligning the visual cut with the musical downbeat for a seamless energy handoff.

## Source Examples

| Source | Usage | Timestamp Reference |
|--------|-------|-------------------|
| **Qmike样片** (travel/lifestyle) | Ambient sound J-cuts between location transitions; voice-over J-cuts leading into b-roll segments | Throughout — signature technique for vlog pacing |
| **Apple "Snowbrawl"** | Snowball impact sounds from the next shot briefly overlap the current shot's ending, creating percussive continuity | During action sequence |
| **Honda "The Cog"** | Mechanical sound effects from the next part in the chain reaction bleed into the current shot's final frames | Transition segments |
| **Nike "You Can't Stop Us"** | Overlapping crowd noise and music between split-screen segments to maintain rhythmic momentum | Throughout |

## Related Techniques

- [l-cut](l-cut.md) — The reverse split edit: video leads, audio trails (audio from clip A continues into clip B)
- [hard-cut](hard-cut.md) — Direct cut with no audio overlap; the opposite of a J-cut
- [match-cut](match-cut.md) — Can be enhanced by J-cut audio overlap for smoother perceptual transitions

## FFmpeg Notes

J-cuts require separate audio and video track handling since the audio offset differs from the video cut point.

**Basic J-cut with two clips (audio leads by 0.5s):**
```bash
# In a streaming/complex filter context, use adelay and acrossfade
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:a]adelay=0|0[aA]; \
    [1:a]adelay=500|500[aB]; \
    [aA][aB]acrossfade=d=0.1:c1=tri:c2=tri[aout]; \
    [0:v][1:v]concat=n=2:v=1:a=0[vout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**More sophisticated approach with separate audio tracks (DaVinci Resolve recommended for fine control):**
- Layer clip B's audio track 0.5s before the video cut point on the timeline
- Apply a short crossfade (0.1s) at the transition between the two audio clips
- Use a hard-cut on the video track at the intended cut point

**Python (ffmpeg-python) helper concept:**
```python
# Placeholder — full implementation pending
# def apply_j_cut(clip_a_path, clip_b_path, audio_offset_s=0.5, output_path):
```
