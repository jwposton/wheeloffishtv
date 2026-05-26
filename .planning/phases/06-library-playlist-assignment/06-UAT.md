---
status: complete
phase: 06-library-playlist-assignment
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md, 06-05-SUMMARY.md, 06-06-SUMMARY.md, 06-07-SUMMARY.md, supplemental-2026-05-26]
started: 2026-05-26T00:00:00Z
updated: 2026-05-26T21:12:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Long-press opens menu on mobile
expected: Long-press on a Library tile shows the same add-to-playlist menu as the ⋯ button
result: pass
reported: "Advanced… now visible in add-to-playlist menus (06-07 gap closure)"

### 2. Two-pane side-by-side at md+
expected: Playlist edit shows In | Available columns at ≥768px; tabs on smaller screens
result: pass
reported: "Layout pass; In-pane posters load from API thumb_url on edit (06-07)"

### 3. Metadata displays after sync
expected: After catalog sync, series detail shows summary, genres, content rating from provider_metadata
result: pass

### 4. Quick-add from Library
expected: Context menu or ⋯ → select playlist → row appended without opening full form
result: pass
reported: "Pass; sticky Save/Cancel footer added (06-07)"

### 5. Two-pane edit flow
expected: Add/remove series in two-pane picker; row settings via In-pane context menu
result: pass
reported: "Remove and row settings work via context menu; URL encoding fix (06-06) + row menu UX (06-07)"

### 6. Duplicate add feedback on Library poster
expected: Adding a show to a playlist it is already on shows a neutral on-poster message, not a corner error toast
result: pass

### 7. Library menus omit Advanced link
expected: Library ⋮ and context menus show playlist names and Create new only — no Advanced… item (Advanced remains on series detail Add to playlist menu)
result: pass

### 8. Series detail In playlists list
expected: Series detail page lists playlist names the show is on (links to each playlist); shows empty state when not in any
result: pass

### 9. Playlist detail two-column layout
expected: Playlist detail shows Shows column on the left (poster grid with row menus) and Output episode list on the right at desktop widths
result: pass

### 10. Edit playlist compact settings
expected: On a wide screen, playlist edit form shows settings in a compact horizontal layout (single card, fields side-by-side) above the two-pane picker
result: pass
reported: "Pass; could be even more compact if slot count and policy shared one row. Episode count input keeps leading zeros (030, 01) while editing — logged as gap."

### 11. Remove confirm dialog on edit
expected: On playlist edit, Remove from playlist opens a readable confirm dialog that stays open; confirming removes the show from the In playlist pane
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Episode count field accepts numeric input without spurious leading zeros while editing"
  status: resolved
  reason: "User reported during Test 10: when you edit a number it forces a leading 0 so you get 030 01 010"
  severity: minor
  test: 10
  root_cause: "Controlled type=number input coerced via Number() on each keystroke, preserving intermediate leading-zero strings in the field"
  artifacts:
    - path: frontend/src/components/playlists/PlaylistForm.tsx
      issue: "episodeCount number state with type=number input"
  missing:
    - "Use string-backed numeric input; normalize on blur before submit"
  debug_session: ""

[resolved gaps from prior session — see git history 06-UAT.md 2026-05-26]
