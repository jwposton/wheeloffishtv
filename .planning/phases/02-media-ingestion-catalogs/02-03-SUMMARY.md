---
phase: 02-media-ingestion-catalogs
plan: 03
subsystem: api
tags: [plex, oauth, httpx, respx, fastapi, media-provider]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: domain DTOs, composite IDs, MediaProvider protocol, fixtures (02-01)
  - phase: 02-media-ingestion-catalogs
    provides: connections schema, vault, test-then-save service (02-02)
provides:
  - Plex PIN OAuth flow (start, callback, status routes)
  - PlexProvider implementing MediaProvider with guid-based composite IDs
  - GET /api/v1/connections/{id}/libraries live fetch for Plex
  - build_provider_for_connection factory replacing ephemeral stub for Plex
affects: [02-04, 02-05, catalog sync, Jellyfin parity]

tech-stack:
  added: []
  patterns:
    - Plex OAuth against plex.tv/api/v2 with in-memory PIN state (15 min TTL)
    - Test-then-save OAuth callback validates token + discovers server before vault write
    - PlexProvider resolves guid→ratingKey internally; composite IDs use guid
    - respx fixture tests for OAuth, libraries, series paging, episode watch fields

key-files:
  created:
    - backend/src/wheeloffish/integrations/plex/auth.py
    - backend/src/wheeloffish/integrations/plex/client.py
    - backend/src/wheeloffish/integrations/plex/mappers.py
    - backend/src/wheeloffish/integrations/plex/__init__.py
    - backend/src/wheeloffish/api/routes/oauth_plex.py
    - backend/src/wheeloffish/api/schemas/oauth.py
    - backend/tests/integrations/test_plex_client.py
    - backend/tests/fixtures/plex/show_series.json
    - backend/tests/fixtures/plex/guid_lookup.json
  modified:
    - backend/src/wheeloffish/core/connections.py
    - backend/src/wheeloffish/api/routes/connections.py
    - backend/src/wheeloffish/main.py
    - backend/tests/api/test_connections_routes.py
    - backend/tests/conftest.py

key-decisions:
  - "In-memory PIN state keyed by pin_id with 15 min TTL — acceptable for ≤5 users Phase 2"
  - "Auto-generate plex_client_identifier when missing on manual token connect"
  - "OAuth callback returns JSON (not redirect) with connection_id; tokens never in response body"

patterns-established:
  - "Pattern: Plex auth module separate from PMS client (plex.tv vs operator base_url)"
  - "Pattern: build_provider_for_connection selects PlexProvider or ephemeral Jellyfin stub"
  - "Pattern: Episode watch mapping — viewCount>0 played override; viewOffset/duration percent"

requirements-completed: [INT-01, INT-02]

duration: 35min
completed: 2026-05-25
---

# Phase 2 Plan 03 Summary

**Plex PIN OAuth connect flow and live PlexProvider listing TV libraries with stable guid-based composite IDs**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- Implemented Plex OAuth auth module (PIN create/poll, token validation, server discovery) with threat-model mitigations T-02-03-01 and T-02-03-03
- Shipped PlexProvider with mappers for Library/Series/Episode; composite IDs use Plex guid, ratingKey resolved internally
- Wired OAuth routes (`/start`, `/callback`, `/status`) and `GET /connections/{id}/libraries` endpoint
- Added 11 integration/API tests with respx mocks; all 49 backend tests pass

## Task Commits

Single plan commit:

1. **All tasks (1–3)** - pending (feat)

**Plan metadata:** pending (this summary)

## Files Created/Modified

- `backend/src/wheeloffish/integrations/plex/` — auth, client, mappers package
- `backend/src/wheeloffish/api/routes/oauth_plex.py` — Plex OAuth PIN flow REST routes
- `backend/src/wheeloffish/core/connections.py` — build_provider_for_connection + list_connection_libraries
- `backend/tests/integrations/test_plex_client.py` — respx tests for OAuth and provider reads

## Decisions Made

- OAuth callback returns JSON with `connection_id` rather than browser redirect (SPA polls status endpoint)
- Removed legacy `integrations/plex.py` stub in favor of `integrations/plex/` package
- Auto-generate `plex_client_identifier` UUID when not supplied on manual POST /connections

## Deviations from Plan

None - plan executed as specified.

## Issues Encountered

- Existing route tests patched `build_ephemeral_provider`; updated to patch `build_provider_for_connection` after factory introduction
- Manual Plex connection POST requires `plex_client_identifier` for real provider ping — auto-generated when absent

## User Setup Required

None - no external service configuration required beyond existing `WOF_OAUTH_CALLBACK_BASE` and `WOF_PLEX_PRODUCT_NAME` settings.

## Verification

- `cd backend && uv run ruff check .` — pass
- `cd backend && uv run pytest -q` — 49 passed
- `pytest tests/integrations/test_plex_client.py -q` — pass
- `pytest tests/api/test_connections_routes.py -k plex -q` — pass

## Next Phase Readiness

- Plex vertical slice complete; ready for Jellyfin provider parity (02-04)
- Libraries endpoint live-fetches; cache population deferred to plan 05
- OAuth tokens stored encrypted in vault; never returned in API bodies

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*
