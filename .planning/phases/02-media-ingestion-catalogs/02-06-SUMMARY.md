---
phase: 02-media-ingestion-catalogs
plan: 06
subsystem: api
tags: [fastapi, resume-service, live-episodes, media-provider, int-03]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: MediaProvider protocol, connections service, catalog sync (02-01–02-05)
provides:
  - ResumeService domain class reusable by Phase 4 playlist builder
  - GET /connections/{id}/series/{series_id}/episodes (live provider fetch)
  - GET /connections/{id}/series/{series_id}/resume (ResumeCursor preview)
  - EpisodeResponse and ResumePreviewResponse API schemas
affects: [02-07, Phase 3 SPA, Phase 4 playlist builder]

tech-stack:
  added: []
  patterns:
    - ResumeService.compute(series_id, episodes, on_deck) hybrid rule (D-10)
    - Live episode fetch via build_provider_for_connection + per-user vault token
    - Composite series_id validation against connection_id prefix (T-02-06-03)

key-files:
  created:
    - backend/src/wheeloffish/api/schemas/resume.py
  modified:
    - backend/src/wheeloffish/core/resume.py
    - backend/src/wheeloffish/api/routes/catalog.py
    - backend/tests/unit/test_resume_service.py
    - backend/tests/api/test_catalog_routes.py

key-decisions:
  - "ResumeService class wraps existing compute logic; compute_resume kept as convenience wrapper"
  - "Resume preview API omits nested episode field from ResumeCursor DTO"
  - "Per-user provider isolation uses vault token lookup in _build_provider_for_user"

patterns-established:
  - "Pattern: validate series composite id prefix matches route connection_id before live fetch"
  - "Pattern: episodes/resume routes use live MediaProvider only — no episode SQLite table"

requirements-completed: [INT-03]

duration: 20min
completed: 2026-05-25
---

# Phase 2 Plan 06 Summary

**Live episode fetch and resume preview API with reusable ResumeService for Phase 4**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Finalized `ResumeService` with `compute`, module-level helpers, and Phase 4 reuse docstring
- Shipped `GET …/series/{series_id}/episodes` and `GET …/series/{series_id}/resume` with live provider fetch (no episode DB persistence)
- Added `EpisodeResponse`, `EpisodesListResponse`, and `ResumePreviewResponse` schemas
- Added 4 integration tests: live fetch, resume/service parity, on-deck-ahead, per-user isolation

## Task Commits

Single commit for plan 02-06:

1. **Tasks 1–3: ResumeService, live endpoints, and tests** — `feat(02-06): live episodes and resume preview API`

## Files Created/Modified

- `backend/src/wheeloffish/core/resume.py` — ResumeService class + module docstring
- `backend/src/wheeloffish/api/schemas/resume.py` — Episode and resume preview response schemas
- `backend/src/wheeloffish/api/routes/catalog.py` — live episodes and resume preview routes
- `backend/tests/api/test_catalog_routes.py` — INT-03 episodes/resume integration tests

## Decisions Made

- Kept `compute_resume()` as a thin wrapper around `ResumeService().compute()` for existing unit tests
- Resume preview response excludes nested `episode` field from domain ResumeCursor
- Series ID validation uses `parse_composite_id` and rejects mismatched connection prefix

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `EpisodeResponse.from_dto` return annotation required `from __future__ import annotations` to avoid NameError at class body evaluation time
- Per-user isolation test initially used same resume episode for both users; adjusted fixtures so users resume at different episodes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- INT-03 complete: watch metadata sufficient for resume pointers via REST preview
- Phase 3 SPA can consume live episodes and resume endpoints for series detail UX
- Phase 4 playlist builder can import `ResumeService` directly

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*
