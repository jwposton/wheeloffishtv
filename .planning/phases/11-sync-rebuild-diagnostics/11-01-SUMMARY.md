---
phase: 11-sync-rebuild-diagnostics
plan: 01
subsystem: api
tags: [pydantic, fastapi, typescript, diagnostics, rebuild]

requires: []
provides:
  - Backend Pydantic diagnostics models on RebuildRunSummary
  - Frontend TS types mirroring diagnostics + PruneEvent/recent_prune_events
  - RED unit-test scaffold for build_rebuild_diagnostics (Plan 02)
affects: [11-02, 11-03, 11-04, 11-05]

tech-stack:
  added: []
  patterns:
    - "Interface-first: diagnostics contract on RebuildRunSummary before resolver implementation"
    - "Optional diagnostics defaults None on recent_runs (D-24)"

key-files:
  created:
    - backend/tests/unit/test_rebuild_diagnostics.py
  modified:
    - backend/src/wheeloffish/api/schemas/playlists.py
    - frontend/src/api/playlists.ts

key-decisions:
  - "Diagnostics models defined before RebuildRunSummary so forward refs are unnecessary"
  - "Frontend PruneEvent mirrors PruneEventResponse for recent_prune_events typing (Pitfall 3)"

patterns-established:
  - "DiagnosticIssueRow carries reason_code, reason_text, remediation_hint, and actions[] per D-19/D-22"
  - "RED resolver tests import from wheeloffish.core.rebuild_diagnostics for Plan 02 GREEN gate"

requirements-completed: [DIAG-02, DIAG-05]

duration: 15min
completed: 2026-06-03
---

# Phase 11 Plan 01: Diagnostics contracts Summary

**Cross-cutting rebuild diagnostics types on backend and frontend, plus RED resolver tests for Plan 02**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-03T01:37:00Z
- **Completed:** 2026-06-03T01:52:17Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `DiagnosticAction`, `DiagnosticIssueRow`, and `RebuildDiagnostics` Pydantic models with optional `diagnostics` on `RebuildRunSummary` (D-21, D-22, D-23).
- Mirrored TypeScript interfaces and typed `recent_prune_events` on `PlaylistDetailResponse` (DIAG-05 / Pitfall 3).
- Created five named RED unit tests importing `build_rebuild_diagnostics` from the not-yet-built `rebuild_diagnostics` module.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add backend diagnostics Pydantic models** - `8a858cc` (feat)
2. **Task 2: Mirror diagnostics types in the frontend API layer** - `8843296` (feat)
3. **Task 3: Create RED resolver unit-test scaffold** - `12d31af` (test)

**Plan metadata:** `52ca0be` (docs: complete plan)

## Files Created/Modified

- `backend/src/wheeloffish/api/schemas/playlists.py` - Diagnostics models + `RebuildRunSummary.diagnostics`
- `frontend/src/api/playlists.ts` - TS diagnostics types, `PruneEvent`, `recent_prune_events`
- `backend/tests/unit/test_rebuild_diagnostics.py` - RED resolver contract tests for Plan 02

## Decisions Made

None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 can implement `wheeloffish.core.rebuild_diagnostics` and turn RED tests GREEN.
- Plan 03 can wire `build_rebuild_diagnostics` into `_playlist_to_detail` for `last_rebuild` only.
- Frontend modal/UI plans (04–05) can consume typed `diagnostics` and `recent_prune_events`.

---
*Phase: 11-sync-rebuild-diagnostics*
*Completed: 2026-06-03*

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/api/schemas/playlists.py
- FOUND: frontend/src/api/playlists.ts
- FOUND: backend/tests/unit/test_rebuild_diagnostics.py
- FOUND: 8a858cc
- FOUND: 8843296
- FOUND: 12d31af
