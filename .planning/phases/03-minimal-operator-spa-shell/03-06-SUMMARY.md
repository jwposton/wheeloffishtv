---
phase: 03-minimal-operator-spa-shell
plan: 06
subsystem: ui
tags: [react, tanstack-query, infinite-scroll, debounce, localStorage, vitest]

requires:
  - phase: 03-minimal-operator-spa-shell
    provides: LibraryScopeGuard, auth shell, Phase 2 catalog API integration path
provides:
  - Read-only series browse page with infinite scroll and debounced search
  - Grid/list layout preference persisted in localStorage
  - Non-blocking sync status banner during background catalog sync
affects: [03-07-series-detail, phase-4-playlists]

tech-stack:
  added: []
  patterns:
    - "TanStack useInfiniteQuery against page-based catalog API with sync polling"
    - "300ms debounced search via useDebouncedValue hook"
    - "IntersectionObserver sentinel for infinite scroll load-more"

key-files:
  created:
    - frontend/src/hooks/useDebouncedValue.ts
    - frontend/src/hooks/useSeriesInfiniteQuery.ts
    - frontend/src/hooks/useBrowseLayout.ts
    - frontend/src/components/browse/BrowseToolbar.tsx
    - frontend/src/components/browse/SeriesCard.tsx
    - frontend/src/components/browse/SeriesGrid.tsx
    - frontend/src/components/browse/SeriesList.tsx
    - frontend/src/components/layout/SyncBanner.tsx
    - frontend/src/pages/BrowsePage.tsx
  modified:
    - frontend/src/api/types.ts
    - frontend/src/App.tsx

key-decisions:
  - "Series navigation uses composite series.id in /series/{id} route (detail ships in 03-07)"
  - "SyncBanner sticky at top of browse content; stale series remain visible below during sync.running"

requirements-completed: [WEB-01]

duration: 12min
completed: 2026-05-25
---

# Phase 3 Plan 06: Series Browse Summary

**Read-only series browser with TanStack infinite query, 300ms debounced search, grid/list layout toggle, and non-blocking sync banner**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-25T13:11:00Z
- **Completed:** 2026-05-25T13:13:00Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments

- Catalog browse hooks: `useDebouncedValue` (300ms) and `useSeriesInfiniteQuery` (limit 50, sync polling every 3s)
- Browse UI components: grid/list layouts, keyboard-focusable `SeriesCard`, `BrowseToolbar`, sticky `SyncBanner`
- `BrowsePage` at `/browse` with IntersectionObserver infinite scroll, skeleton loading, and empty state
- TypeScript types aligned with backend `SeriesBrowseResponse`, `Series`, `SyncStatusEmbed`

## Task Commits

1. **Task 1 RED:** Debounced search and infinite query hook tests — `e52a3be` (test)
2. **Task 1 GREEN:** Debounced search and infinite query hooks — `5a2e577` (feat)
3. **Task 2 RED:** Browse layout and sync banner tests — `f6dd8b5` (test)
4. **Task 2 GREEN:** Browse layout components and sync banner — `2de4573` (feat)
5. **Task 3:** BrowsePage with infinite scroll — `1fddd1d` (feat)

## Verification Results

```
cd frontend && npm run test -- --run
# 6 test files, 10 tests passed

cd frontend && npm run build
# tsc + vite build succeeded
```

Acceptance criteria:
- Infinite query uses limit 50 (`SERIES_PAGE_LIMIT`) — PASS
- Debounce interval 300ms verified in hook test — PASS
- Grid default layout via `useBrowseLayout` — PASS
- SyncBanner visible when `sync.status === 'running'` — PASS
- SeriesCard uses `<button>` with focus-visible ring — PASS

## Files Created/Modified

- `frontend/src/hooks/useDebouncedValue.ts` — Generic debounce hook for search input
- `frontend/src/hooks/useSeriesInfiniteQuery.ts` — Infinite catalog query with sync-aware polling
- `frontend/src/hooks/useBrowseLayout.ts` — Grid/list preference in `wof.browse.layout`
- `frontend/src/components/browse/*` — Toolbar, card, grid, and list renderers
- `frontend/src/components/layout/SyncBanner.tsx` — Sticky "Updating library…" banner
- `frontend/src/pages/BrowsePage.tsx` — Browse route page with infinite scroll sentinel
- `frontend/src/api/types.ts` — Catalog DTO types
- `frontend/src/App.tsx` — Registers `BrowsePage` under `LibraryScopeGuard`

## Decisions Made

- Series detail route (`/series/{id}`) registered for navigation but detail page is out of scope for this plan (03-07)
- SyncBanner uses sticky positioning within browse content rather than viewport-fixed overlay

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Browse vertical slice complete; ready for 03-07 series detail + resume preview
- `/series/{composite_id}` navigation wired from cards; detail page not yet implemented

## Self-Check: PASSED

- All key files present on disk
- Commits e52a3be, 5a2e577, f6dd8b5, 2de4573, 1fddd1d verified in git log
- Full test suite and production build pass

---
*Phase: 03-minimal-operator-spa-shell*
*Completed: 2026-05-25*
