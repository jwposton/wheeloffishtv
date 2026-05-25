---
phase: 06-library-playlist-assignment
plan: 04
subsystem: ui
tags: [react, two-pane, playlist-editor, shadcn, tanstack-query]

# Dependency graph
requires:
  - phase: 06-library-playlist-assignment
    provides: Row append/remove/patch API (06-02), Library add-to-playlist patterns (06-03)
provides:
  - TwoPanePicker tile editor (In playlist | Available to add)
  - RowSettingsSheet bottom sheet for per-row mode/policy/remove
  - PlaylistForm integration with ?seriesId= pre-select on create
  - removePlaylistRow/patchPlaylistRow API hooks
affects:
  - 06-05 series detail enrichment

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optimistic row add/remove/patch with revert + toast on API failure (T-06-04-01)"
    - "Mobile Tabs / md+ side-by-side grid for two-pane layout (D-17)"
    - "Catalog infinite scroll via useSeriesInfiniteQuery + intersection observer"

key-files:
  created:
    - frontend/src/components/playlists/TwoPanePicker.tsx
    - frontend/src/components/playlists/TwoPanePicker.test.tsx
    - frontend/src/components/playlists/RowSettingsSheet.tsx
    - frontend/src/components/playlists/RowSettingsSheet.test.tsx
    - frontend/src/components/ui/tabs.tsx
  modified:
    - frontend/src/components/playlists/PlaylistForm.tsx
    - frontend/src/pages/PlaylistFormPage.tsx
    - frontend/src/api/playlists.ts

key-decisions:
  - "SeriesRow type exported from TwoPanePicker; RowSettingsSheet imports shared shape"
  - "Edit mode uses incremental row API when playlistId set; create mode stays local until save"
  - "Form page max-width widened to max-w-6xl for two-column picker layout"
  - "Added shadcn-style Tabs via @base-ui/react/tabs for mobile pane switching"

patterns-established:
  - "Available pane dims already-selected tiles; In pane opens RowSettingsSheet on tile click"

requirements-completed: [PLT-03, WEB-01]

# Metrics
duration: 2min
completed: 2026-05-25
---

# Phase 6 Plan 04: Two-Pane Tile Picker Summary

**Two-pane playlist editor with In/Available tile grids, bottom-sheet row settings, responsive mobile tabs, and optimistic row API mutations replacing SeriesPicker.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-25T23:43:17Z
- **Completed:** 2026-05-25T23:44:59Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- RowSettingsSheet: ordered/random toggle, completion policy select, remove with confirm dialog
- TwoPanePicker: debounced catalog search, infinite scroll, member/available tile grids, md+ columns + mobile tabs
- PlaylistForm wired to TwoPanePicker; SeriesPicker removed; Advanced create path pre-selects via `?seriesId=`

## Task Commits

Each task was committed atomically:

1. **Task 1: RowSettingsSheet component (D-16)** - `0eaf94d` (feat)
2. **Task 2: TwoPanePicker component (D-13–D-17)** - `5ded58a` (feat)
3. **Task 3: Integrate into PlaylistForm; remove SeriesPicker** - `3ce48b6` (feat)

## Files Created/Modified

- `frontend/src/components/playlists/RowSettingsSheet.tsx` - Bottom sheet row settings per D-16
- `frontend/src/components/playlists/RowSettingsSheet.test.tsx` - Sheet controls and onSave tests
- `frontend/src/components/playlists/TwoPanePicker.tsx` - Two-pane tile picker with API wiring
- `frontend/src/components/playlists/TwoPanePicker.test.tsx` - Layout/tab responsive tests
- `frontend/src/components/ui/tabs.tsx` - shadcn-style Tabs for mobile pane switch
- `frontend/src/api/playlists.ts` - removePlaylistRow, patchPlaylistRow, mutation hooks
- `frontend/src/components/playlists/PlaylistForm.tsx` - TwoPanePicker in Shows section
- `frontend/src/pages/PlaylistFormPage.tsx` - seriesId query param pre-select on create

## Decisions Made

- Optimistic UI for append/remove/patch with rollback on failure (T-06-04-01 mitigation)
- Create flow keeps row changes local; edit flow uses 06-02 row endpoints incrementally
- Deleted SeriesPicker entirely (D-21); no remaining frontend imports

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Two-pane editor ready for operator UAT on `/playlists/new` and `/playlists/:id/edit`
- Plan 06-05 can focus on series detail hero/metadata without picker blockers

## Self-Check: PASSED

- FOUND: frontend/src/components/playlists/TwoPanePicker.tsx
- FOUND: frontend/src/components/playlists/RowSettingsSheet.tsx
- FOUND: frontend/src/components/playlists/TwoPanePicker.test.tsx
- FOUND: frontend/src/components/playlists/RowSettingsSheet.test.tsx
- FOUND: 0eaf94d
- FOUND: 5ded58a
- FOUND: 3ce48b6
- SeriesPicker.tsx deleted; build and 5 unit tests pass

---
*Phase: 06-library-playlist-assignment*
*Completed: 2026-05-25*
