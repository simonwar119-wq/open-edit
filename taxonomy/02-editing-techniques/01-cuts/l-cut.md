---
name: l-cut
description: |-
  A split edit where the video from the next shot appears before its corresponding audio transitions, or more classically, the audio from the previous shot continues playing over the incoming visuals.
category: cut
complexity: medium
requires_audio: true
ffmpeg_available: true
source:
  origin: "Classical continuity editing, formalized in Hollywood's studio era (1930s–1950s)"
  first_documented: "Karel Reisz, The Technique of Film Editing (1953)"
last_updated: 2026-05-13
example_videos:
  - url: "https://www.youtube.com/watch?v=1ckIH4C7IvA"
    duration: "0:51"
    author: "av college"
    title: "L Cuts"
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

An **L-cut** (also called **audio lag** or **split edit**) is a split editing technique with two common interpretations:

1. **Classical definition**: The audio from clip A continues playing over the beginning of clip B's video. The viewer hears the previous scene's dialogue, music, or ambient sound while watching the new visuals. On a timeline, clip A's audio track extends under clip B's video track, forming an **L** shape.

2. **Alternative definition (less common)**: The video of clip B appears before its audio — the reverse of a J-cut. This usage is debated; many editors use "L-cut" as a catch-all for any split edit and specify direction with "audio lead" (J-cut) vs "audio lag" (L-cut).

The L-cut is the mirror image of the J-cut. While J-cuts **pull** the viewer forward with future audio, L-cuts **hold** the viewer in the previous moment's emotional or narrative context while the visuals move ahead. This makes L-cuts ideal for reaction shots, emotional transitions, and moments where the audio carries narrative weight that should persist across visual changes.

## Parameters

| Parameter | Type | Range | Default | Notes |
|---|---|---|---|---|
| `video_offset_s` | float | 0.1 to 10.0 | 0.5 | How many seconds the video of clip B appears before clip B's audio replaces clip A's audio. |
| `crossfade_duration_s` | float | 0.0 to 2.0 | 0.1 | Overlap duration between clip A's audio fade-out and clip B's audio fade-in. |
| `audio_carry_mode` | enum | `full` / `duck` / `fade` | `full` | How clip A's audio behaves during the overlap: full volume, ducked under clip B's eventual audio, or fading out gradually. |
| `video_transition` | enum | `hard-cut` / `cross-dissolve` / `none` | `hard-cut` | Visual transition at the video cut point (clip A video → clip B video). |
| `emotional_intent` | enum | `contemplative` / `reactive` / `suspenseful` / `bridging` | `bridging` | The narrative purpose of the L-cut, influencing recommended overlap duration. |

## Usage Scenarios

- **Reaction shots (dialogue scenes)**: Character A finishes speaking, cut to Character B's reaction while still hearing Character A's final words. The visual focus shifts to the listener while the dialogue context remains, creating emotional depth. Common in interview-based content and narrative film.

- **Emotional transitions (Qmike travel/lifestyle)**: A sunset shot's ambient wind sounds or music continue playing as the video cuts to the next morning's breakfast scene. The audio bridges the temporal gap, making the time jump feel emotionally continuous rather than jarring.

- **Narrative voice-over across b-roll**: The subject's voice-over narration from one section continues over visuals of the next section. This maintains narrative flow and prevents the voice-over from feeling disconnected from the images.

- **Music-driven transitions (Nike / Qmike)**: The musical phrase from one sequence extends into the next visual sequence, sustaining the emotional tone even as the imagery changes completely.

## Source Examples

| Source | Usage | Timestamp Reference |
|--------|-------|-------------------|
| **Qmike样片** (travel/lifestyle) | Ambient audio from scenic shots (waves, wind) continuing over the next activity sequence; music carried across scene changes | Transition points between location segments |
| **Apple "Snowbrawl"** | Snow crunch sounds and winter ambiance persisting across cuts between wide and close-up action shots | Throughout snowball fight sequence |
| **Honda "The Cog"** | The rhythmic musical score and mechanical soundscape carries across visual cuts between different parts of the chain reaction | Entire ad — the musical continuity is essential |
| **Nike "You Can't Stop Us"** | Crowd roar and commentary audio from one sport segment continues over the visuals of a different sport, uniting disparate imagery | Throughout split-screen transitions |

## Related Techniques

- [j-cut](j-cut.md) — The reverse split edit: audio leads, video follows
- [hard-cut](hard-cut.md) — Direct cut with no audio overlap; the opposite approach
- [match-cut](match-cut.md) — Can be paired with L-cut audio carry-over for powerful emotional effects

## FFmpeg Notes

L-cuts require offsetting audio and video tracks in the timeline, similar to J-cuts but in the opposite direction (audio from clip A extends into clip B's video).

**Basic L-cut with two clips (video of B appears while audio of A continues):**
```bash
# Using filter_complex to handle audio offset
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "\
    [0:a]adelay=0|0[aA]; \
    [1:a]adelay=500|500[aB]; \
    [aA][aB]acrossfade=d=0.3:c1=tri:c2=tri[aout]; \
    [0:v]trim=duration=5[vA]; \
    [1:v]setpts=PTS-STARTPTS+0.5/TB[vB]; \
    [vA][vB]concat=n=2:v=1:a=0[vout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**In practice (DaVinci Resolve / Premiere Pro):**
- Extend clip A's audio track into clip B's video region on the timeline
- Trim clip B's audio start point to align with clip A's audio transition
- Apply crossfade between the two audio clips at the intended hand-off point

**Python (ffmpeg-python) helper concept:**
```python
# Placeholder — full implementation pending
# def apply_l_cut(clip_a_path, clip_b_path, video_offset_s=0.5, crossfade_s=0.1, output_path):
```
