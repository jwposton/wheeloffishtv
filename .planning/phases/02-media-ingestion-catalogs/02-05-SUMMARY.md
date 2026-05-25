---
phase: 02-media-ingestion-catalogs
plan: 05
subsystem: api
tags: [fastapi, sqlalchemy, asyncio, catalog-sync, cached-series, background-tasks]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: DB models, MediaProvider protocol, connections service (02-01–02-04)
provides:
  - Chunked background catalog sync service (catalog_sync.py)
  - GET /connections/{id}/series with paging, search, embedded sync status
  - POST /connections/{id}/sync and GET /sync/status (non-blocking 202)
  - POST /session/catalog-refresh for login-time sync (D-16, D-18)
  - PUT /admin/connections/{id}/library-scope for in_scope filtering (D-09)
  - OAuth connect triggers initial sync on Plex and Jellyfin
affects: [02-06, 02-07, resume service, Phase 3 SPA]

tech-stack:
  added: []
  patterns:
    - asyncio.create_task for non-blocking chunked sync from async routes
    - cached_libraries in_scope gate before series browse and sync
    - WOF_SCOPED_LIBRARY_IDS env for install-level library scope defaults
    - Sync status idle→running→complete/failed in catalog_sync_state

key-files:
  created:
    - backend/src/wheeloffish/core/catalog_sync.py
    - backend/src/wheeloffish/api/schemas/catalog.py
    - backend/src/wheeloffish/api/routes/catalog.py
    - backend/tests/api/test_catalog_routes.py
  modified:
    - backend/src/wheeloffish/core/config.py
    - backend/src/wheeloffish/main.py
    - backend/src/wheeloffish/api/deps.py
    - backend/src/wheeloffish/api/routes/connections.py
    - backend/src/wheeloffish/api/routes/oauth_plex.py
    - backend/src/wheeloffish/api/routes/oauth_jellyfin.py
    - backend/tests/conftest.py

key-decisions:
  - "Libraries route moved to catalog router; returns cached in-scope libraries with live fetch on first access"
  - "Sync trigger routes are async so asyncio.create_task runs inside the ASGI event loop"
  - "When WOF_SCOPED_LIBRARY_IDS unset, all libraries default in_scope=true for dev usability"

patterns-established:
  - "Pattern: trigger_sync sets catalog_sync_state=running then spawns run_chunked_sync task"
  - "Pattern: Series browse embeds sync status for Updating library banner UX (D-18)"
  - "Pattern: Admin library-scope PUT toggles cached_libraries.in_scope flags"

requirements-completed: [INT-02]

duration: 30min
completed: 2026-05-25
---

# Phase 2 Plan 05 Summary

**Chunked background catalog sync with cached series browse API, library scoping, and non-blocking sync triggers**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Implemented `catalog_sync.py` with `trigger_sync`, `run_chunked_sync`, and `get_sync_status`; upserts `CachedSeries` only (no episode cache per D-14)
- Shipped catalog REST routes: series browse with `?page=&limit=&q=`, sync trigger/status, session catalog-refresh, admin library-scope
- Wired OAuth Plex/Jellyfin callbacks to trigger initial sync on connect
- Added 6 integration tests covering paging, search, sync lifecycle, non-blocking response, session refresh, and library scope filter

## Task Commits

Single commit for plan 02-05:

1. **Tasks 1–3: Catalog sync service, browse API, and tests** — `feat(02-05): catalog sync and browse API`

## Files Created/Modified

- `backend/src/wheeloffish/core/catalog_sync.py` — chunked background sync engine
- `backend/src/wheeloffish/api/routes/catalog.py` — browse, sync, session refresh, admin scope routes
- `backend/src/wheeloffish/api/schemas/catalog.py` — SeriesBrowseResponse, SyncStatusResponse, LibraryScopeUpdate
- `backend/tests/api/test_catalog_routes.py` — INT-02 catalog browse and sync tests
- `backend/src/wheeloffish/core/config.py` — WOF_SCOPED_LIBRARY_IDS setting

## Decisions Made

- Moved GET `/connections/{id}/libraries` from connections router to catalog router (cached + in_scope filter)
- Made POST sync and session catalog-refresh async endpoints so background tasks spawn correctly under ASGI
- Default all libraries in_scope when env scope list is empty (admin can narrow via PUT library-scope)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Sync routes initially used sync def handlers; `asyncio.create_task` failed without a running loop. Fixed by making sync-trigger routes async.

## User Setup Required

None - no external service configuration required.

Optional env:
- `WOF_SCOPED_LIBRARY_IDS` — comma-separated native library IDs to mark in_scope on first fetch
- `WOF_CATALOG_SYNC_CHUNK_SIZE` — default 100
- `WOF_CATALOG_PAGE_DEFAULT` — default 50

## Next Phase Readiness

- INT-02 catalog browse and sync complete; ready for live episode fetch and resume endpoints (02-06+)
- Phase 3 SPA can consume series browse with embedded sync status for "Updating library…" banner

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*
