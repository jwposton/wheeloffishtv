---
status: complete
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
source: [09-VERIFICATION.md, 09-04-SUMMARY.md]
started: 2026-06-02T17:06:00Z
updated: 2026-06-02T22:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Open detail from Library, view-playlist, and edit-playlist View series
expected: Identical layout and back-affordance behavior across entry points
result: pass

### 2. Episode watched/unwatched on Plex and Jellyfin
expected: Badges update after refresh following single-episode mutations
result: pass

### 3. Plex season bulk watch/unwatch (T-09-01)
expected: All episodes in season update on provider
result: pass

### 4. Jellyfin season bulk (T-09-03)
expected: Descendant episodes update
result: pass

### 5. Jellyfin series bulk (T-09-04)
expected: Descendant episodes update
result: pass

### 6. Expired provider auth
expected: Actionable failure messaging, no false success
result: skipped
reason: Operator skip — live auth-break test deferred (covered by automated API guardrail tests)

## Summary

total: 6
passed: 5
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps
