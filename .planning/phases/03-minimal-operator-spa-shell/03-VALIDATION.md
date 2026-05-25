---
phase: 3
slug: minimal-operator-spa-shell
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-25
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio (backend); vitest + @testing-library/react (frontend) |
| **Config file** | `backend/pyproject.toml`; `frontend/vitest.config.ts` (Wave 0) |
| **Quick run command** | `cd backend && uv run pytest tests/unit -q` OR `cd frontend && npm run test -- --run` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest && cd ../frontend && npm run test -- --run && npm run build` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** backend `uv run pytest tests/unit -q` OR frontend `npm run test -- --run` (whichever changed)
- **After every plan wave:** full backend pytest + frontend vitest + `npm run build`
- **Before `/gsd-verify-work`:** Full suites green + manual keyboard/browse UAT
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | WEB-01 | T-01 | Session cookie httpOnly | unit | `uv run pytest tests/unit/test_boot_sync.py -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | WEB-01 | T-02 | Unauthenticated `/auth/me` → 401 | integration | `uv run pytest tests/api/test_auth_routes.py -k unauthenticated -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | WEB-01 | T-03 | `require_admin` returns 403 for non-admin | integration | `uv run pytest tests/api/test_auth_routes.py -k require_admin -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | WEB-01 | T-04 | Session cookie set on OAuth callback | integration | `uv run pytest tests/api/test_auth_routes.py -k session_cookie -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | WEB-01 | T-05 | Setup mode allows browse, blocks admin PUT | integration | `uv run pytest tests/api/test_catalog_routes.py -k setup_mode -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | WEB-01 | — | SPA index served at `/` | integration | `uv run pytest tests/api/test_spa_routes.py -k index -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 1 | WEB-01 | — | SPA fallback for `/browse` | integration | `uv run pytest tests/api/test_spa_routes.py -k fallback -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 2 | WEB-01 | — | Login wall redirects unauthenticated users | frontend component | `npm run test -- --run src/routes/ProtectedRoute.test.tsx` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 2 | WEB-01 | — | Infinite query fetches next page | frontend unit | `npm run test -- --run src/hooks/useSeriesInfiniteQuery.test.ts` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 2 | WEB-01 | — | Debounced search resets pages | frontend unit | `npm run test -- --run src/hooks/useDebouncedValue.test.ts` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 2 | WEB-01 | — | Sync banner shown when sync.status=running | frontend component | `npm run test -- --run src/components/SyncBanner.test.tsx` | ❌ W0 | ⬜ pending |
| 03-05-02 | 05 | 2 | WEB-01 | — | Grid/list preference persists localStorage | frontend unit | `npm run test -- --run src/hooks/useBrowseLayout.test.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Migration `003_app_users.py` + `AppUser` model
- [ ] `core/boot.py` env→DB sync + unit tests
- [ ] `api/routes/auth.py` + session middleware wiring
- [ ] Refactor `oauth_plex.py` / `oauth_jellyfin.py` for env connection
- [ ] `SPAStaticFiles` mount + `tests/api/test_spa_routes.py`
- [ ] `frontend/` Vite scaffold + shadcn init + vitest config
- [ ] Docker multi-stage frontend build in `backend/Dockerfile`
- [ ] Update `.env.example` with Phase 3 vars
- [ ] Extend `Library` DTO with `in_scope` if missing for admin UI

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Keyboard: series grid items focusable | WEB-01 | axe/Lighthouse deferred Phase 7 | Tab through browse grid; Enter opens detail |
| Admin library scope checkbox saves | WEB-01 | Requires admin session + live DB | Admin toggles library → refresh → scope persists |
| Plex OAuth E2E | WEB-01 | Requires real Plex account | Complete PIN flow; verify browse loads |
| Jellyfin auth E2E | WEB-01 | Requires real Jellyfin server | Authenticate; verify browse loads |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
