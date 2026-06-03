---
phase: 11-sync-rebuild-diagnostics
plan: 03
subsystem: api
tags: [diagnostics, playlists, integration-tests, owner-gated]

requires:
  - phase: 11-sync-rebuild-diagnostics
    plan: 02
    provides: build_rebuild_diagnostics resolver and DiagnosticsContext
provides:
  - last_rebuild.diagnostics on GET /playlists/{id} detail
  - D-24 scoping (recent_runs diagnostics remain None)
  - Integration coverage for partial/failed runs and prune regression
affects: [11-04, 11-05]

tech-stack:
  added: []
  patterns:
    - "DiagnosticsContext built in _playlist_to_detail from DB + run snapshot (Pitfall 2)"
    - "provider_open_url computed once and reused for response + resolver (T-11-02)"

key-files:
  created: []
  modified:
    - backend/src/wheeloffish/api/routes/playlists.py
    - backend/tests/integration/test_playlists_api.py

key-decisions:
  - "Diagnostics attach only to last_rebuild after _rebuild_run_to_summary; recent_runs unchanged"
  - "Episode title fallback merges latest_good snapshot_out when run snapshot is empty"

patterns-established:
  - "Detail GET remains sole diagnostics surface via _get_owned_playlist (D-21, T-11-01)"

requirements-completed: [DIAG-02]

duration: 8min
completed: 2026-06-02
---

# Phase 11 Plan 03: Playlist detail diagnostics embed Summary

**Owner-gated playlist detail GET now resolves rebuild diagnostics on `last_rebuild` only while `recent_runs` stay summary-only**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-02T14:00:00Z
- **Completed:** 2026-06-02T14:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Wired `build_rebuild_diagnostics` into `_playlist_to_detail` with owner-scoped series titles, run snapshot episode titles, and server-built provider URL.
- Preserved D-24: `recent_runs[*].diagnostics` is `None`; `_rebuild_run_to_summary` unchanged for history rows.
- Added `test_playlist_detail_diagnostics` and `test_failed_run_diagnostics_has_rebuild_error`; Phase 10 `test_prune_events_in_detail` still passes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Embed diagnostics on last_rebuild in _playlist_to_detail** - `abe74d1` (feat)
2. **Task 2: Integration test for diagnostics embed + D-24 scoping** - `6363093` (test)

**Plan metadata:** `f604316` (docs: complete plan)

## Files Created/Modified

- `backend/src/wheeloffish/api/routes/playlists.py` - DiagnosticsContext assembly and `last_rebuild.diagnostics` assignment
- `backend/tests/integration/test_playlists_api.py` - Partial/failed-run diagnostics integration tests

## Decisions Made

- Reuse single `_playlist_open_url` result for both response field and `DiagnosticsContext.provider_open_url`.
- Series title map includes playlist row ids plus fetch_warning series ids from the latest run only.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Plan 04–05 can consume `last_rebuild.diagnostics` in the SPA (modals, action handlers).
- Resolver unit tests remain green without changes.

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/api/routes/playlists.py
- FOUND: backend/tests/integration/test_playlists_api.py
- FOUND: abe74d1
- FOUND: 6363093

---
*Phase: 11-sync-rebuild-diagnostics*
*Completed: 2026-06-02*
