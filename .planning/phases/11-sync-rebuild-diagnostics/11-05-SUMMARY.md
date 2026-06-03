---
phase: 11-sync-rebuild-diagnostics
plan: 05
subsystem: ui
tags: [react, vitest, rebuild, diagnostics, writeback]

requires:
  - phase: 11-sync-rebuild-diagnostics
    provides: RebuildDiagnosticsDialog and shouldShowDiagnostics (Plan 04)
provides:
  - Panel-level View details trigger and modal host on RebuildBanner
  - Detail writeback surface without inline bullet lists
  - PlaylistDetailPage prune events and remove-row wiring
affects: []

tech-stack:
  added: []
  patterns:
    - "Granular sync/rebuild detail on-demand via single View details link (D-01–D-04)"
    - "Inline failed error_message removed from banner; modal owns detail (D-07, T-11-03)"

key-files:
  created:
    - frontend/src/components/playlists/RebuildBanner.test.tsx
    - frontend/src/components/playlists/WritebackStatus.test.tsx
  modified:
    - frontend/src/components/playlists/RebuildBanner.tsx
    - frontend/src/components/playlists/WritebackStatus.tsx
    - frontend/src/pages/PlaylistDetailPage.tsx
    - frontend/src/pages/PlaylistDetailPage.test.tsx

key-decisions:
  - "Remove snapshot/episodeTitlesById from banner; WritebackStatus no longer renders per-episode lists on detail"
  - "Remove-row from modal uses existing useRemovePlaylistRow without extra confirm (Phase 11 discretion)"

patterns-established:
  - "shouldShowDiagnostics gates single View details link at panel bottom"
  - "Compact WritebackStatus unchanged; detail shows badge + one-liners only"

requirements-completed: [DIAG-01, DIAG-05]

duration: 18min
completed: 2026-06-03
---

# Phase 11 Plan 05: Operator Surface Summary

**Single View details entry point on the rebuild panel with modal diagnostics; inline lists and failed error paragraph removed from the banner**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-03T02:00:00Z
- **Completed:** 2026-06-03T02:18:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Extended `RebuildBanner` with `View details` link gated by `shouldShowDiagnostics`, local modal state, and `RebuildDiagnosticsDialog` host; removed inline failed `error_message` paragraph.
- Stripped non-compact `WritebackStatus` episode/info `<ul>` lists while preserving badge, provider link, failed one-liner, and partial summary; compact mode unchanged.
- Wired `PlaylistDetailPage` with `recent_prune_events`, `onRemoveRow` via `useRemovePlaylistRow`, and toast feedback for success/stale removal.

## Task Commits

Each task was committed atomically:

1. **Task 1: RebuildBanner trigger + modal host** - `5b2518c` (test), `3ee70a3` (feat)
2. **Task 2: Strip inline writeback lists** - `75d9ab3` (test), `4d4111c` (feat)
3. **Task 3: Wire prune events + remove-row** - `d35d57a` (feat)

## Files Created/Modified

- `frontend/src/components/playlists/RebuildBanner.tsx` - View details + modal; inline error removed
- `frontend/src/components/playlists/RebuildBanner.test.tsx` - Trigger visibility and modal behavior
- `frontend/src/components/playlists/WritebackStatus.tsx` - Detail lists removed
- `frontend/src/components/playlists/WritebackStatus.test.tsx` - List absence and compact assertions
- `frontend/src/pages/PlaylistDetailPage.tsx` - Prune events and remove-row handler
- `frontend/src/pages/PlaylistDetailPage.test.tsx` - Updated expectations for on-demand diagnostics

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- `npm test -- --run RebuildBanner.test.tsx WritebackStatus.test.tsx PlaylistDetailPage.test.tsx` — 18 passed
- `npx tsc --noEmit` — passed

## Self-Check: PASSED

- FOUND: frontend/src/components/playlists/RebuildBanner.test.tsx
- FOUND: frontend/src/components/playlists/WritebackStatus.test.tsx
- FOUND: frontend/src/components/playlists/RebuildBanner.tsx
- FOUND: frontend/src/components/playlists/WritebackStatus.tsx
- FOUND: frontend/src/pages/PlaylistDetailPage.tsx
- FOUND: commits 5b2518c, 3ee70a3, 75d9ab3, 4d4111c, d35d57a
