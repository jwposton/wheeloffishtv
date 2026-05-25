---
phase: 04-playlist-mathematics
plan: 06
subsystem: core
tags: [playlist, builder, slot-allocation, ordered, disordered, pytest, golden-vectors]

requires:
  - phase: 04-playlist-mathematics
    provides: completion policies (04-03), ordered picker (04-04), disordered picker (04-05), domain models (04-01)
provides:
  - PlaylistBuilder.build() single entry point for Phase 5 rebuild orchestration (D-23)
  - SlotAllocation WILD/BALANCED/ROUND_ROBIN with allocate_slots helper (D-01, D-02)
  - Deterministic rebuild_seed → RNG via make_build_rng (D-24)
  - 10 end-to-end golden-vector tests proving PLT-01–06 and SCH-02 together
affects:
  - Phase 5 scheduler and manual rebuild routes (call PlaylistBuilder.build with live snapshots)

tech-stack:
  added: []
  patterns:
    - "Stateless builder — each build returns fresh episode list, never appends prior output (D-16)"
    - "PlaylistBuildResult.day_key stores opaque rebuild_seed string, not calendar date (D-24)"
    - "slots_filled counts successful slot iterations; len(episodes) may exceed due to multipart (D-20)"

key-files:
  created:
    - backend/src/wheeloffish/core/playlist/builder.py
    - backend/tests/unit/test_playlist_builder.py
  modified:
    - backend/src/wheeloffish/domain/playlist.py
    - backend/src/wheeloffish/core/playlist/__init__.py
    - backend/tests/unit/test_playlist_models.py

key-decisions:
  - "SlotAllocation enum on Playlist with WILD default; episode_count explicit default 20 (D-01, D-19)"
  - "RNG seed = sha256(f'{playlist.id}:{rebuild_seed}')[:8] as int — same seed + inputs yields identical output"
  - "Zero active rows after completion returns empty episodes without raising (T-04-06-01)"
  - "Mixed-row golden test uses ROUND_ROBIN to guarantee both ordered and disordered rows contribute"

patterns-established:
  - "Pattern: Phase 5 passes list[SeriesRebuildInput] snapshots; builder has no MediaProvider/DB imports"
  - "Pattern: Per-row OrderedCursor and emitted_ids initialized once before slot loop"

requirements-completed: [PLT-01, PLT-02, PLT-03, PLT-04, PLT-05, PLT-06, SCH-02]

duration: 12min
completed: 2026-05-25
---

# Phase 4 Plan 06: PlaylistBuilder Integration Summary

**Stateless PlaylistBuilder.build() orchestrates completion → slot allocation → ordered/disordered materialization with WILD/BALANCED/ROUND_ROBIN modes and 10 golden-vector proofs**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-25T20:42:56Z
- **Completed:** 2026-05-25T20:55:00Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Added `SlotAllocation` enum and `Playlist.slot_allocation` / `episode_count=20` defaults (D-01, D-02, D-19)
- Implemented `make_build_rng`, `allocate_slots`, and `PlaylistBuilder.build()` in `core/playlist/builder.py`
- Wired completion evaluation, ordered cursors, disordered emitted_ids tracking, and multipart block expansion
- 10 end-to-end golden vectors; full unit suite 108 passed

## Build API Contract

```python
from wheeloffish.core.playlist import PlaylistBuilder

result = PlaylistBuilder.build(
    playlist: Playlist,
    inputs: list[SeriesRebuildInput],
    rebuild_seed: str,  # opaque per-run string from Phase 5
) -> PlaylistBuildResult
```

- `result.day_key` stores the `rebuild_seed` verbatim (field name from 04-01; not a calendar date)
- `result.slots_requested` = `playlist.episode_count`
- `result.slots_filled` = slot iterations that produced ≥1 episode (may be < requested when rows exhaust, D-21)

## Slot Allocation Behavior

| Mode | Behavior |
|------|----------|
| WILD (default) | `rng.choice(active_series_ids)` per slot |
| BALANCED | Pick among rows with minimum pick count; ties broken by sorted series_id then rng |
| ROUND_ROBIN | Cycle `sorted(active_series_ids)` repeating |

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SlotAllocation enum + Playlist fields** - `66edc81` (feat)
2. **Task 2: Implement slot allocation helpers** - `f178847` (feat)
3. **Task 3: Implement PlaylistBuilder.build()** - `ee81a47` (feat)
4. **Task 4: End-to-end golden-vector tests** - `430ec30` (test)

## Files Created/Modified

- `backend/src/wheeloffish/domain/playlist.py` - SlotAllocation enum, slot_allocation field, episode_count default 20
- `backend/src/wheeloffish/core/playlist/builder.py` - make_build_rng, allocate_slots, PlaylistBuilder.build()
- `backend/src/wheeloffish/core/playlist/__init__.py` - exports PlaylistBuilder
- `backend/tests/unit/test_playlist_models.py` - default field tests
- `backend/tests/unit/test_playlist_builder.py` - 10 golden-vector end-to-end tests

## Decisions Made

- Mixed-row test uses ROUND_ROBIN allocation to deterministically ensure both ordered and disordered rows appear in output (WILD could starve one row with unlucky RNG)
- Multipart contiguous test resumes past s1e1 (marked complete) so first slot lands on multipart anchor

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 generator complete — Phase 5 can call `PlaylistBuilder.build()` with live episode snapshots from MediaProvider
- Optional plan 04-07 (Hypothesis property tests) remains out of scope per plan

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/builder.py
- FOUND: backend/tests/unit/test_playlist_builder.py
- FOUND: 66edc81
- FOUND: f178847
- FOUND: ee81a47
- FOUND: 430ec30

---
*Phase: 04-playlist-mathematics*
*Completed: 2026-05-25*
