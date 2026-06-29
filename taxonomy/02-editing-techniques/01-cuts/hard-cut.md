---
name: hard-cut
description: |-
  An instantaneous transition between two shots with no optical effect, dissolve, or any other transitional treatment — the most basic and most common editing technique.
category: cut
complexity: low
requires_audio: false
ffmpeg_available: true
source:
  origin: "Fundamental to motion picture editing since the Lumière brothers' first films (1895); the default assembly method of all film editing"
  first_documented: "Edwin S. Porter, The Great Train Robbery (1903); codified by D.W. Griffith (1910s)"
last_updated: 2026-05-13
---

## Definition

A **hard cut** (also called a **straight cut**, **direct cut**, or simply a **cut**) is the simplest and most common transition in video editing: frame N of clip A is followed immediately by frame 1 of clip B, with no dissolve, wipe, fade, or any other optical effect bridging them. The transition is instantaneous — 0 seconds duration.

Hard cuts are the **default transition** in virtually all editing workflows. They are so fundamental that they are often invisible to viewers — audiences accustomed to film language process them subconsciously. The hard cut's power lies in its invisibility: when placed at the right moment (between actions, at a gesture's peak, on a musical beat), the viewer's brain naturally bridges the gap without noticing the join.

Despite being labeled a "transition" in some taxonomies (including this project's schema), the hard cut is technically the **absence of a transition** — it is the baseline against which all other transitions are measured.

**Important taxonomy note:** In Open Edit's schema v1, `hard-cut` is classified under the `transition` enum (not the `cut` enum) for practical workflow reasons — it's the zero-duration endpoint of the transition spectrum. However, in common editing terminology, "hard cut" and "straight cut" (the `cut` enum value) describe the same technique: a direct join with no transitional treatment.

## Parameters

| Parameter | Type | Range | Default | Notes |
|---|---|---|---|---|
| `cut_point_s` | float | 0.0 to duration | N/A | The precise timestamp of the cut. For hard cuts, placement is everything — the ideal cut point depends on motion, dialogue rhythm, or music beat. |
| `cut_type_override` | enum | `hard-cut` / `straight-cut` | `hard-cut` | Both values produce an instantaneous transition; included for taxonomy compatibility with both the `cut` and `transition` enums. |
| `surrounding_context` | enum | `action-peak` / `dialogue-pause` / `beat-sync` / `eyeline` | `action-peak` | The narrative context that determines optimal cut placement. Different contexts demand different cut points. |

## Usage Scenarios

- **Default assembly (all sources)**: Every video is assembled primarily with hard cuts. Transitions are the exception, hard cuts are the rule. In all four analyzed sources, 80–95%+ of edits are hard cuts.

- **Action continuity (Apple "Snowbrawl")**: Hard cuts between different angles of the same continuous action — a child winding up to throw, cut to a different angle of the throw in flight. The hard cut preserves the action's momentum.

- **Dialogue editing (Qmike travel/lifestyle)**: Hard cuts between different takes or different subjects during a conversation or vlog segment. The rhythm of hard cuts in dialogue defines the pacing.

- **Beat-synced editing (Nike / Qmike)**: Hard cuts precisely aligned with musical downbeats, creating a direct, punchy audiovisual connection. No dissolve softens the impact — the hard cut hits exactly on the beat.

- **Montage sequences (Honda "The Cog")**: The chain reaction uses hard cuts between each mechanical component. The visual match between parts creates continuity; a dissolve would spoil the precise mechanical rhythm.

## Source Examples

| Source | Usage | Hard Cut Percentage (Estimated) |
|--------|-------|-------------------------------|
| **Nike "You Can't Stop Us"** | Primary transition throughout — split-screen transitions are hard cuts, not dissolves | ~95% |
| **Apple "Snowbrawl"** | Standard editing — hard cuts between most shots, occasional dissolves for time transitions | ~90% |
| **Honda "The Cog"** | Almost exclusively hard cuts — the single-take illusion requires precise, instantaneous cuts between mechanical parts | ~98% |
| **Qmike样片** | Primary assembly method — hard cuts between b-roll clips, talking-head sections, and location transitions | ~85% |

## Related Techniques

- [jump-cut](jump-cut.md) — A specific type of hard cut where the subject jumps in time/space
- [smash-cut](smash-cut.md) — A hard cut with extreme contrast in tone/volume between the two shots
- [match-cut](match-cut.md) — A hard cut enhanced by visual continuity between the two shots
- [j-cut](j-cut.md) / [l-cut](l-cut.md) — Split edits that combine hard video cuts with overlapping audio

## FFmpeg Notes

Hard cuts are the simplest FFmpeg operation — they are the default behavior of the `concat` filter and the file-level concatenation protocols.

**Simple concatenation of two clips (hard cut):**
```bash
# Using concat demuxer (recommended for same-codec files)
echo "file 'clipA.mp4'" > files.txt
echo "file 'clipB.mp4'" >> files.txt
ffmpeg -f concat -safe 0 -i files.txt -c copy output.mp4
```

**Using filter_complex (works with different codecs/sizes):**
```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vout][aout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**Batch trimming multiple segments into a hard-cut sequence:**
```bash
# Extract segments and join with hard cuts
ffmpeg -i input.mp4 -filter_complex "\
  [0:v]trim=start=0:end=10,setpts=PTS-STARTPTS[seg1v]; \
  [0:a]atrim=0:10[seg1a]; \
  [0:v]trim=start=20:end=30,setpts=PTS-STARTPTS[seg2v]; \
  [0:a]atrim=20:30[seg2a]; \
  [seg1v][seg1a][seg2v][seg2a]concat=n=2:v=1:a=1[vout][aout]" \
  -map "[vout]" -map "[aout]" output.mp4
```

**Note:** When using `-c copy` with concat demuxer, the hard cut is lossless (no re-encoding). When using filter_complex, re-encoding occurs at the cut points.
