# Phase 4: Playlist mathematics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 4-playlist-mathematics
**Areas discussed:** Slot allocation, Disordered feathers, Multipart blocks, Completion policies, Rebuild semantics & output length, Rebuild identity

---

## Slot allocation

| Option | Description | Selected |
|--------|-------------|----------|
| Uniform random (Wild shuffle) | Each slot independently picks a random active show | ✓ (default) |
| Balanced shuffle | Pre-allocate N slots evenly across shows, shuffle order | ✓ (optional per playlist) |
| Round-robin | Rotate through shows with random start | ✓ (optional per playlist) |

**User's choice:** Support all three via per-playlist `slot_allocation`; default Wild shuffle. Expose in UI later with plain-language labels under advanced settings.
**Notes:** User asked if per-playlist randomization option would be too archaic — agreed plain labels (Wild / Balanced / Round-robin) are fine for self-host operators.

---

## Disordered feathers

| Option | Description | Selected |
|--------|-------------|----------|
| All episodes | Full series pool including completed | ✓ (base pool) |
| Minus last N watched | Exclude recently watched from pool before random pick | ✓ (N=15) |
| Re-roll on collision | Pick random, re-roll if in recent set | |
| Emission history | Track prior playlist outputs | Deferred |

**User's choice:** Pool = all episodes minus **last 15 watched** (by provider `last_viewed_at` on episode snapshot). Exclude from population before random pick (not re-roll). No repeats within same rebuild. Empty pool → fall back to full list.
**Notes:** User asked if separate history API needed — no; derive from existing `allLeaves` episode fetch once mappers add `last_viewed_at`.

---

## Multipart blocks

| Option | Description | Selected |
|--------|-------------|----------|
| Ordered: tail from resume | Block from resume part forward through group | ✓ |
| Ordered: full block from part 1 | Always include all parts from start of group | |
| Disordered: full block on any part hit | All parts when random lands on multipart | ✓ |
| Disordered: single episode only | | |

**User's choice:** Ordered = tail from resume forward. Disordered = full block if any part selected; overrides last-15 exclusion for those parts.

---

## Completion policies

| Option | Description | Selected |
|--------|-------------|----------|
| Series complete only | v1 completion event | ✓ |
| Season complete | Mid-show season boundary | Deferred v1 |
| Default policy remove | Drop show when complete | ✓ |
| Per-playlist default policy | User sets playlist-level default | ✓ |
| Per-row override | Row policy wins | ✓ |

**User's choice:** Series complete triggers policy. Default **remove**; each playlist has configurable default completion policy; per-row override when adding show. User initially conflated "disordered on complete" with automatic behavior — clarified as one of three explicit policies.

---

## Rebuild semantics & output length

| Option | Description | Selected |
|--------|-------------|----------|
| Fresh rebuild each run | Replace entire playlist | ✓ |
| Running queue / refill | Top up to N on schedule | |
| N = slots (multipart expands) | Output may exceed N | ✓ |
| Default N = 20 | Per-playlist configurable | ✓ |
| Shortfall: emit fewer | No backfill | ✓ |

**User's choice:** Fresh nightly menu (Model A); ordered continuity via Plex resume not list carryover. Default 20 slots per playlist. Full refresh on user-defined schedule (Phase 5).

---

## Rebuild identity

| Option | Description | Selected |
|--------|-------------|----------|
| Stable same calendar day | Identical output if rebuilt twice same day | |
| Fresh each invocation | Scheduled and manual rebuild both run full logic anew | ✓ |

**User's choice:** "Rebuild now" runs same pipeline as scheduled job — true rebuild with fresh output each invocation.

---

## Claude's Discretion

Balanced/round-robin allocation details, module layout, Hypothesis adoption, Jellyfin timestamp mapping specifics.

## Deferred Ideas

- Season-complete completion event
- Emission-history anti-repeat layer
- Per-playlist schedule (Phase 5)
