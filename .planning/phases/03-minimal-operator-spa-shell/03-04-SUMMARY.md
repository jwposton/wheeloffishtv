---
phase: 03-minimal-operator-spa-shell
plan: 04
subsystem: auth
tags: [react, tanstack-query, oauth, vitest, react-router]

requires:
  - phase: 03-minimal-operator-spa-shell
    provides: Session auth, OAuth routes, SPA mount, Vite/React scaffold
provides:
  - useAuth hook with /auth/me TanStack Query
  - ProtectedRoute auth gate with return URL redirect
  - LoginPage with Plex OAuth and Jellyfin credential form
  - AdminSetupPage with provider_user_id copy panel
  - SettingsPage read-only connection display
  - AppShell with nav, theme toggle, logout
affects: [03-05, 03-06, browse, library-scope]

tech-stack:
  added: []
  patterns:
    - "TanStack Query authQueryKey ['auth','me'] with 401 no-retry"
    - "ProtectedRoute requires has_media_link after OAuth"
    - "SetupModeGate redirects to /setup/admin unless browsing scoped libraries"

key-files:
  created:
    - frontend/src/hooks/useAuth.ts
    - frontend/src/api/types.ts
    - frontend/src/routes/ProtectedRoute.tsx
    - frontend/src/routes/ProtectedRoute.test.tsx
    - frontend/src/pages/LoginPage.tsx
    - frontend/src/pages/AdminSetupPage.tsx
    - frontend/src/pages/SettingsPage.tsx
    - frontend/src/components/auth/PlexLoginButton.tsx
    - frontend/src/components/auth/JellyfinLoginForm.tsx
    - frontend/src/components/auth/AdminSetupPanel.tsx
    - frontend/src/components/layout/AppShell.tsx
    - frontend/src/routes/AdminRoute.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx

key-decisions:
  - "ProtectedRoute treats users without has_media_link as unauthenticated to block bootstrap pending sessions"
  - "SetupModeGate allows /browse when libraries_scoped per D-04 non-blocking browse"

requirements-completed: [WEB-01]

duration: 2 min
completed: 2026-05-25
---

# Phase 3 Plan 04: Auth Vertical Slice Summary

**TanStack Query auth gate, provider-specific login wall, admin discovery copy panel, and read-only settings shell**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-25T17:07:00Z
- **Completed:** 2026-05-25T17:09:11Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- Client-side auth gate via `useAuth` + `ProtectedRoute` with skeleton loading and `/login?returnUrl=` redirect
- Login wall with bootstrap session, Plex OAuth start, and Jellyfin credential POST — no server URL inputs (D-09)
- Admin setup screen with `provider_user_id` clipboard copy and env restart instructions (D-04)
- Settings shows read-only "Connected to {base_url} ({display_name})" (D-08)
- AppShell nav with Browse, Settings, theme toggle, and POST `/auth/logout`

## Task Commits

1. **Task 1: useAuth hook and ProtectedRoute (TDD)** — `4dbdc1d` (test), `abe8c6b` (feat)
2. **Task 2: LoginPage with Plex OAuth and Jellyfin form** — `51c1447` (feat)
3. **Task 3: Admin setup screen and read-only Settings** — `572ab8f` (feat)

## Verification Results

```text
cd frontend && npm run test -- --run
✓ 2 test files, 3 tests passed

cd frontend && npm run build
✓ tsc -b && vite build succeeded
```

Acceptance criteria:
- AuthMeResponse includes `setup_mode` and `is_admin` — PASS
- ProtectedRoute redirect/render tests — PASS
- LoginPage has no base_url or provider selector inputs — PASS (grep)
- Plex button calls `/connections/plex/oauth/start` — PASS
- Jellyfin form posts to `/connections/jellyfin/auth` — PASS
- AdminSetupPage renders provider_user_id copy UI — PASS
- SettingsPage read-only connection URL — PASS
- Logout via POST `/auth/logout` in AppShell — PASS

## Files Created/Modified

- `frontend/src/hooks/useAuth.ts` — TanStack Query wrapper for GET `/auth/me`
- `frontend/src/routes/ProtectedRoute.tsx` — Auth gate with skeleton and redirect
- `frontend/src/pages/LoginPage.tsx` — Provider-specific sign-in wall
- `frontend/src/components/auth/AdminSetupPanel.tsx` — Operator admin ID copy panel
- `frontend/src/components/layout/AppShell.tsx` — Header nav, setup gate, logout
- `frontend/src/App.tsx` — Route tree wiring login, protected shell, setup, settings

## Decisions Made

- Bootstrap pending sessions (no `has_media_link`) cannot access protected routes — prevents bypassing login wall before OAuth
- SetupModeGate permits `/browse` when `libraries_scoped` so setup mode stays non-blocking per D-04

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Require has_media_link for protected access**
- **Found during:** Task 2 (LoginPage routing)
- **Issue:** Bootstrap session creates a pending `AppUser` that passes `/auth/me` without OAuth, bypassing the login wall
- **Fix:** `ProtectedRoute` redirects when `!user.has_media_link`
- **Files modified:** `frontend/src/routes/ProtectedRoute.tsx`
- **Verification:** ProtectedRoute tests pass; unauthenticated flow reaches LoginPage
- **Committed in:** `51c1447`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Required for D-01/D-09 login wall correctness. No scope creep.

## Known Stubs

| File | Reason |
|------|--------|
| `frontend/src/App.tsx` `BrowsePlaceholderPage` | Catalog browser ships in plan 03-05 |
| `frontend/src/App.tsx` `HomePage` | Placeholder until browse/plan routes land |

## Issues Encountered

None

## Next Phase Readiness

- Auth vertical slice complete — ready for 03-05 catalog browse wiring
- `AdminRoute` wrapper in place for future admin-only library scope UI

## Self-Check: PASSED

- All 13 key files FOUND on disk
- Commits `4dbdc1d`, `abe8c6b`, `51c1447`, `572ab8f` verified via `git rev-parse`
- Plan verification commands passed (3 tests, build OK)

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
