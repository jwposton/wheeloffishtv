---
phase: 06-library-playlist-assignment
plan: 03
subsystem: ui
tags: [react, context-menu, dropdown-menu, playlists, library, tdd]

# Dependency graph
requires:
  - phase: 06-library-playlist-assignment
    plan: 02
    provides: POST /playlists/{id}/rows append API and owner-scoped 404
provides:
  - appendPlaylistRow / useAppendPlaylistRow / createPlaylistWithSeries frontend hooks
  - Shared AddToPlaylistMenu dropdown + AddToPlaylistContextMenuItems for tiles
  - QuickCreatePlaylistDialog with Advanced link to /playlists/new?seriesId=
  - Library nav rename (Browse → Library) with tile ⋯ and context menu on SeriesCard
affects:
  - 06-04 Two-pane playlist editor (reuses AddToPlaylistMenu patterns)
  - 06-05 Series detail Add to playlist button

# Tech tracking
tech-stack:
  added:
    - "@base-ui/react/context-menu (via shadcn context-menu primitive)"
    - "@base-ui/react/dialog (via shadcn dialog primitive)"
  patterns:
    - "DropdownMenuTrigger render prop merges trigger element without nested buttons"
    - "Shared useAddToPlaylistHandlers hook powers dropdown and context menu item sets"
    - "Tile menu actions stopPropagation to preserve tile navigation (D-06)"

key-files:
  created:
    - frontend/src/components/playlists/AddToPlaylistMenu.tsx
    - frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx
    - frontend/src/components/ui/context-menu.tsx
    - frontend/src/components/ui/dialog.tsx
    - frontend/src/components/playlists/AddToPlaylistMenu.test.tsx
    - frontend/src/components/browse/SeriesCard.test.tsx
  modified:
    - frontend/src/api/playlists.ts
    - frontend/src/components/browse/SeriesCard.tsx
    - frontend/src/pages/BrowsePage.tsx
    - frontend/src/components/layout/AppShell.tsx

key-decisions:
  - "DropdownMenuTrigger uses render prop for custom ⋯ button — avoids invalid nested buttons"
  - "Quick create calls createPlaylistWithSeries directly; toast copy matches UI-SPEC Added to {name}"
  - "Route stays /browse; only nav label and page heading read Library (D-03)"

patterns-established:
  - "AddToPlaylistMenu + AddToPlaylistContextMenuItems share handler hook for D-19 reuse"

requirements-completed: [PLT-03, WEB-01]

# Metrics
duration: 12min
completed: 2026-05-25
---

# Phase 6 Plan 03: Library Tile Add-to-Playlist Summary

**Library nav rename with visible tile ⋯ menu, shared AddToPlaylistMenu (dropdown + context menu), quick-create dialog, and frontend hooks wired to row append API.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-25T23:40:00Z
- **Completed:** 2026-05-25T23:52:00Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Frontend `appendPlaylistRow`, `useAppendPlaylistRow`, and `createPlaylistWithSeries` hooks with query invalidation
- Shared `AddToPlaylistMenu` listing user playlists + quick-create; `AddToPlaylistContextMenuItems` for right-click/long-press
- `QuickCreatePlaylistDialog` with trimmed name validation, Create and add, and Advanced… link
- Browse → Library rename; SeriesCard grid/list tiles with MoreVertical ⋯, ContextMenu, and propagation guards

## Task Commits

Each task was committed atomically:

1. **Task 1: Frontend API hooks for row append + quick create** - `66cbaaa` (feat)
2. **Task 2: AddToPlaylistMenu + QuickCreatePlaylistDialog** - `ac42309` (test), `1ab8f55` (feat)
3. **Task 3: Library nav rename + SeriesCard ⋯ integration** - `e84b454` (test), `fcfc984` (feat)

## Files Created/Modified

- `frontend/src/api/playlists.ts` - append and quick-create API helpers + mutation hook
- `frontend/src/components/playlists/AddToPlaylistMenu.tsx` - shared dropdown/context menu items
- `frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx` - inline name + Advanced link
- `frontend/src/components/ui/context-menu.tsx` - base-ui context menu primitive
- `frontend/src/components/ui/dialog.tsx` - base-ui dialog primitive
- `frontend/src/components/browse/SeriesCard.tsx` - ⋯ button, context menu, stopPropagation
- `frontend/src/pages/BrowsePage.tsx` - page heading Library
- `frontend/src/components/layout/AppShell.tsx` - nav label Library

## Decisions Made

- DropdownMenuTrigger `render` prop for ⋯ button — base-ui wraps children in a button by default
- Path remains `/browse`; only labels change per planning discretion
- Empty playlist name rejected client-side via trim before submit (T-06-03-01)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] shadcn wrote UI files to wrong `@/` directory**
- **Found during:** Task 2
- **Issue:** `npx shadcn add` created `frontend/@/components/ui/` instead of `frontend/src/components/ui/`
- **Fix:** Copied context-menu.tsx and dialog.tsx to correct path; removed erroneous `@/` tree
- **Files modified:** frontend/src/components/ui/context-menu.tsx, frontend/src/components/ui/dialog.tsx
- **Committed in:** `1ab8f55`

**2. [Rule 3 - Blocking] @testing-library/user-event not installed**
- **Found during:** Task 2 test authoring
- **Issue:** Test import failed — user-event absent from devDependencies
- **Fix:** Used fireEvent from @testing-library/react (already installed)
- **Files modified:** frontend/src/components/playlists/AddToPlaylistMenu.test.tsx
- **Committed in:** `ac42309`, `1ab8f55`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Infrastructure fixes only; no scope change.

## TDD Gate Compliance

- Task 2: RED `ac42309` → GREEN `1ab8f55` ✓
- Task 3: RED `e84b454` → GREEN `fcfc984` ✓

## Issues Encountered

None beyond deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 3 complete — Library tiles can add shows to existing playlists or quick-create
- Ready for 06-04 two-pane tile picker (will reuse AddToPlaylistMenu patterns on detail in 06-05)

## Self-Check: PASSED

- FOUND: frontend/src/components/playlists/AddToPlaylistMenu.tsx
- FOUND: frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx
- FOUND: frontend/src/components/browse/SeriesCard.tsx
- FOUND: .planning/phases/06-library-playlist-assignment/06-03-SUMMARY.md
- FOUND: 66cbaaa, ac42309, 1ab8f55, e84b454, fcfc984

---
*Phase: 06-library-playlist-assignment*
*Completed: 2026-05-25*
