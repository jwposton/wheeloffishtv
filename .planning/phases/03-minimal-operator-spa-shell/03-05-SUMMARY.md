---
phase: 03-minimal-operator-spa-shell
plan: 05
subsystem: ui
tags: [react, tanstack-query, shadcn, library-scope, sonner]

requires:
  - phase: 03-minimal-operator-spa-shell
    provides: useAuth, ProtectedRoute, AdminRoute, AppShell from plans 03-01–03-04
provides:
  - useLibraryScope hook with admin GET/PUT library scope APIs
  - LibraryScopeForm checkbox UI with toast feedback
  - Admin first-run library picker at /setup/libraries
  - Settings → Libraries permanent scope editor
  - HoldingPage for non-admins when scope unset
  - LibraryScopeGuard gating /browse by libraries_scoped and role
affects:
  - 03-06-series-browser
  - 03-07-polish

tech-stack:
  added: []
  patterns:
    - "TanStack Query hook with auth + libraries cache invalidation on scope save"
    - "Route guard layering: ProtectedRoute → AppShell → LibraryScopeGuard for browse"

key-files:
  created:
    - frontend/src/hooks/useLibraryScope.ts
    - frontend/src/components/admin/LibraryScopeForm.tsx
    - frontend/src/pages/AdminLibrarySetupPage.tsx
    - frontend/src/pages/SettingsLibrariesPage.tsx
    - frontend/src/pages/HoldingPage.tsx
    - frontend/src/routes/LibraryScopeGuard.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/pages/SettingsPage.tsx
    - frontend/src/api/types.ts
    - frontend/src/main.tsx

key-decisions:
  - "LibraryScopeForm returns null when !is_admin || setup_mode (T-03-05-01 mitigation)"
  - "Toaster mounted in main.tsx for sonner toast on scope save success/error"

patterns-established:
  - "libraryScopeQueryKey(connectionId) for admin libraries cache key"
  - "onSaveSuccess callback on LibraryScopeForm for first-run continue gate"

requirements-completed: [WEB-01]

duration: 12min
completed: 2026-05-25
---

# Phase 3 Plan 05: Library Scope Admin UI Summary

**Admin checkbox library scoping with first-run checklist, settings editor, and role-based browse gating via LibraryScopeGuard**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-25T17:00:00Z
- **Completed:** 2026-05-25T17:10:31Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- `useLibraryScope` fetches admin libraries with `in_scope` flags and PUTs `in_scope_library_native_ids`
- Reusable `LibraryScopeForm` with shadcn checkboxes, save mutation, and sonner toasts
- First-run admin flow at `/setup/libraries` with continue-to-browse gate after ≥1 library saved
- Settings → Libraries link and `/settings/libraries` page for ongoing scope edits
- `HoldingPage` for non-admins when `libraries_scoped === false`
- `LibraryScopeGuard` redirects unscoped admins to setup and blocks unscoped non-admins

## Task Commits

Each task was committed atomically:

1. **Task 1: useLibraryScope hook and LibraryScopeForm** - `6894078` (feat)
2. **Task 2: First-run admin checklist and Settings → Libraries** - `4b054e6` (feat)
3. **Task 3: Non-admin holding page and LibraryScopeGuard** - `58d5bc6` (feat)

## Verification Results

| Check | Result |
|-------|--------|
| `cd frontend && npm run build` (Task 1) | PASS |
| `cd frontend && npm run build` (Task 2) | PASS |
| `cd frontend && npm run build` (Task 3) | PASS |
| GET admin libraries + in_scope flags | PASS — `useLibraryScope.ts` |
| PUT sends `in_scope_library_native_ids` | PASS — `LibraryScopeForm.tsx`, `useLibraryScope.ts` |
| Admin routes `/setup/libraries`, `/settings/libraries` | PASS — `App.tsx` |
| Settings exposes Libraries section | PASS — `SettingsPage.tsx` |
| Non-admin holding when unscoped | PASS — `LibraryScopeGuard.tsx` → `HoldingPage` |
| Admin redirect when unscoped | PASS — `LibraryScopeGuard.tsx` → `/setup/libraries` |

## Files Created/Modified

- `frontend/src/hooks/useLibraryScope.ts` - TanStack Query hook for admin library list and scope PUT
- `frontend/src/components/admin/LibraryScopeForm.tsx` - Checkbox scope UI with save + toast
- `frontend/src/pages/AdminLibrarySetupPage.tsx` - First-run checklist with continue gate
- `frontend/src/pages/SettingsLibrariesPage.tsx` - Permanent scope editor page
- `frontend/src/pages/HoldingPage.tsx` - Non-admin waiting state copy
- `frontend/src/routes/LibraryScopeGuard.tsx` - Browse route guard by role and scope
- `frontend/src/App.tsx` - Wired admin and guarded browse routes
- `frontend/src/pages/SettingsPage.tsx` - Libraries section link for admins
- `frontend/src/api/types.ts` - Library and LibraryScope DTO types
- `frontend/src/main.tsx` - Mounted Toaster for sonner notifications

## Decisions Made

- LibraryScopeForm self-guards admin-only rendering (`is_admin && !setup_mode`) per threat model T-03-05-01
- Added Toaster to `main.tsx` (sonner was installed but not mounted in prior plans)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Mounted Toaster for toast notifications**
- **Found during:** Task 1 (LibraryScopeForm)
- **Issue:** `sonner` Toaster component existed but was not rendered; toast calls would be no-ops
- **Fix:** Import and render `<Toaster />` in `main.tsx`
- **Files modified:** `frontend/src/main.tsx`
- **Verification:** Build passes; Toaster present in app tree
- **Committed in:** `6894078` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Required for specified toast UX; no scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Library scope vertical slice complete; browse route is gated and ready for series browser (03-06)
- Admin can scope libraries via UI; non-admins see holding page until scoped

## Self-Check: PASSED

- All 6 key created files exist on disk
- Commits verified: `6894078`, `4b054e6`, `58d5bc6`
- Plan-level `npm run build` passed on final task

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
