---
status: diagnosed
phase: 06-library-playlist-assignment
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md, 06-05-SUMMARY.md]
started: 2026-05-26T00:00:00Z
updated: 2026-05-26T12:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Long-press opens menu on mobile
expected: Long-press on a Library tile shows the same add-to-playlist menu as the ⋯ button
result: issue
reported: "Don't see Advanced on long-press menu nor the ellipses in the browser — add and create new but no Advanced"
severity: major

### 2. Two-pane side-by-side at md+
expected: Playlist edit shows In | Available columns at ≥768px; tabs on smaller screens
result: pass
reported: "Layout pass; existing shows on playlist don't reliably load posters — lots of missing images in In playlist pane"
note: layout verified; poster gap logged separately

### 3. Metadata displays after sync
expected: After catalog sync, series detail shows summary, genres, content rating from provider_metadata
result: pass

### 4. Quick-add from Library
expected: Context menu or ⋯ → select playlist → row appended without opening full form
result: pass
reported: "Pass; on playlist edit screen save/cancel should float at bottom or top — floating always visible is best"
note: quick-add verified; sticky actions gap logged separately

### 5. Two-pane edit flow
expected: Add/remove series in two-pane picker; row settings sheet opens from In pane
result: issue
reported: "Remove doesn't work. Instead of a sheet, want click/long-press context menu for playback, completion, remove — like add from Library"
severity: major

## Summary

total: 5
passed: 3
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Add-to-playlist menu (⋯ and long-press) shows playlist list, Create new, and Advanced… link per Phase 6 spec"
  status: failed
  reason: "User reported: Don't see Advanced on long-press menu nor the ellipses in the browser — add and create new but no Advanced"
  severity: major
  test: 1
  root_cause: "Advanced… link lives only inside QuickCreatePlaylistDialog; AddToPlaylistMenu and AddToPlaylistContextMenuItems expose playlist names + Create new but no top-level Advanced menu item"
  artifacts:
    - path: frontend/src/components/playlists/AddToPlaylistMenu.tsx
      issue: "No Advanced… ContextMenuItem/DropdownMenuItem linking to /playlists/new?seriesId="
    - path: frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx
      issue: "Advanced link hidden until user opens Create new dialog"
  missing:
    - "Add Advanced… menu item to both dropdown and context menu variants (after Create new separator)"
  debug_session: .planning/debug/06-advanced-menu-missing.md

- truth: "In playlist pane shows poster art for each row member"
  status: failed
  reason: "User reported during Test 2: existing shows on playlist don't reliably load posters — lots of missing images"
  severity: major
  test: 2
  root_cause: "PlaylistForm initializes row thumb_url to null; TwoPanePicker displayRows only enriches from paginated catalog infinite query — rows not in loaded catalog pages keep null thumb_url"
  artifacts:
    - path: frontend/src/components/playlists/PlaylistForm.tsx
      issue: "thumb_url: null on edit load (line 68)"
    - path: frontend/src/components/playlists/TwoPanePicker.tsx
      issue: "catalogById built from infinite query pages only, not keyed lookup for all row IDs"
  missing:
    - "Persist or fetch thumb_url for playlist row members (API field or batch catalog lookup by series_id)"
  debug_session: .planning/debug/06-in-pane-missing-posters.md

- truth: "Playlist edit Save/Cancel actions remain visible while scrolling the two-pane picker"
  status: failed
  reason: "User reported during Test 4: save/cancel should float at bottom or top — floating always visible is best"
  severity: minor
  test: 4
  root_cause: "Save/Cancel buttons render inline at bottom of PlaylistForm; long two-pane content scrolls them off-screen"
  artifacts:
    - path: frontend/src/components/playlists/PlaylistForm.tsx
      issue: "Submit actions not sticky/fixed"
  missing:
    - "Sticky or fixed footer bar for Save/Cancel on playlist edit/create form"
  debug_session: .planning/debug/06-sticky-form-actions.md

- truth: "Remove from playlist works in edit mode via row settings"
  status: failed
  reason: "User reported during Test 5: remove doesn't work"
  severity: major
  test: 5
  root_cause: "removePlaylistRow and patchPlaylistRow interpolate seriesId into URL path without encodeURIComponent; Plex composite IDs break DELETE/PATCH routing (same as CR-01 in 06-REVIEW.md)"
  artifacts:
    - path: frontend/src/api/playlists.ts
      issue: "DELETE/PATCH /rows/${seriesId} unencoded"
    - path: frontend/src/lib/seriesId.ts
      issue: "seriesApiPath encodes IDs but row ops don't use it"
  missing:
    - "encodeURIComponent(seriesId) in removePlaylistRow and patchPlaylistRow URLs"
  debug_session: .planning/debug/06-row-remove-url-encoding.md

- truth: "In-pane row settings accessible via ⋯ or long-press context menu (playback, completion, remove)"
  status: failed
  reason: "User reported during Test 5: want context menu like Library add flow instead of bottom sheet"
  severity: major
  test: 5
  root_cause: "Phase 6 implemented RowSettingsSheet opened on tile click; user expects Library-style ContextMenu with inline row actions"
  artifacts:
    - path: frontend/src/components/playlists/TwoPanePicker.tsx
      issue: "MemberTile click opens RowSettingsSheet only"
    - path: frontend/src/components/playlists/RowSettingsSheet.tsx
      issue: "Bottom sheet pattern; remove buried in confirm dialog"
  missing:
    - "Replace or supplement sheet with ContextMenu on In-pane tiles (ordered/random, completion policy, remove)"
    - "Visible ⋯ affordance on In-pane tiles matching Library SeriesCard pattern"
  debug_session: .planning/debug/06-row-context-menu-ux.md
