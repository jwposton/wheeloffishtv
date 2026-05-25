---
phase: 03-minimal-operator-spa-shell
plan: 03
subsystem: ui
tags: [vite, react, typescript, tailwindcss, shadcn, tanstack-query, fastapi, docker, spa]

requires:
  - phase: 03-01
    provides: Session auth and env-bound connection boot sync
  - phase: 03-02
    provides: OAuth flows with session cookies
provides:
  - Greenfield Vite+React+TS frontend with shadcn/ui and TanStack Query
  - SPAStaticFiles mount with client-route fallback
  - Multi-stage Docker build embedding frontend dist
  - Vitest + Testing Library baseline
affects: [03-04, auth-gate, browse-ui]

tech-stack:
  added: [vite, react, typescript, tailwindcss, @tanstack/react-query, react-router-dom, next-themes, shadcn/ui, vitest, @testing-library/react]
  patterns: [SPAStaticFiles fallback, /api dev proxy, credentials:include API client, create_app factory]

key-files:
  created:
    - frontend/vite.config.ts
    - frontend/vitest.config.ts
    - frontend/src/api/client.ts
    - frontend/src/components/layout/ThemeProvider.tsx
    - backend/src/wheeloffish/api/spa.py
    - backend/tests/api/test_spa_routes.py
  modified:
    - backend/src/wheeloffish/main.py
    - backend/src/wheeloffish/core/config.py
    - backend/Dockerfile
    - compose.yml
    - frontend/README.md

key-decisions:
  - "SPA mount gated on dist/index.html existence so local backend dev works without a built frontend"
  - "Docker build context widened to repo root to include frontend/ in multi-stage image"
  - "shadcn v4 sonner used instead of legacy toast component (equivalent notification primitive)"

patterns-established:
  - "Pattern: fetchJson at /api/v1 with credentials:include for session cookies"
  - "Pattern: API routers registered before SPAStaticFiles mount at /"

requirements-completed: [WEB-01]

duration: 45min
completed: 2026-05-25
---

# Phase 3 Plan 03: Frontend SPA Shell Summary

**Vite+React operator shell with shadcn theme tokens, TanStack Query wiring, and FastAPI SPAStaticFiles served from Docker multi-stage build**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-05-25T16:21:00Z
- **Completed:** 2026-05-25T17:06:38Z
- **Tasks:** 2 completed (Task 1 checkpoint cleared by human approval)
- **Files modified:** 43

## Accomplishments

- Bootstrapped `frontend/` with Vite, React 19, Tailwind v4, shadcn/ui, TanStack Query, React Router, and next-themes (system default)
- Added `/api` dev proxy to port 8000 and `fetchJson` client with `credentials: "include"`
- Implemented `SPAStaticFiles` with index.html fallback for `/browse` deep links
- Extended Dockerfile with `frontend-build` stage; compose build context now repo root

## Task Commits

Each task was committed atomically:

1. **Task 2: Scaffold frontend** - `8969587` (feat)
2. **Task 3: Mount SPAStaticFiles + Docker** - `caed36c` (feat)

## Verification Results

```bash
cd backend && uv run pytest tests/api/test_spa_routes.py -q
# 2 passed

cd ../frontend && npm run build
# built successfully

cd frontend && npm run test -- --run
# 1 passed
```

## Files Created/Modified

- `frontend/vite.config.ts` - Tailwind plugin, `@` alias, `/api` proxy to :8000
- `frontend/src/main.tsx` - QueryClientProvider, BrowserRouter, ThemeProvider
- `frontend/src/api/client.ts` - Session-aware fetch wrapper
- `backend/src/wheeloffish/api/spa.py` - SPAStaticFiles 404→index.html
- `backend/src/wheeloffish/main.py` - `create_app()` with conditional SPA mount
- `backend/Dockerfile` - node:22-alpine frontend-build stage
- `backend/tests/api/test_spa_routes.py` - `/` and `/browse` HTML fallback tests

## Decisions Made

- SPA mount only when `SPA_DIST_DIR/index.html` exists — avoids breaking local backend pytest/dev without a frontend build
- Compose build context changed from `./backend` to `.` with `dockerfile: backend/Dockerfile` so frontend sources are available in Docker build
- shadcn CLI v4 placed components under literal `@/` path; moved to `src/components/ui/` manually

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] shadcn CLI wrote files to literal `@/` directory**
- **Found during:** Task 2
- **Issue:** `npx shadcn init/add` created `@/components/ui/` instead of `src/components/ui/`
- **Fix:** Moved all generated components to `src/components/ui/`
- **Files modified:** `frontend/src/components/ui/*`
- **Verification:** `npm run build` passes
- **Committed in:** 8969587

**2. [Rule 3 - Blocking] TypeScript build errors in scaffold**
- **Found during:** Task 2
- **Issue:** `erasableSyntaxOnly` rejected parameter properties in `ApiError`; `baseUrl` deprecation error
- **Fix:** Explicit class fields; added `ignoreDeprecations: "6.0"`
- **Files modified:** `frontend/src/api/client.ts`, `frontend/tsconfig.app.json`
- **Verification:** `npm run build` passes
- **Committed in:** 8969587

**3. [Rule 3 - Blocking] Vitest missing matchMedia mock for next-themes**
- **Found during:** Task 2
- **Issue:** `window.matchMedia is not a function` in jsdom
- **Fix:** Added matchMedia stub in `src/test/setup.ts`
- **Verification:** `npm run test -- --run` passes
- **Committed in:** 8969587

**4. [Rule 2 - Missing Critical] Conditional SPA mount for dev/test ergonomics**
- **Found during:** Task 3
- **Issue:** Unconditional mount would fail when `/app/static/spa` missing in local dev
- **Fix:** `spa_dist_exists()` guard before mount; extracted `create_app()` factory
- **Files modified:** `backend/src/wheeloffish/api/spa.py`, `backend/src/wheeloffish/main.py`
- **Verification:** SPA tests pass; existing health/auth tests unaffected
- **Committed in:** caed36c

---

**Total deviations:** 4 auto-fixed (3 blocking, 1 missing critical)
**Impact on plan:** All necessary for build/test correctness. No scope creep.

## Issues Encountered

- Pre-existing failure in `tests/integrations/test_jellyfin_client.py::test_dto_shape_matches_plex` (unrelated `in_scope` field drift) — out of scope, not introduced by this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Frontend shell ready for auth gate and browse routes (plans 03-04+)
- Production container serves React at `/` on port 8000 after `docker compose build`
- Local dev: run backend on :8000, `npm run dev` in frontend for HMR with proxied API

## Self-Check: PASSED

- FOUND: frontend/vite.config.ts
- FOUND: frontend/vitest.config.ts
- FOUND: frontend/src/api/client.ts
- FOUND: frontend/src/components/layout/ThemeProvider.tsx
- FOUND: backend/src/wheeloffish/api/spa.py
- FOUND: backend/tests/api/test_spa_routes.py
- FOUND: backend/Dockerfile
- FOUND: commit 8969587 (Task 2)
- FOUND: commit caed36c (Task 3)

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
