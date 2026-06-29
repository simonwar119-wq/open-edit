---
name: problem-solution
description: |-
  A narrative structure that presents a conflict, tension, or undesirable situation (problem), then progresses toward a harmonious or satisfying resolution (solution).
category: narrative-structure
complexity: low
requires_audio: false
ffmpeg_available: false
source:
  origin: "Classical dramatic structure — Freytag's Pyramid (conflict → rising action → resolution); foundational to advertising's 'before and after' format"
  first_documented: "Gustav Freytag, Die Technik des Dramas (1863); modern advertising codification: Rosser Reeves, Reality in Advertising (1961) — the Unique Selling Proposition as problem-solution framework"
last_updated: 2026-05-13
---

## Definition

**Problem-solution** (also called **conflict-resolution**, **before-after**, or **setup-payoff**) is a narrative structure where the first section establishes a undesirable state — a problem, a tension, a lack, a conflict — and the second section shows how that state is resolved, transformed, or overcome.

The structure is the most fundamental narrative pattern in human communication. It maps to the basic cognitive process of recognizing and eliminating dissonance. In advertising, it's the "before and after" format. In storytelling, it's the "hero's journey" in miniature. In social media content, it's the "struggle → life hack" format.

**Apple "Snowbrawl" (2025)** uses problem-solution as its emotional backbone disguised as a fun action piece:
- **Problem (first 60s)**: The "enemy" sister takes the brother's controller. The problem escalates into a full neighborhood snowball war. Sibling antagonism. Chaos and cold.
- **Solution (final 30s)**: The sister offers her controller back. The snowball war transforms into building a snowman together. Siblings laughing, working together, a warm drink at home. The resolution is emotional rather than material — the real problem was not lost controllers but lost connection.

The structure's power is its universality. Any viewer, in any culture, understands the pattern. It's the story form that requires the least cognitive load to follow.

## Parameters

| Parameter | Type | Range | Default | Notes |
|-----------|------|-------|---------|-------|
| `problem_type` | enum | `physical` / `emotional` / `social` / `practical` / `missing-knowledge` | `practical` | The nature of the problem. Physical = broken, blocked. Emotional = sad, lonely. Social = conflict, rivalry. Practical = inefficiency, difficulty. Missing-knowledge = curiosity gap. |
| `solution_type` | enum | `product-fix` / `emotional-resolution` / `skill-mastery` / `reconciliation` / `knowledge-revealed` | `product-fix` | How the problem is solved. Product-fix = a tool/object resolves it. Emotional = feelings change. Skill-mastery = the protagonist learns. Reconciliation = relationships heal. |
| `problem_duration_pct` | float | 0.3–0.7 | 0.55 | Percentage of runtime spent on the problem before the turning point. More problem time = more tension. |
| `turning_point_type` | enum | `character-decision` / `external-event` / `realization` / `product-introduction` | `character-decision` | What triggers the shift from problem to solution. A character decides to act. An external event intervenes. The protagonist realizes something. A product enters the scene. |
| `resolution_clarity` | enum | `explicit` / `implied` / `ambiguous` | `explicit` | How clearly the solution is shown. Explicit = the viewer sees the problem fully resolved. Implied = the viewer infers the solution continues. Ambiguous = the solution is partial or open to interpretation. |
| `show_both_sides` | bool | true / false | true | Whether both the before (problem) and after (solution) are shown on screen, or just implied. |
| `emotional_arc` | enum | `negative-to-positive` / `chaos-to-order` / `cold-to-warm` / `alone-to-together` | `negative-to-positive` | The emotional journey from problem to solution. |

## Usage Scenarios

- **Family dynamics narrative (Apple "Snowbrawl")**: Problem: sibling rivalry escalates into snowball war → Solution: reconciliation, shared activity, warmth at home. The problem-solution arc is hidden beneath the fun action sequences.

- **Cooking tutorial (Qmike food)**: Problem: viewer doesn't know how to make a dish or they have leftover ingredients → Solution: step-by-step guide revealing the completed dish. The problem is "missing knowledge"; the solution is "skill mastery."

- **Travel transformation (Qmike travel/lifestyle)**: Problem: the stress and greyness of city life (shown in desaturated, fast-paced shots) → Solution: arriving at a peaceful natural location (golden hour, slow-motion, wide shots). The problem is emotional (burnout); the solution is spatial (travel as therapy).

- **Product utility (brand content)**: Problem: a daily inconvenience (messy cables, slow phone, hard-to-clean surface) → Solution: the product demonstrating its value in a side-by-side comparison. The classic before-after format.

## Source Examples

| Source | Usage | Problem-Solution Arc |
|--------|-------|---------------------|
| **Apple "Snowbrawl" (2025)** | Problem: sibling rivalry, stolen controller, snowball war isolation → Turning point: sister returns controller → Solution: building snowman together, hot cocoa, sibling bonding. | problem: 60% (chaos/cold), turning: reconciliation gesture, solution: 30% (warmth/together), explicit resolution |
| **Qmike样片 (food)** | Problem: viewer craving/complex recipe → Solution: step-by-step cooking → finished dish hero shot. Implicit problem-solution: the skill gap is closed. | problem: 10% implied (intro), solution: 80% (process), resolution: 10% (dish reveal) |
| **Qmike样片 (travel)** | Problem: city burnout montage → Solution: departure, journey, nature arrival, peace. The structure is the video's emotional narrative. | problem: 15%, turning: leaving, solution: 75%, explicit resolution |
| **Virtually all before-after ads** | Problem: stained clothes, dull hair, cluttered room → Solution: product use → clean, shiny, organized result. | problem: 30%, product intro: 10%, solution: 60%, explicit |

## Related Techniques

- [chronological](chronological.md) — Problem-solution is typically presented chronologically (problem → solution). The chronological order reinforces the causal link.
- [reveal-payoff](reveal-payoff.md) — The solution in problem-solution can be framed as a reveal (the viewer anticipates the solution and is rewarded).
- [hook-3s](hook-3s.md) — The problem can serve as the hook: opening with conflict immediately grabs attention.
- [in-medias-res](in-medias-res.md) — Starting in the middle of the problem (peak conflict) is a powerful variant: the viewer is dropped into the worst moment, then shown how it got there and how it resolves.
- [circular-ending](circular-ending.md) — A problem-solution arc can end by returning to the problem's starting point, now transformed — the "same but different" closure.

## Editorial Notes

The most successful problem-solution structures in social media content are **disguised**. The viewer doesn't feel like they're watching a "problem-solution ad" — they're watching a fun sibling snowball fight (Apple "Snowbrawl") that happens to have an emotional problem-solution arc underneath. The emotional solution (reconciliation) is more powerful than any product solution would be.
