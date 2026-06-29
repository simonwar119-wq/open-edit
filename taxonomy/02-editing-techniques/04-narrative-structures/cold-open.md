---
name: cold-open
description: |-
  A narrative structure where a video begins with a self-contained scene — typically from the middle of the story — before a title sequence, logo, or setup, creating immediate immersion.
category: narrative-structure
complexity: low
requires_audio: false
ffmpeg_available: false
source:
  origin: "Television broadcasting technique popularized in the 1960s (Star Trek, The Man from U.N.C.L.E.); now standard in episodic TV, YouTube, and commercial advertising"
  first_documented: "First attributed to TV producer Quinn Martin (The Fugitive, 1963); formalized as 'cold open' or 'teaser' in television screenwriting guides (1970s)"
last_updated: 2026-05-13
---

## Definition

A **cold open** (also called **teaser scene**, **pre-title sequence**, or **pre-cap**) is a narrative structure where the video begins with a scene that assumes the viewer is already invested, bypassing the usual setup (title cards, logos, introductions, "hey guys welcome back to my channel") and dropping directly into compelling content.

The cold open has four characteristics:
1. **No preamble**: No logo, no title sequence, no intro music — the first frame IS the content
2. **Self-contained**: The scene is coherent on its own, even without the context of the full video
3. **Immediately engaging**: High action, emotion, curiosity, or humor — the cold open must earn the viewer's attention
4. **Seamless transition**: The cold open bleeds into the main content either directly or through a title card/logo after the cold open ends

The cold open differs from hook-3s in **scope**: hook-3s describes the first 3 seconds' attention-capture mechanism; cold open describes a structural pattern where the opening is a full scene (15–90 seconds), separated from the main content by a title sequence or transition. A cold open always includes a hook-3s but also provides enough substance to sustain the viewer through a longer pre-title segment.

Cold open also differs from in-medias-res in **intention**: in-medias-res starts in the middle of the plot and requires backfill to make sense. A cold open may be chronologically positioned at the start of the story — it just skips the introduction and starts with action.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `cold_open_duration_s` | float | 3.0–120.0 | 20.0 | Duration of the cold open before the title/transition. YouTube standard: 15–45s. TV standard: 30–90s. Short-form: 3–10s. |
| `transition_type` | enum | `title-card` / `logo-reveal` / `hard-cut` / `sound-bridge` / `dissolve-to-logo` | `title-card` | What separates the cold open from the main content. Title card = the video title appears. Logo = brand logo transition. Hard cut = abrupt shift to main content. |
| `cold_open_content` | enum | `action-peak` / `emotional-hook` / `comedic-beat` / `curiosity-setup` / `summary` | `action-peak` | What the cold open contains. Action-peak = the most exciting moment of the video. Emotional-hook = a poignant moment. Summary = a highlight reel of what's coming. |
| `brand_delay_s` | float | 0.0–60.0 | 15.0 | How many seconds pass before the brand logo appears. Longer = more immersion before branding. |
| `return_to_timeline` | enum | `chronological-reset` / `continue-from-open` / `time-jump` | `chronological-reset` | Where the main content picks up relative to the cold open. Chronological-reset = go back to the beginning and tell the story that leads to the open. Continue = pick up right after the open. Time-jump = jump to a different time. |

## Usage Scenarios

- **YouTube creator video (Qmike travel/lifestyle)**: The video opens with a 20-second highlight montage of the most stunning moments from the trip — a sunset time-lapse, a food close-up, a laugh with a local — then cuts to the title card "A Day in Tokyo" before the chronological vlog begins. The cold open answers the viewer's unspoken question: "Is this video worth watching?"

- **Brand commercial (Nike "You Can't Stop Us")**: Opens with no preamble — just the split-screen action. No Nike logo appears until the final 5 seconds. The cold open IS the entire 90-second ad (no title sequence needed). This is the extreme form: the whole ad is a cold open.

- **TV episode (Apple "Snowbrawl" as short film)**: Opens with a child's face in close-up, eyes wide with determination, then a snowball flies past the camera. The cold open is 15 seconds of pure action before the title card "Apple — Snowbrawl" appears. Then the narrative resets to the indoor scene (sister taking controller).

- **Podcast/vlog intro (creator content)**: "I almost died today." → 30 seconds of a dramatic story → "Anyway, that's what happened this morning. Welcome back to the channel." The cold open uses the most interesting moment of the episode to hook the viewer before the standard intro.

## Source Examples

| Source | Usage | Cold Open Structure |
|--------|-------|-------------------|
| **Nike "You Can't Stop Us" (2020)** | The entire 90s ad is a cold open — no brand or title appears until the final 5s. The cold open IS the content, and the logo appears as the closing reveal. | 85s cold open, 5s brand reveal, no reset |
| **Apple "Snowbrawl" (2025)** | 15s cold open: snowball flying toward camera → action peek → title card "Snowbrawl" → reset to indoor scene (beginning of chronological narrative). The cold open gives a taste of the climax without context. | 15s cold open, title card, chronological reset to beginning |
| **Qmike样片 (travel)** | 20s highlight montage of the day's best moments → title card "Tokyo Days" → chronological vlog begins at morning. The cold open answers "is this trip worth watching?" before the viewer commits. | 20s cold open, title card, chronological reset |
| **YouTube standard (MrBeast, Casey Neistat)** | 15–60s cold open showing the most intense moment of the video, often with on-screen text previewing the stakes. Then title card → main video begins. | 15-60s cold open, title card, chronological reset |

## Related Techniques

- [hook-3s](hook-3s.md) — The first 3 seconds of a cold open must function as a hook-3s. Cold open extends the concept to a full scene.
- [in-medias-res](in-medias-res.md) — Cold opens are often in-medias-res (starting from the middle of the story), but not always. A cold open can be chronologically first — it just skips the pleasantries.
- [chronological](chronological.md) — After the cold open, many videos reset to chronological order (the "chronological reset"). The cold open is a non-chronological insert at the chronologically-organized narrative.
- [reveal-payoff](reveal-payoff.md) — The cold open can act as the reveal (showing the climax/resolution first), and the main content shows how we got there — a reverse reveal-payoff.
- [circular-ending](circular-ending.md) — A video that starts with a cold open and ends by returning to the same imagery (or a callback to it) creates a satisfying circular structure.

## Editorial Notes

**Platform-specific cold open best practices:**
- **TikTok/Reels/Shorts**: The cold open is just the first 1–3 seconds. No time for a full scene. The hook IS the cold open.
- **YouTube (long-form)**: 15–45s cold open is optimal. Long enough to provide value, short enough not to delay the main content.
- **YouTube (short-form)**: 3–10s cold open. The whole short could BE a cold open.
- **Commercial/TV**: 15–90s cold open. Can constitute the entire content (logo appears only at the end).

**The 3-Second Test:** If you cut the first 3 seconds of your video and nothing of value is lost, you don't have a cold open — you have dead air before the viewer tunes out.
