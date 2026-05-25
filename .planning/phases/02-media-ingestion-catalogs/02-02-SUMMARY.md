---
phase: 02-media-ingestion-catalogs
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, alembic, connections, vault, pytest]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: domain DTOs, MediaProvider protocol, ProviderError taxonomy, respx fixtures (02-01)
provides:
  - Alembic migration 002_connections_catalog (five catalog/connection tables)
  - Per-user vault token helpers (D-13 key scheme)
  - Connection service with test-then-save and ephemeral provider stub
  - POST/GET/DELETE /api/v1/connections and POST /api/v1/connections/{id}/test
affects: [02-03, 02-04, 02-05, oauth routes, catalog sync, provider clients]

tech-stack:
  added: []
  patterns:
    - Test-then-save: provider ping before DB commit; rollback on failure
    - Per-user vault keys media_server/{connection_id}/users/{app_user_id}/token
    - Single transaction for connection row + UserMediaLink + vault write
    - Structured 422 errors with detail.code for provider failures

key-files:
  created:
    - backend/alembic/versions/002_connections_catalog.py
    - backend/src/wheeloffish/db/models/connection.py
    - backend/src/wheeloffish/db/models/user_media_link.py
    - backend/src/wheeloffish/db/models/cached_library.py
    - backend/src/wheeloffish/db/models/cached_series.py
    - backend/src/wheeloffish/db/models/catalog_sync_state.py
    - backend/src/wheeloffish/core/connections.py
    - backend/src/wheeloffish/api/deps.py
    - backend/src/wheeloffish/api/schemas/connections.py
    - backend/src/wheeloffish/api/routes/connections.py
    - backend/tests/api/test_connections_routes.py
  modified:
    - backend/src/wheeloffish/core/namespaces.py
    - backend/src/wheeloffish/core/secrets.py
    - backend/src/wheeloffish/db/models/__init__.py
    - backend/alembic/env.py
    - backend/src/wheeloffish/main.py
    - backend/tests/conftest.py

key-decisions:
  - "Vault set_secret accepts commit=False for transactional create_connection flow"
  - "EphemeralMediaProvider stub used until Plex/Jellyfin clients ship in plans 03-04"
  - "Unique constraint on connections.provider_type enforces one Plex + one Jellyfin (D-05)"

patterns-established:
  - "Pattern: create_connection pings provider before any DB/vault writes"
  - "Pattern: connection_factory conftest helper with mocked build_ephemeral_provider"
  - "Pattern: FastAPI dependency override get_db for route integration tests"

requirements-completed: [INT-01]

duration: 25min
completed: 2026-05-25
---

# Phase 2 Plan 02 Summary

**Connections schema migration, per-user vault tokens, and REST CRUD with test-then-save validation**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 4
- **Files modified:** 17

## Accomplishments

- Created migration `002_connections_catalog` with connections, user_media_links, cached_libraries, cached_series, and catalog_sync_state tables
- Extended SecretsVault with per-user token storage and bulk connection secret deletion
- Implemented connection service with test-then-save, provider_disabled gating, and duplicate provider_type conflict (409)
- Shipped REST routes with nine integration tests covering success, all 422 error codes, and token exclusion from responses

## Task Commits

Single plan commit:

1. **All tasks (1–4)** - pending (feat)

**Plan metadata:** pending (this summary)

## Files Created/Modified

- `backend/alembic/versions/002_connections_catalog.py` — Phase 2 catalog schema migration
- `backend/src/wheeloffish/db/models/*.py` — five ORM models with cascade FK relationships
- `backend/src/wheeloffish/core/connections.py` — EphemeralMediaProvider stub + create/test/delete service
- `backend/src/wheeloffish/core/secrets.py` — per-user token vault methods with optional commit=False
- `backend/src/wheeloffish/api/routes/connections.py` — GET/POST/DELETE connections + POST test
- `backend/tests/api/test_connections_routes.py` — nine route tests with mocked provider ping

## Decisions Made

- Added `commit=False` parameter to vault write methods so connection create uses a single DB transaction
- Used stub `EphemeralMediaProvider` for ping until real httpx clients land in plans 03-04
- Alembic env imports connection model module as `connection_model` to avoid variable name clash

## Deviations from Plan

None - plan executed as specified.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Verification

- `cd backend && uv run ruff check .` — pass
- `cd backend && uv run pytest -q` — 38 passed
- `cd backend && uv run alembic upgrade head` (temp sqlite) — pass
- `pytest tests/api/test_connections_routes.py -k unauthorized` — pass
- `pytest tests/api/test_connections_routes.py -k provider_disabled` — pass

## Next Phase Readiness

- Schema and connection CRUD foundation ready for Plex/Jellyfin OAuth and real provider clients (02-03+)
- Cached library/series tables ready for catalog sync service
- `connection_factory` conftest helper available for downstream route tests

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*

## Self-Check

PASSED
