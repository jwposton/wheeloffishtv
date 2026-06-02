---
phase: 10-safe-catalog-prune
plan: 05
subsystem: api
tags: [prune, orchestrator, nightly, catalog_sync, D-05, D-04]

# Dependency graph
requires:
  - phase: 10-02
    provides: reset_absence_counters_for_connection in catalog_prune
  - phase: 10-03
    provides: rebuild evidence channel and reachable-gated absence
  - phase: 10-04
    provides: run_chunked_sync sync-driven evidence and prune
provides:
  - Connection-grouped nightly batch with sync-before-rebuild ordering (D-05)
  - Unreachable connection counter reset and failed RebuildRuns (D-04)
affects: [10-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Nightly batch groups due playlists by connection_id from first row series_id"
    - "await run_chunked_sync directly per connection (no create_task in batch path)"
    - "Per-connection loop continues on failure without aborting other connections"

key-files:
  created: []
  modified:
    - backend/src/wheeloffish/core/orchestrator.py
    - backend/tests/unit/test_orchestrator.py

key-decisions:
  - "run_chunked_sync uses its own DB session; nightly batch session reads fresh state after await returns"
  - "Playlists with no rows or unparseable series_id are skipped during grouping"

patterns-established:
  - "Nightly cadence: probe reachability → sync OR reset+fail → rebuild per connection"

requirements-completed: [PRUNE-02]

# Metrics
duration: 12min
completed: 2026-06-02
---

# Phase 10 Plan 05: Nightly Sync-Before-Rebuild Summary

**Connection-grouped nightly batch awaits full catalog sync per connection before rebuilding due playlists; unreachable providers reset absence counters and fail only that connection's playlists**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-06-02
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Refactored `run_nightly_batch` from first-connection global reachability gate to per-connection sync-then-rebuild loop
- `await run_chunked_sync(connection_id, app_user_id)` runs before rebuild loop for reachable connections (D-05)
- Unreachable connections create failed `RebuildRun` rows, call `reset_absence_counters_for_connection`, and skip sync (D-04)
- Two new unit tests prove sync-before-rebuild ordering and unreachable reset behavior
- 15 orchestrator tests + 239 unit/integration tests green

## Task Commits

1. **Task 1: Refactor run_nightly_batch** - `d4b791b` (feat)
2. **Task 2: Nightly ordering and reset tests** - `4bc450e` (test)

## Files Created/Modified

- `backend/src/wheeloffish/core/orchestrator.py` - Connection-grouped sync-before-rebuild nightly batch
- `backend/tests/unit/test_orchestrator.py` - Ordering, unreachable reset, updated weekly skip mocks

## Decisions Made

- Skipped playlists when connection has no `UserMediaLink` (per plan action)
- Missing connection creates per-playlist failed runs with connection-not-found message

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Nightly batch now accumulates sync + rebuild evidence together each night (D-05)
- Ready for 10-06 UI/API surfaces that surface prune state to operators

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/orchestrator.py
- FOUND: backend/tests/unit/test_orchestrator.py
- FOUND: d4b791b, 4bc450e

---
*Phase: 10-safe-catalog-prune*
*Completed: 2026-06-02*
