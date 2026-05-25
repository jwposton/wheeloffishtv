---
phase: "05-orchestration-scheduling"
plan: "06"
subsystem: "frontend"
tags: [spa, playlist-ui, crud, rebuild, catalog-picker]
dependency_graph:
  requires:
    - "05-04 (playlist CRUD API)"
    - "05-05 (playlist list page + StatusBadge)"
  provides:
    - "PlaylistDetailPage (/playlists/:id)"
    - "PlaylistFormPage (/playlists/new + /playlists/:id/edit)"
    - "SeriesPicker catalog search multi-select"
    - "RebuildBanner status + error display"
    - "OutputList snapshot episode list"
  affects:
    - "frontend/src/App.tsx (routes)"
    - "frontend/src/api/playlists.ts (full CRUD)"
tech_stack:
  added: []
  patterns:
    - "TanStack Query useMutation for CRUD + rebuild"
    - "refetchInterval polling for running/queued rebuild status"
    - "Base UI AlertDialog for delete confirmation"
    - "Debounced catalog search in SeriesPicker (300ms)"
key_files:
  created:
    - frontend/src/components/playlists/SeriesPicker.tsx
    - frontend/src/components/playlists/PlaylistForm.tsx
    - frontend/src/components/playlists/RebuildBanner.tsx
    - frontend/src/components/playlists/OutputList.tsx
    - frontend/src/pages/PlaylistFormPage.tsx
    - frontend/src/pages/PlaylistDetailPage.tsx
    - frontend/src/pages/PlaylistDetailPage.test.tsx
  modified:
    - frontend/src/api/playlists.ts
    - frontend/src/App.tsx
decisions:
  - "AlertDialog delete copy: 'This removes the playlist and its rebuild history. This cannot be undone.' (UI-SPEC exact copy)"
  - "Edit link uses Button render={<Link>} — same pattern as PlaylistsPage (pre-existing nativeButton warning acceptable)"
  - "SeriesPicker uses connection-scoped /connections/:id/series API with 20-item limit"
  - "RebuildBanner error_message rendered as plain text only (T-05-06-03 XSS mitigation)"
metrics:
  duration: "~5 minutes"
  completed: "2026-05-25"
  tasks: 4
  files: 9
---

# Phase 5 Plan 06: Playlist SPA Vertical Slice Summary

**One-liner:** Full playlist lifecycle UI — create/edit form with catalog series picker, detail page with output list, rebuild now with polling, and delete confirmation.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | API mutations and detail hook | 16a93ef | frontend/src/api/playlists.ts |
| 2 | SeriesPicker component | 28bbcbf | frontend/src/components/playlists/SeriesPicker.tsx |
| 3 | PlaylistForm create/edit | 6469d8d | PlaylistForm.tsx, PlaylistFormPage.tsx, App.tsx |
| 4 | Detail page output + rebuild + delete | 9401fb0 | PlaylistDetailPage.tsx, RebuildBanner.tsx, OutputList.tsx, test |

## What Was Built

### Task 1 — API layer

Extended `frontend/src/api/playlists.ts` with:
- **Types:** `PlaylistDetailResponse`, `SnapshotEpisode`, `PlaylistSeriesRowResponse`, `RebuildRunSummary`, `PlaylistCreatePayload`, `PlaylistUpdatePayload`, `SlotAllocation`, `RowMode`, `CompletionPolicy`
- **Functions:** `fetchPlaylist`, `createPlaylist`, `updatePlaylist`, `deletePlaylist`, `triggerRebuild`
- **Hooks:** `usePlaylist(id)` with `refetchInterval: 5000` when status is `running`/`queued`; `useCreatePlaylist`, `useUpdatePlaylist`, `useDeletePlaylist`, `useRebuildPlaylist` mutations all invalidating `['playlists']`
- **Labels map:** `SLOT_ALLOCATION_LABELS` (wild→Wild, balanced→Balanced, round_robin→Round-robin) per D-26

### Task 2 — SeriesPicker

`SeriesPicker` component with:
- Debounced search (300ms) against `/connections/:id/series?q=` (catalog browse reuse, D-25)
- Results as clickable list with poster thumb + title; duplicate prevention via `selectedIds` set
- Selected rows as removable cards with per-row ordered/random toggle + completion policy override select
- No free-text series ID entry

### Task 3 — PlaylistForm + routes

`PlaylistForm` with three sections per UI-SPEC:
- **Basics:** name, episode_count (default 20), slot_allocation Select (Wild/Balanced/Round-robin), default_completion_policy Select
- **Schedule:** daily/weekly radio; weekly shows day-of-week select (Mon–Sun)
- **Series:** SeriesPicker integrated with per-row overrides

Validation: name required, episode_count ≥ 1, weekly requires DOW, at least one series row.

`PlaylistFormPage` reads `:id` — "new" → create mode, else → edit mode with `usePlaylist` load.

`App.tsx` routes added: `/playlists/new`, `/playlists/:id/edit`, `/playlists/:id` (ordered so `/new` is never captured by `/:id`).

### Task 4 — PlaylistDetailPage + tests

`PlaylistDetailPage`:
- Header: playlist name, Edit link, "Rebuild now" button (disabled while running/queued), Delete button
- **Delete confirmation:** Base UI `AlertDialog` with exact UI-SPEC copy — "This removes the playlist and its rebuild history. This cannot be undone."
- `RebuildBanner`: `StatusBadge` + relative timestamp; plain text `error_message` for failed; partial warning text from UI-SPEC
- `OutputList`: numbered `slot_index + 1` list with episode title and series title
- Empty output message when no snapshot

Test file `PlaylistDetailPage.test.tsx` — 5 passing assertions:
1. "Rebuild now" button present
2. Output list renders episode titles
3. Playlist name in heading
4. Delete button present
5. Loading skeletons when `isLoading: true`

## Threat Model Compliance

| Threat | Mitigation Applied |
|--------|--------------------|
| T-05-06-01 Rebuild tampering | Rebuild button only in owned detail page; API enforces D-22 (409 when rebuild_in_progress) |
| T-05-06-02 Delete tampering | AlertDialog with destructive copy — user must explicitly confirm |
| T-05-06-03 XSS via error_message | `error_message` rendered as JSX text node (plain text only, no `dangerouslySetInnerHTML`) |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

- Base UI `nativeButton` warning appears in tests when `Button` wraps a `Link` (`render={<Link>}`). This is the same pattern used in `PlaylistsPage.tsx` and `PlaylistCard.tsx` — a pre-existing project convention that works correctly at runtime.

## Known Stubs

None. All components are wired to live API hooks.

## Self-Check

### Created files exist
- ✓ frontend/src/components/playlists/SeriesPicker.tsx
- ✓ frontend/src/components/playlists/PlaylistForm.tsx
- ✓ frontend/src/components/playlists/RebuildBanner.tsx
- ✓ frontend/src/components/playlists/OutputList.tsx
- ✓ frontend/src/pages/PlaylistFormPage.tsx
- ✓ frontend/src/pages/PlaylistDetailPage.tsx
- ✓ frontend/src/pages/PlaylistDetailPage.test.tsx

### Commits exist
- ✓ 16a93ef — API mutations
- ✓ 28bbcbf — SeriesPicker
- ✓ 6469d8d — PlaylistForm + routes
- ✓ 9401fb0 — Detail page + tests

## Self-Check: PASSED
