---
status: partial
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
source: [09-VERIFICATION.md]
started: 2026-06-02T17:06:00Z
updated: 2026-06-02T17:06:00Z
---

## Current Test

Provider bulk watch semantics on live Plex/Jellyfin (Plan 09-04 Task 3)

## Tests

### 1. Open detail from Library, view-playlist, and edit-playlist View series
expected: Identical layout and back-affordance behavior across entry points
result: pending

### 2. Episode watched/unwatched on Plex and Jellyfin
expected: Badges update after refresh following single-episode mutations
result: pending

### 3. Plex season bulk watch/unwatch (T-09-01)
expected: All episodes in season update on provider
result: pending

### 4. Jellyfin season bulk (T-09-03)
expected: Descendant episodes update
result: pending

### 5. Jellyfin series bulk (T-09-04)
expected: Descendant episodes update
result: pending

### 6. Expired provider auth
expected: Actionable failure messaging, no false success
result: pending

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
