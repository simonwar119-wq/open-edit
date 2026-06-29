---
name: hook-3s
description: |-
  A narrative structure that delivers a compelling visual or conceptual hook within the first 3 seconds of a video, capturing viewer attention before they scroll past.
category: narrative-structure
complexity: low
requires_audio: false
ffmpeg_available: false
source:
  origin: "Digital attention economy — platform research by YouTube (2012), Facebook (2014), TikTok (2018) showing that >50% of viewers are lost in the first 3 seconds"
  first_documented: "YouTube Creator Academy, 'How to Hook Viewers in the First 3 Seconds' (2012); Wistia video marketing research (2014)"
last_updated: 2026-05-13
---

## Definition

The **3-second hook** (also called **the thumb-stopper**, **first-frame rule**, or **hook-3s**) is a narrative opening strategy that front-loads the most visually compelling, emotionally provocative, or curiosity-inducing content into the first 0–3 seconds of a video. The goal is to arrest the viewer's scrolling behavior on social media platforms and compel them to stop and watch.

The hook operates at the neurological level of **orienting response** — the brain's automatic attention shift toward novel, surprising, or salient stimuli. In the scrolling feed context, the first 3 seconds compete against every other video vying for the viewer's thumb-pause. A strong hook creates an "information gap" that the viewer must close by watching further.

The hook can take several forms:
- **Visual spectacle**: Split-screen action, explosive motion, dramatic reveal
- **Curiosity gap**: A question implied by the imagery, an unexpected juxtaposition
- **Emotional trigger**: A face with strong expression, a heartwarming moment, a shocking image
- **Pattern interrupt**: Something that breaks the expected visual flow of the feed

**Nike "You Can't Stop Us"** opens with exactly this principle: in the first 0.5 seconds, a split-screen appears showing two athletes in mirrored poses. There's no title card, no logo, no fade-in — just pure visual action. The audience is hooked before they can look away. By the time Rapinoe's first words register, the viewer has already committed to watching.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `hook_type` | enum | `visual-spectacle` / `curiosity-gap` / `emotional-trigger` / `pattern-interrupt` / `question` | `visual-spectacle` | The psychological mechanism of the hook. |
| `hook_timing_s` | float | 0.0–3.0 | 0.0 | When the hook element first appears. 0.0 = first frame. Up to 3.0 = late hook (higher risk). |
| `hook_duration_s` | float | 0.3–3.0 | 1.5 | How long the hook element is displayed before the narrative proper begins. |
| `info_gap_urgency` | enum | `low` / `medium` / `high` | `high` | How urgently the hook creates an unanswered question. High = viewer must watch to find out. |
| `has_title_card` | bool | true / false | false | Whether a title or logo appears before the hook. Generally harmful to retention (delaysthe hook). |
| `platform_optimization` | enum | `short-form` / `long-form` / `both` | `short-form` | Whether the hook is optimized for <60s content (immediate hook) or also works for longer content. |
| `hook_reinforcement` | enum | `none` / `loop` / `slow-motion-play` | `none` | Whether the hook is reinforced (e.g., the first 0.5s plays in slow-motion or loops before the video proceeds). |

## Usage Scenarios

- **Ad opening (Nike "You Can't Stop Us")**: First frame: split-screen with two athletes in mirrored pose. No fade-in, no logo, no music swell — just raw visual match-cut. The hook says "watch this" before the brain can form a question about it.

- **Travel video opening (Qmike travel/lifestyle)**: First 2 seconds: a time-lapse of a dramatic landscape (mountain sunrise, city skyline at sunset) that cuts from a macro detail into the hero shot. The visual spectacle arrests scrolling and sets the location's emotional tone.

- **Food content hook (Qmike food)**: First 2 seconds: a close-up of food being cut — the knife slicing through a crust, steam rising, sauce spilling. The visceral texture and implied taste create an immediate sensory hook that food-scrollers can't resist.

- **Product launch (brand content)**: First 1 second: the product is shown in an unexpected context or with dramatic lighting that makes it look unfamiliar. The curiosity gap makes the viewer stay to "recognize" it.

## Source Examples

| Source | Usage | Hook Type |
|--------|-------|-----------|
| **Nike "You Can't Stop Us" (2020)** | First frame: split-screen mirrored athletes. No title, no delay. The match-cut action IS the hook. | visual-spectacle (t=0.0s) |
| **Qmike样片 (travel)** | First 2s: dramatic time-lapse of mountain peak at sunrise, then cut to subject's face. The landscape IS the hook. | visual-spectacle / emotional-trigger (t=0.0s) |
| **Apple "Snowbrawl" (2025)** | First frame: a snowball flies directly toward the camera lens. The impending impact hooks the viewer. | visual-spectacle / pattern-interrupt (t=0.0s) |
| **Honda "The Cog" (2003)** | First frame: a close-up of a gear clicking into place. No context, no title. The mechanical mystery hooks the viewer. | curiosity-gap (t=0.0s) |
| **TikTok viral recipe videos** | First 2s: the finished dish being drizzled with sauce, then a smash cut to "here's how I made it." The result-first hook is the platform standard. | visual-spectacle (t=0.0s) |

## Related Techniques

- [cold-open](cold-open.md) — A 3-second hook is a type of cold open (the video starts as if it's already begun). Cold open is the broader technique; hook-3s quantifies the first-3-seconds constraint.
- [in-medias-res](in-medias-res.md) — Hooks that start in the middle of action overlap with in-medias-res. Hook-3s emphasizes the retention imperative; in-medias-res emphasizes narrative structure.
- [chronological](chronological.md) — A chronological opening (title → setup → action) is the opposite of hook-3s. Hook-3s front-loads the best content, then backfills context.
- [reveal-payoff](reveal-payoff.md) — The hook can be the beginning of a reveal: "what is that?" → progressive reveal → full payoff at the end.

## Editorial Notes

**Do NOT** put a logo, title card, or fade-from-black in the first 3 seconds of any social media video. Every millisecond without content is a viewer lost.

**Platform-specific hook timing:**
- TikTok: First 1–2 seconds is critical (users scroll fast)
- Instagram Reels: First 2–3 seconds
- YouTube Shorts: First 3 seconds
- YouTube long-form: First 5–10 seconds (lower scroll speed, higher commitment)
- TV commercials: First 1 second (cannot be skipped)
