---
name: chronological
description: |-
  A narrative structure that presents events in the order they occur in time, creating a clear causal chain from beginning to end.
category: narrative-structure
complexity: low
requires_audio: false
ffmpeg_available: false
source:
  origin: "The most fundamental narrative structure — predates recorded history (oral storytelling); formalized as 'linear narrative' in Aristotle's Poetics (~335 BC)"
  first_documented: "Aristotle, Poetics (~335 BC) — unity of action requiring events to follow in probable or necessary sequence"
last_updated: 2026-05-13
---

## Definition

**Chronological** (also called **linear narrative**, **temporal order**, or **straight timeline**) is a narrative structure where events are presented in the sequence they occur in the story's timeline. The structure follows a simple A→B→C logic: each scene or sequence directly follows its predecessor in time, and the viewer understands the causal relationships because they witness each step in order.

Chronological structure is the **default narrative mode** — the one that requires the least cognitive effort from the viewer. It is the most accessible structure across all cultures, age groups, and attention levels. Its strength is clarity; its weakness is predictability.

Both **Apple "Snowbrawl"** and **Honda "The Cog"** use chronological structure:
- **Apple "Snowbrawl"**: The story begins at the house (sister takes controller), follows the brother's chase outside, escalates through the snowball fight, and resolves with the siblings reconciling. Each event causally leads to the next. The viewer never has to ask "when is this happening?"
- **Honda "The Cog"**: The chain reaction begins with a single gear clicking and progresses sequentially through each mechanical step until the car rolls off the ramp. The entire ad is a literal timeline — part A triggers part B triggers part C. The chronological structure mirrors the mechanical causality.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `time_span` | enum | `continuous` / `condensed` / `extended` | `condensed` | How the timeline relates to real time. Continuous = real-time (or near). Condensed = hours/days compressed into minutes. Extended = slow-motion or time-stretched. |
| `ellipsis_type` | enum | `none` / `hard-cut` / `dissolve` / `title-card` | `hard-cut` | How time jumps are handled. In strict chronological, ellipses should be minimal, but practical editing often skips unimportant moments. |
| `cause_effect_clarity` | enum | `explicit` / `implied` / `ambiguous` | `explicit` | How clearly the causal link between events is shown. Explicit = the viewer sees action A cause result B. Implied = the viewer infers it. Ambiguous = open to interpretation. |
| `reversibility` | bool | true / false | false | Whether the chronological order could be reversed without losing meaning. True = symmetrical timeline (events are not causally dependent). False = irreversible chain. |
| `temporal_markers` | enum | `none` / `visual-cues` / `text-titles` / `audio-cues` | `visual-cues` | How the passage of time is communicated. Visual cues = light changes, clothing changes, weather. Text = "3 hours later." Audio = clock sounds, music evolution. |
| `pace_variation` | enum | `constant` / `accelerating` / `decelerating` / `variable` | `variable` | Whether the pacing is uniform or changes across the timeline. Variable is most natural (different scenes need different pacing). |

## Usage Scenarios

- **Chain reaction narrative (Honda "The Cog")**: The entire ad is a single chronological chain. Part A hits part B, which rolls to part C, which triggers part D. The chronological structure is not just a storytelling choice — it's integral to the content. Breaking chronology would break the mechanical logic.

- **Day-in-the-life travel vlog (Qmike travel/lifestyle)**: The video follows the subject chronologically through a single day: morning coffee → exploring streets → lunch → afternoon activity → sunset → dinner → night scene. The chronological structure gives the viewer a vicarious sense of having lived that day alongside the subject.

- **Recipe/cooking process (Qmike food)**: Prep → cook → plate → taste. Chronological order is essential: the viewer needs to see each step in sequence to learn the recipe. Breaking chronology would confuse the instructions.

- **Event coverage (sports, brand event)**: The event unfolds in real time or condensed real time. Opening → main event → conclusion. The viewer experiences the event's natural rhythm.

## Source Examples

| Source | Usage | Chronological Type |
|--------|-------|-------------------|
| **Honda "The Cog" (2003)** | The chain reaction is a literal timeline. Mechanical causality drives the narrative order. Reversing would break the premise. | continuous (real-time chain reaction), explicit cause-effect, pure linear |
| **Apple "Snowbrawl" (2025)** | Indoor → chase outside → snowball fight → reconciliation → indoor. Every scene follows the previous in time. The viewer tracks the sibling relationship through its temporal evolution. | condensed (30min of snowball fight into 2min video), explicit cause-effect |
| **Qmike样片 (travel/lifestyle)** | A day-in-the-life: morning routine → daytime exploration → evening dinner → night lights. Each segment follows the sun's progression. | condensed (full day into 3-8 min), variable pace |
| **Qmike样片 (food)** | Recipe in chronological order: ingredient intro → step 1 → step 2 → ... → finished dish → tasting. | condensed (cooking time compressed), explicit cause-effect |

## Related Techniques

- [problem-solution](problem-solution.md) — Problem-solution narratives are typically presented chronologically (problem first, then solution) to establish the causal relationship.
- [reveal-payoff](reveal-payoff.md) — Can be chronological (as in Honda The Cog — parts shown one by one in order) or non-chronological.
- [in-medias-res](in-medias-res.md) — The opposite approach: start at the end/climax, then backtrack chronologically to show how we got there.
- [hook-3s](hook-3s.md) — In chronological narrative, the hook is the first event. If the first event isn't hook-worthy, the chronological structure fails to capture attention.
- [circular-ending](circular-ending.md) — A chronological narrative can end by returning to the starting imagery/themes, creating a temporal loop that reinforces the arc.

## Editorial Notes

**When to choose chronological:**
- The causal chain is the story (Honda "The Cog" wouldn't work any other way)
- The viewer needs to learn a process (recipes, tutorials)
- The content is inherently temporal (a journey, a day, an event)
- The audience has low attention tolerance (linear is easiest to follow)

**When to avoid chronological:**
- The opening scene lacks hook potential (start in-medias-res instead)
- The causality is obvious and doesn't need sequential demonstration
- Emotional impact depends on revealing information out of order
- The content needs to feel dynamic and unpredictable (chronological can feel flat)

**Combining with rhythm patterns:** Even chronological narratives need varied editing rhythm. A chronological travel vlog should use accelerando for the city walking section, breath-rhythm for the sunset moment, and beat-sync for the night-life montage — all within the same chronological container.
