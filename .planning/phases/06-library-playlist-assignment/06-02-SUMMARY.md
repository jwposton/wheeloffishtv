---
phase: 06-library-playlist-assignment
plan: 02
subsystem: api
tags: [fastapi, playlists, row-ops, owner-scoped, tdd]

# Dependency graph
requires:
  - phase: 05-orchestration-scheduling
    provides: Playlist CRUD routes, _get_owned_playlist ownership gate (D-18)
provides:
  - POST /api/v1/playlists/{id}/rows append one series row
  - DELETE /api/v1/playlists/{id}/rows/{series_id} remove one row
  - PATCH /api/v1/playlists/{id}/rows/{series_id} update row mode/policy/event
  - AppendRowRequest and PatchRowRequest Pydantic schemas
  - Integration tests for happy path, 409 duplicate, cross-user 404
affects:
  - 06-03 Library context-menu quick-add
  - 06-04 Two-pane playlist editor incremental mutations

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Incremental row mutations return full PlaylistDetailResponse via _playlist_to_detail"
    - "Duplicate (playlist_id, series_id) checked before insert; DB UniqueConstraint as backstop"
    - "sort_order assigned max(existing)+1 on append"

key-files:
  created: []
  modified:
    - backend/src/wheeloffish/api/schemas/playlists.py
    - backend/src/wheeloffish/api/routes/playlists.py
    - backend/tests/integration/test_playlists_api.py

key-decisions:
  - "Append defaults mode=ordered, completion_policy=remove, completion_event=series_complete (match create)"
  - "Cross-user row ops return 404 via existing _get_owned_playlist (D-18)"
  - "Duplicate append returns 409 Conflict before insert"
  - "PatchRowRequest validator requires at least one mutable field"

patterns-established:
  - "Row op routes co-located in playlists.py with CRUD; shared _get_playlist_row helper for 404 on missing row"

requirements-completed: [PLT-03]

# Metrics
duration: 1min
completed: 2026-05-25
---

# Phase 6 Plan 02: Row Append/Remove/Patch API Summary

**Owner-scoped POST/DELETE/PATCH row endpoints let Library quick-add and the two-pane editor mutate playlist rows without full PUT replacement.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-25T23:32:39Z
- **Completed:** 2026-05-25T23:33:17Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added five integration tests (append, duplicate 409, remove, patch mode, cross-user 404) in TDD RED then GREEN
- Implemented `AppendRowRequest` / `PatchRowRequest` schemas with create defaults and patch validator
- Live routes: append with sort_order=max+1, remove 204, patch returns updated detail; all update `playlist.updated_at`

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 — failing integration tests for row ops (D-20)** - `05bb1bd` (test)
2. **Task 2: Implement append, remove, patch row endpoints (D-20)** - `781c3b2` (feat)

## Files Created/Modified

- `backend/src/wheeloffish/api/schemas/playlists.py` - AppendRowRequest, PatchRowRequest with validators
- `backend/src/wheeloffish/api/routes/playlists.py` - append_playlist_row, remove_playlist_row, patch_playlist_row
- `backend/tests/integration/test_playlists_api.py` - Five row-op integration tests

## Decisions Made

- Append row defaults match playlist create row defaults (ordered/remove/series_complete)
- Duplicate detection via pre-insert query; 409 before hitting DB UniqueConstraint
- PATCH requires at least one of mode, completion_policy, or completion_event

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Full `ruff check src/wheeloffish/api/` reports pre-existing issues in auth.py, catalog.py, oauth_plex.py (out of scope); modified files pass ruff cleanly

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 06-03 (Library context-menu quick-add) can call POST `/playlists/{id}/rows`
- Plan 06-04 (two-pane editor) can use append/remove/patch for incremental mutations without PUT row replacement

---
*Phase: 06-library-playlist-assignment*
*Completed: 2026-05-25*

## Self-Check: PASSED

- Modified files exist: schemas/playlists.py, routes/playlists.py, test_playlists_api.py
- Task commits verified: 05bb1bd, 781c3b2
- All 18 playlist integration tests pass
