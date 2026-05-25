---
phase: 03-minimal-operator-spa-shell
plan: 01
subsystem: auth
tags: [fastapi, session, sqlalchemy, alembic, starlette]

requires:
  - phase: 02-media-ingestion-catalogs
    provides: connections catalog tables and Phase 2 API routes
provides:
  - app_users table and AppUser model
  - env-driven connection boot sync on startup
  - SessionMiddleware with configurable TTL
  - GET /auth/me with admin and setup_mode flags
  - POST /auth/bootstrap-session for login wall
  - GET /meta/providers single-provider response
affects: [03-02, 03-04, 03-05, 03-06, 03-07]

tech-stack:
  added: [itsdangerous]
  patterns: [starlette SessionMiddleware, env boot sync upsert]

key-files:
  created:
    - backend/alembic/versions/003_app_users.py
    - backend/src/wheeloffish/db/models/app_user.py
    - backend/src/wheeloffish/core/boot.py
    - backend/src/wheeloffish/core/auth.py
    - backend/src/wheeloffish/api/routes/auth.py
    - backend/src/wheeloffish/api/schemas/auth.py
    - backend/tests/unit/test_boot_sync.py
    - backend/tests/api/test_auth_routes.py
  modified:
    - backend/src/wheeloffish/core/config.py
    - backend/src/wheeloffish/api/deps.py
    - backend/src/wheeloffish/main.py
    - backend/src/wheeloffish/api/routes/meta.py
    - .env.example

key-decisions:
  - "WOF_PROVIDER drives single-provider installs; WOF_ENABLED_PROVIDERS kept for multi-provider test compat when comma-separated"
  - "Session cookie https_only only in production ENVIRONMENT to keep TestClient/dev HTTP working"

patterns-established:
  - "Boot sync upserts one Connection row per WOF_PROVIDER on every app startup"
  - "get_current_user reads app_user_id from signed session cookie; get_app_user_id delegates to it"

requirements-completed: [WEB-01]

duration: 25 min
completed: 2026-05-25
---

# Phase 3 Plan 01: Session Auth Foundation Summary

**Env-synced connection boot plus Starlette session cookies with /auth/me admin and setup_mode gating**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-25T16:35:00Z
- **Completed:** 2026-05-25T17:00:00Z
- **Tasks:** 3
- **Files modified:** 20

## Accomplishments

- `003_app_users` migration and `AppUser` model with unique `provider_user_id`
- `sync_connection_from_env` upserts env connection on lifespan startup
- SessionMiddleware, `/auth/me`, `/auth/bootstrap-session`, `/auth/logout`
- `require_admin` and `is_setup_mode` replace Phase 2 stubs
- `/meta/providers` returns single `provider` + `oauth_callback_base`

## Task Commits

1. **Task 1: Add app_users migration and env config fields** - `85f62f7` (feat)
2. **Task 2: Wire SessionMiddleware, auth routes, and deps** - `cbe1069` (feat)
3. **Task 3: Extend conftest for session auth tests** - `e9bb414` (test)

## Self-Check: PASSED

- `uv run ruff check .` — PASS
- `uv run pytest tests/unit/test_boot_sync.py tests/api/test_auth_routes.py -q` — 9 passed
- `uv run pytest -q` — 79 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added itsdangerous dependency**
- **Found during:** Task 2 (SessionMiddleware)
- **Issue:** Starlette SessionMiddleware requires itsdangerous; not previously declared
- **Fix:** Added `itsdangerous>=2.2` to pyproject.toml
- **Files modified:** backend/pyproject.toml, backend/uv.lock
- **Verification:** App imports and session tests pass
- **Committed in:** cbe1069

**2. [Rule 1 - Bug] Set test ENVIRONMENT=development for session cookies**
- **Found during:** Task 3 (bootstrap-session test)
- **Issue:** `https_only=True` in production blocked session cookies over HTTP in TestClient
- **Fix:** Default `ENVIRONMENT=development` in test conftest before app import
- **Files modified:** backend/tests/conftest.py
- **Verification:** bootstrap-session and /auth/me integration tests pass
- **Committed in:** e9bb414

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Required for session auth correctness; no scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-02 OAuth refactor to env-bound connection and session on callback
- Ready for 03-03 frontend scaffold (parallel after 03-01)

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
