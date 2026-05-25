---
phase: 03-minimal-operator-spa-shell
plan: 02
subsystem: api
tags: [oauth, plex, jellyfin, session, catalog, env-config]

requires:
  - phase: 03-01
    provides: Session auth, boot sync, AppUser model, require_admin, bootstrap-session
provides:
  - Env-bound Plex PIN OAuth with link_media_user
  - Env-bound Jellyfin username/password auth
  - POST /connections gated with env_config_only
  - Admin GET libraries with in_scope flags
  - Session-protected catalog browse routes
affects: [03-03, 03-04, 03-05]

tech-stack:
  added: []
  patterns:
    - "OAuth callbacks link to boot-synced connection via link_media_user"
    - "WOF_PROVIDER single-provider gate on oauth routes"
    - "Connection CRUD blocked; env is sole config source"

key-files:
  created: []
  modified:
    - backend/src/wheeloffish/api/routes/oauth_plex.py
    - backend/src/wheeloffish/api/routes/oauth_jellyfin.py
    - backend/src/wheeloffish/api/routes/connections.py
    - backend/src/wheeloffish/api/routes/catalog.py
    - backend/src/wheeloffish/core/connections.py
    - backend/src/wheeloffish/core/catalog_sync.py
    - backend/src/wheeloffish/domain/dto.py
    - backend/src/wheeloffish/integrations/plex/auth.py
    - backend/tests/api/test_auth_routes.py
    - backend/tests/api/test_connections_routes.py
    - backend/tests/api/test_catalog_routes.py

key-decisions:
  - "Plex OAuth callback redirects to SPA (302) instead of JSON 201"
  - "PIN state stores connection_id; session_mismatch guard on callback"
  - "Jellyfin auth returns JSON 201 with session cookie (form POST flow)"

patterns-established:
  - "link_media_user: upsert UserMediaLink + vault token against env connection"
  - "Admin GET /admin/connections/{id}/libraries returns all libraries with in_scope"

requirements-completed: [WEB-01]

duration: 25min
completed: 2026-05-25
---

# Phase 3 Plan 2: OAuth Refactor Summary

**Env-bound Plex/Jellyfin auth linking media accounts to boot-synced connection with session cookies and catalog admin library listing**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Plex OAuth start/callback binds to env connection row via `link_media_user`; no client `base_url`
- Jellyfin auth accepts `{username, password}` only; server URL from env connection
- OAuth callbacks set `request.session["app_user_id"]` after upserting provider user
- `POST /api/v1/connections` returns 403 `env_config_only` (D-06)
- Catalog routes session-protected; admin GET libraries returns all libraries with `in_scope` flag
- setup_mode blocks admin PUT library-scope (403)

## Task Commits

1. **Task 1: Refactor Plex OAuth to env connection** — `ca18cb5` (test), `43c83cd` (feat)
2. **Task 2: Refactor Jellyfin auth and gate connection CRUD** — `7ca6c5a` (feat)
3. **Task 3: Session-protect catalog routes, admin libraries endpoint** — `2a66db6` (feat)

## Files Created/Modified

- `backend/src/wheeloffish/core/connections.py` — `link_media_user` helper
- `backend/src/wheeloffish/api/routes/oauth_plex.py` — env-bound PIN flow, session on callback
- `backend/src/wheeloffish/api/routes/oauth_jellyfin.py` — env-bound Jellyfin auth
- `backend/src/wheeloffish/api/routes/connections.py` — gate POST with env_config_only
- `backend/src/wheeloffish/api/routes/catalog.py` — admin libraries route, auth on browse
- `backend/src/wheeloffish/domain/dto.py` — `Library.in_scope` field
- `backend/src/wheeloffish/core/catalog_sync.py` — `get_all_libraries`, DTO in_scope population

## Decisions Made

- Plex callback uses 302 redirect to `WOF_OAUTH_CALLBACK_BASE` (`/` or `/setup`) per SPA login flow
- Callback validates PIN `app_user_id` matches session before linking (T-03-02-04)
- Connection tests use real session bootstrap instead of dependency overrides for OAuth flows

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Connection tests needed session cookies for OAuth callback**
- **Found during:** Task 2
- **Issue:** Dependency overrides bypass SessionMiddleware; callback session_mismatch guard blocked tests
- **Fix:** Refactored `connections_client` fixture to bootstrap session; pin state uses session user id
- **Files modified:** `backend/tests/api/test_connections_routes.py`
- **Committed in:** `7ca6c5a`

**2. [Rule 3 - Blocking] Plex list libraries test patched wrong module**
- **Found during:** Task 2
- **Issue:** Patch targeted `core.connections` but `ensure_libraries_cached` imports from `catalog_sync`
- **Fix:** Patch `wheeloffish.core.catalog_sync.build_provider_for_connection`
- **Files modified:** `backend/tests/api/test_connections_routes.py`
- **Committed in:** `7ca6c5a`

---

**Total deviations:** 2 auto-fixed (both Rule 3 blocking test issues)
**Impact on plan:** Test infrastructure fixes only; no API behavior changes.

## Issues Encountered

None beyond test fixture adjustments documented above.

## User Setup Required

None — uses existing env vars from Phase 3 plan 01.

## Next Phase Readiness

- Media-server login path complete for SPA integration (plan 03-03+)
- Admin library checkbox UI can consume `GET /admin/connections/{id}/libraries` with `in_scope` flags
- Series browse requires authenticated session (use bootstrap-session or post-OAuth session)

## Self-Check: PASSED

- FOUND: `.planning/phases/03-minimal-operator-spa-shell/03-02-SUMMARY.md`
- FOUND: `ca18cb5`
- FOUND: `43c83cd`
- FOUND: `7ca6c5a`
- FOUND: `2a66db6`
- Verification: 31 tests passed (`test_auth_routes`, `test_catalog_routes`, `test_connections_routes`)

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
