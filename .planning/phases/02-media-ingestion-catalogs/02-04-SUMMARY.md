---
phase: 02-media-ingestion-catalogs
plan: 04
subsystem: api
tags: [jellyfin, httpx, respx, fastapi, media-provider, authenticate-by-name]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: domain DTOs, composite IDs, MediaProvider protocol, fixtures (02-01)
  - phase: 02-media-ingestion-catalogs
    provides: connections schema, vault, test-then-save service (02-02)
  - phase: 02-media-ingestion-catalogs
    provides: PlexProvider reference implementation (02-03)
provides:
  - Jellyfin AuthenticateByName auth module and POST /api/v1/connections/jellyfin/auth route
  - JellyfinProvider implementing MediaProvider with identical Library/Series/Episode DTOs
  - build_provider_for_connection Jellyfin branch with per-user provider_user_id
  - GET /api/v1/connections/{id}/libraries end-to-end for Jellyfin connections
affects: [02-05, catalog sync, resume service, dual-provider parity]

tech-stack:
  added: []
  patterns:
    - Jellyfin AuthenticateByName with MediaBrowser Authorization header
    - Per-user AccessToken in vault; provider_user_id on UserMediaLink
    - Admin API key username rejected for user linking (D-13)
    - Jellyfin mappers use same domain/dto.py classes as Plex with composite jellyfin IDs

key-files:
  created:
    - backend/src/wheeloffish/integrations/jellyfin/auth.py
    - backend/src/wheeloffish/integrations/jellyfin/client.py
    - backend/src/wheeloffish/integrations/jellyfin/mappers.py
    - backend/src/wheeloffish/integrations/jellyfin/__init__.py
    - backend/src/wheeloffish/api/routes/oauth_jellyfin.py
    - backend/tests/integrations/test_jellyfin_client.py
  modified:
    - backend/src/wheeloffish/api/schemas/oauth.py
    - backend/src/wheeloffish/core/connections.py
    - backend/src/wheeloffish/main.py
    - backend/tests/api/test_connections_routes.py

key-decisions:
  - "AuthenticateByName only for user linking; 32-char hex usernames rejected as API keys"
  - "JellyfinProvider ping uses GET /Users/Me to validate per-user token"
  - "build_provider_for_connection accepts provider_user_id for Jellyfin user-scoped API calls"

patterns-established:
  - "Pattern: Jellyfin auth route validates token via /Users/Me before create_connection ping"
  - "Pattern: Episode watch mapping — UserData.Played override; PlayedPercentage or ticks fallback"
  - "Pattern: Composite IDs use Jellyfin item UUID: {connection_id}:jellyfin:{uuid}"

requirements-completed: [INT-01, INT-02]

duration: 25min
completed: 2026-05-25
---

# Phase 2 Plan 04 Summary

**Jellyfin AuthenticateByName user linking and JellyfinProvider with identical Library/Series/Episode DTOs as Plex**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Implemented Jellyfin auth module (`AuthenticateByName`, `/Users/Me` validation) with API-key rejection for user linking
- Shipped JellyfinProvider with mappers for Library/Series/Episode; composite IDs use Jellyfin item UUIDs
- Wired `POST /api/v1/connections/jellyfin/auth` route and extended connection factory for Jellyfin
- Added 12 integration/API tests with respx mocks; all 61 backend tests pass

## Task Commits

Single commit for plan 02-04:

1. **Task 1–3: Jellyfin auth, provider, and route wiring** — `feat(02-04): Jellyfin auth and provider parity`

## Files Created/Modified

- `backend/src/wheeloffish/integrations/jellyfin/auth.py` — AuthenticateByName and token validation
- `backend/src/wheeloffish/integrations/jellyfin/client.py` — JellyfinProvider MediaProvider implementation
- `backend/src/wheeloffish/integrations/jellyfin/mappers.py` — DTO mappers matching Plex field names
- `backend/src/wheeloffish/api/routes/oauth_jellyfin.py` — POST /connections/jellyfin/auth route
- `backend/src/wheeloffish/core/connections.py` — JellyfinProvider factory branch; provider_user_id lookup
- `backend/tests/integrations/test_jellyfin_client.py` — respx tests for auth, libraries, series, episodes, DTO parity

## Decisions Made

- Reject 32-char hex usernames as admin API keys per D-13 threat model T-02-04-02
- Password accepted in POST body only; never logged, stored, or returned (T-02-04-01)
- Jellyfin ping uses `/Users/Me` rather than `/System/Info` to confirm per-user token validity

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Dual-provider foundation complete; ROADMAP criterion #3 (identical DTOs) met
- Ready for plan 02-05 catalog sync and library scoping

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*
