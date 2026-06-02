---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
status: passed
verified: 2026-06-02
score: 12/12
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

Completed via `09-HUMAN-UAT.md` (2026-06-02): 5/6 pass, 1 skipped (expired auth — deferred; API guardrails automated in test 6 of `09-UAT.md`).

## Post-review fixes (2026-06-02)

- CR-01: Episodes query enabled whenever auth is ready (not only when resume needs title)
- WR-01: Roll back optimistic episode cache on non-succeeded mutation envelopes
- WR-02: Reject protocol-relative `from` back URLs
