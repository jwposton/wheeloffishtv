---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_plan: 04-05 — Disordered picker (PLT-04)
status: ready
last_updated: "2026-05-25T20:40:28.000Z"
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 26
  completed_plans: 24
  percent: 46
---

# State — Wheel of Fish TV

**Updated:** 2026-05-25 (Phase 4 plan 04 complete)

## Project reference

See: `.planning/PROJECT.md` (updated 2026-05-25)

**Core value:** Mixed random TV playlists across chosen shows honoring true resume semantics per series whenever `ordered`; allow pure chaos rows + global WheelOfFish.

## Current phase

Phase **4 — Playlist mathematics** — **in progress** (4/6 plans complete).

**Current plan:** 04-05 — Disordered picker (PLT-04)

## Immediate next actions

1. Execute 04-05-PLAN.md — disordered picker + last_viewed_at mappers
2. Continue Phase 4 Wave 2 via `/gsd-execute-phase 4`

## Decisions (Phase 4)

- Import fixtures via `unit.fixtures` path for pytest testpaths compatibility
- Default `completion_event=SERIES_COMPLETE` per research assumption A4
- Null `part_index` anchor returns full block in forward expansion (D-07 fallback)
- Sort key `(part_index is None, part_index or 0, id)` for deterministic multipart ordering
- Playlist.default_completion_policy defaults to REMOVE; row policy wins at evaluation (D-14)
- Only SERIES_COMPLETE triggers in v1; season finish returns None (D-11)
- RESTART sets effective_mode=ORDERED; cursor reset via start_index_for_row(restart=True) (D-17)
- start_index_for_row skips ResumeService when restart=True, always returning 0
- Series complete returns len(order_episodes) as exhausted cursor index (D-21)
- next_block advances via max block member position in ordered list, not index + len(block)

## Decisions (Phase 3)

- WOF_PROVIDER drives single-provider installs; legacy WOF_ENABLED_PROVIDERS retained for multi-provider tests
- Session cookie https_only only when ENVIRONMENT=production
- ProtectedRoute requires has_media_link (not just session bootstrap)
- Storybook deferred to Phase 7 (D-20)

## Working notes

- Phase 4 plan 04: `.planning/phases/04-playlist-mathematics/04-04-SUMMARY.md`
- Phase 4 plan 03: `.planning/phases/04-playlist-mathematics/04-03-SUMMARY.md`
- Phase 4 plan 02: `.planning/phases/04-playlist-mathematics/04-02-SUMMARY.md`
- Phase 4 plan 01: `.planning/phases/04-playlist-mathematics/04-01-SUMMARY.md`
- Phase 3 UAT: `.planning/phases/03-minimal-operator-spa-shell/03-UAT-CHECKLIST.md`
- Phase 2 complete: 7/7 plans
- Phase 1 complete: 5/5 plans

---

*Auto-maintain during `/gsd-transition` / `/gsd-progress`.*
