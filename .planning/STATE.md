---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_plan: 05-01 — Phase 5 orchestration (pending planning)
status: ready
last_updated: "2026-05-25T20:55:00.000Z"
progress:
  total_phases: 7
  completed_phases: 4
  total_plans: 26
  completed_plans: 26
  percent: 57
---

# State — Wheel of Fish TV

**Updated:** 2026-05-25 (Phase 4 complete)

## Project reference

See: `.planning/PROJECT.md` (updated 2026-05-25)

**Core value:** Mixed random TV playlists across chosen shows honoring true resume semantics per series whenever `ordered`; allow pure chaos rows + global WheelOfFish.

## Current phase

Phase **4 — Playlist mathematics** — **complete** (6/6 plans).

**Next phase:** Phase **5 — Orchestration & scheduling**

## Immediate next actions

1. Plan Phase 5 via `/gsd-plan-phase 5` or `/gsd-execute-phase 5` when plans exist
2. Wire Phase 5 scheduler to call `PlaylistBuilder.build()` with live MediaProvider snapshots

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
- Episode.last_viewed_at defaults None; Plex lastViewedAt=0 maps to None (never-played sentinel)
- Malformed provider timestamps map to None via try/except — no ingestion exceptions
- Wave 3 builder must add every block member id to emitted_ids before next disordered pick (D-04, D-09)
- LAST_VIEWED_EXCLUSION_SIZE=15; tie-break equal last_viewed_at by id ascending
- SlotAllocation WILD/BALANCED/ROUND_ROBIN on Playlist; builder is stateless single entry point (D-23)
- PlaylistBuildResult.day_key stores opaque rebuild_seed; RNG from sha256(playlist.id:rebuild_seed) (D-24)
- episode_count defaults to 20; slot_allocation defaults to WILD (D-01, D-19)

## Decisions (Phase 3)

- WOF_PROVIDER drives single-provider installs; legacy WOF_ENABLED_PROVIDERS retained for multi-provider tests
- Session cookie https_only only when ENVIRONMENT=production
- ProtectedRoute requires has_media_link (not just session bootstrap)
- Storybook deferred to Phase 7 (D-20)

## Working notes

- Phase 4 plan 06: `.planning/phases/04-playlist-mathematics/04-06-SUMMARY.md`
- Phase 4 plan 05: `.planning/phases/04-playlist-mathematics/04-05-SUMMARY.md`
- Phase 4 plan 04: `.planning/phases/04-playlist-mathematics/04-04-SUMMARY.md`
- Phase 4 plan 03: `.planning/phases/04-playlist-mathematics/04-03-SUMMARY.md`
- Phase 4 plan 02: `.planning/phases/04-playlist-mathematics/04-02-SUMMARY.md`
- Phase 4 plan 01: `.planning/phases/04-playlist-mathematics/04-01-SUMMARY.md`
- Phase 3 UAT: `.planning/phases/03-minimal-operator-spa-shell/03-UAT-CHECKLIST.md`
- Phase 2 complete: 7/7 plans
- Phase 1 complete: 5/5 plans

---

*Auto-maintain during `/gsd-transition` / `/gsd-progress`.*
