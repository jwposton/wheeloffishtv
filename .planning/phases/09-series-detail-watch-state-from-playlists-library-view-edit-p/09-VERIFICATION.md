---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
status: human_needed
verified: 2026-06-02
score: 11/12
---

# Phase 9 Verification

## Must-haves

| Truth | Status |
|-------|--------|
| Shared series detail from Library / view-playlist / edit-playlist | verified |
| Grouped seasons, S0 last | verified |
| Watch affordances and provider-backed mutations | verified |
| View series + session-new prioritization in playlist edit | verified |
| Save/Cancel staging for membership edits (09-08) | verified |
| Auth/ownership guardrails on watch API | verified (automated) |

## Automated checks

- `uv run pytest tests/api/test_catalog_watch_mutations.py` — 12 passed
- `npm test -- SeriesDetailPage.watch-state PlaylistRowMenuItems.view-series TwoPanePicker PlaylistDetailPage` — passed

## Human verification

### 09-04 Task 3 — Provider bulk semantics (blocking for full sign-off)

Operator should confirm on a live Plex/Jellyfin stack:

1. Season bulk watch/unwatch on Plex (T-09-01)
2. Season and series bulk on Jellyfin (T-09-03, T-09-04)
3. Expired provider auth shows actionable errors

Reply **approved** when complete, or report failing step.

## Post-review fixes (2026-06-02)

- CR-01: Episodes query enabled whenever auth is ready (not only when resume needs title)
- WR-01: Roll back optimistic episode cache on non-succeeded mutation envelopes
- WR-02: Reject protocol-relative `from` back URLs
