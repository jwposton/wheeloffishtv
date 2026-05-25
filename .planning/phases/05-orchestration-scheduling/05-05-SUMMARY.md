---
phase: "05-orchestration-scheduling"
plan: "05"
subsystem: "frontend"
tags: ["spa", "playlists", "tanstack-query", "shadcn", "tdd"]
dependency_graph:
  requires: ["05-04"]
  provides: ["WEB-01-partial", "D-19", "D-20", "D-21"]
  affects: ["frontend/src/pages", "frontend/src/components/playlists", "frontend/src/api"]
tech_stack:
  added: []
  patterns: ["TanStack Query useQuery", "shadcn Badge + Card + Skeleton", "TDD vitest"]
key_files:
  created:
    - frontend/src/api/playlists.ts
    - frontend/src/components/playlists/StatusBadge.tsx
    - frontend/src/components/playlists/PlaylistCard.tsx
    - frontend/src/pages/PlaylistsPage.tsx
    - frontend/src/pages/PlaylistsPage.test.tsx
  modified:
    - frontend/src/api/types.ts
    - frontend/src/App.tsx
    - frontend/src/components/layout/AppShell.tsx
decisions:
  - "Inline formatRelativeTime helper — no date-fns dependency added (not in project)"
  - "Route /playlists placed inside LibraryScopeGuard (same level as /browse) per ProtectedRoute pattern"
  - "RebuildStatus null rendered as outline muted 'Never rebuilt' badge per UI-SPEC"
metrics:
  duration: "~7 minutes"
  completed: "2026-05-25"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 7
---

# Phase 5 Plan 05: SPA Playlist List Page Summary

SPA vertical slice delivering playlist list at `/playlists` — TanStack Query hook, semantic status badges, card grid, empty state, nav link, and 6-test suite.

## What Was Built

**Task 1: API types and usePlaylists hook** (`52d713a`)
- Added `RebuildStatus`, `RefreshCadence`, `PlaylistListItem` types to `types.ts`
- Created `playlists.ts` with `fetchPlaylists()`, `usePlaylists()` (queryKey `['playlists','list']`, staleTime 30 000 ms), and `formatCadence()` helper (returns "Daily" or "Weekly · {DayName}")

**Task 2: StatusBadge + test** (`f66569b`)
- `StatusBadge` maps `succeeded`→green outline, `partial`→amber secondary, `failed`→destructive, `running|queued`→secondary "Rebuilding…", `null`→outline muted "Never rebuilt"
- 6 vitest tests covering all status branches including null and type exhaustiveness

**Task 3: PlaylistsPage, PlaylistCard, routing, nav** (`e5f932d`)
- `PlaylistCard` links to `/playlists/:id`, shows name, `formatCadence`, `StatusBadge`, relative rebuild time (inline helper; no extra library)
- `PlaylistsPage` has header "Playlists" + "New playlist" CTA, grid with loading skeletons, error toast via sonner, empty state with UI-SPEC copywriting
- `App.tsx` route `/playlists` inside `LibraryScopeGuard` + `ProtectedRoute` (same level as `/browse`)
- `AppShell` nav: "Playlists" link between Browse and Settings with active state via `navLinkClass`

## Verification

```
✓ src/pages/PlaylistsPage.test.tsx (6 tests) 23ms
✓ built in 137ms
```

## Deviations from Plan

**1. [Rule 3 - Dependency] Inline relative-time helper instead of date-fns**
- **Found during:** Task 3
- **Issue:** `date-fns` is not installed in the project; plan said "date-fns formatDistanceToNow or simple ISO fallback"
- **Fix:** Implemented a 15-line `formatRelativeTime` helper directly in `PlaylistCard.tsx` (min/hour/day buckets), avoiding a new dependency install
- **Files modified:** `frontend/src/components/playlists/PlaylistCard.tsx`

## Known Stubs

None — `usePlaylists` is wired to the real API endpoint `/api/v1/playlists`.

## Threat Flags

No new trust-boundary surface introduced. `PlaylistsPage` is behind `ProtectedRoute` + `LibraryScopeGuard` (T-05-05-01 mitigated). Error messages rendered as plain text nodes via JSX text children (T-05-05-02 mitigated).

## Self-Check: PASSED
- `frontend/src/api/playlists.ts` — FOUND
- `frontend/src/components/playlists/StatusBadge.tsx` — FOUND
- `frontend/src/components/playlists/PlaylistCard.tsx` — FOUND
- `frontend/src/pages/PlaylistsPage.tsx` — FOUND
- `frontend/src/pages/PlaylistsPage.test.tsx` — FOUND
- Commits `52d713a`, `f66569b`, `e5f932d` — FOUND
