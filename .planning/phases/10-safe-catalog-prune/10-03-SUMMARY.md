---
phase: 10-safe-catalog-prune
plan: 03
subsystem: api
tags: [prune, rebuild, orchestrator, FetchResult, ProviderNotFound]

# Dependency graph
requires:
  - phase: 10-02
    provides: catalog_prune service (record_rebuild_row_absence, execute_auto_prune)
provides:
  - FetchResult typed rebuild fetch with not_found vs fetch_failure taxonomy
  - Reachability-gated rebuild evidence and per-row recovery on ok fetch
  - Playlist-scoped auto-prune after succeeded/partial rebuild
affects: [10-04, 10-05, 10-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fetch_rebuild_inputs_for_row returns FetchResult; orchestrator branches on reason"
    - "Evidence only when check_provider_reachable; fetch_failure never increments"
    - "auto_prune after rebuild success with try/except so prune errors do not fail rebuild"

key-files:
  created: []
  modified:
    - backend/src/wheeloffish/core/playlist/rebuild_inputs.py
    - backend/src/wheeloffish/core/orchestrator.py
    - backend/tests/unit/test_orchestrator.py
    - backend/tests/unit/test_orchestrator_writeback.py
    - backend/tests/integration/test_rebuild_e2e.py

key-decisions:
  - "ProviderNotFound checked before ProviderError for not_found reason (D-02)"
  - "Recovery clears absence inline on ok fetch; auto-prune runs after writeback commits (D-11, D-06)"
  - "Auto-prune threshold test uses fetch_failure for at-threshold row so D-11 recovery does not clear counter before prune"

patterns-established:
  - "Rebuild warnings in row_outcomes_json unchanged for empty_snapshot/fetch_failure/not_found (PRUNE-04)"

requirements-completed: [PRUNE-02, PRUNE-04]

# Metrics
duration: 18min
completed: 2026-06-02
---

# Phase 10 Plan 03: Rebuild Evidence Channel Summary

**FetchResult classifies provider misses; rebuild accumulates evidence only when reachable, recovers on ok fetch, and auto-prunes at threshold per playlist after success/partial runs**

## Performance

- **Duration:** 18 min
- **Completed:** 2026-06-02
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- `FetchResult` dataclass with `ok` / `empty_snapshot` / `not_found` / `fetch_failure` reasons; `ProviderNotFound` maps to `not_found`
- `rebuild_playlist` gates `record_rebuild_row_absence` on reachability; clears prune state on successful row fetch
- `execute_auto_prune` after succeeded/partial rebuild, scoped to playlist, errors logged not propagated
- 13 orchestrator unit tests + 232 backend unit/integration tests green

## Task Commits

1. **Task 1 RED: FetchResult classification tests** - `16ad6bd` (test)
2. **Task 1 GREEN: FetchResult in rebuild_inputs** - `ec4a636` (feat)
3. **Tasks 2–3: Evidence, recovery, auto-prune** - `e11b307` (feat)

## Files Created/Modified

- `backend/src/wheeloffish/core/playlist/rebuild_inputs.py` - FetchResult + ProviderNotFound branch
- `backend/src/wheeloffish/core/orchestrator.py` - Reachable-gated evidence, recovery, auto-prune hook
- `backend/tests/unit/test_orchestrator.py` - Classification, evidence, recovery, auto-prune tests
- `backend/tests/unit/test_orchestrator_writeback.py` - FetchResult mock
- `backend/tests/integration/test_rebuild_e2e.py` - FetchResult mock

## Decisions Made

- Tasks 2 and 3 committed together (single orchestrator change set)
- Auto-prune test uses `fetch_failure` for threshold row because ok fetch triggers D-11 recovery before prune

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated writeback and e2e mocks for FetchResult**
- **Found during:** Full suite verification
- **Fix:** `test_orchestrator_writeback.py` and `test_rebuild_e2e.py` mocks return `FetchResult(..., "ok")`
- **Commit:** `e11b307`

### Test adjustment (not a code deviation)

- `test_rebuild_auto_prune_at_threshold` uses `fetch_failure` for the at-threshold row instead of `ok`, because successful fetch clears `absence_count` per D-11 before auto-prune runs

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Rebuild channel ready for catalog_sync integration (10-04) and API/UI surfaces (10-05/06)
- `not_found` warnings now appear in `fetch_warnings` alongside existing reasons

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/rebuild_inputs.py
- FOUND: backend/src/wheeloffish/core/orchestrator.py
- FOUND: backend/tests/unit/test_orchestrator.py
- FOUND: 16ad6bd, ec4a636, e11b307

---
*Phase: 10-safe-catalog-prune*
*Completed: 2026-06-02*
