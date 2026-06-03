---
phase: 11-sync-rebuild-diagnostics
plan: 08
gap_closure: true
subsystem: ui
tags: [react, rebuild, navigation]

provides:
  - Clean RebuildBanner DOM (no empty placeholders)
  - SPA navigate for open_series from diagnostics modal on playlist detail
key-files:
  modified:
    - frontend/src/components/playlists/RebuildBanner.tsx
    - frontend/src/components/playlists/RebuildBanner.test.tsx
    - frontend/src/pages/PlaylistDetailPage.tsx

requirements-completed: [DIAG-04, DIAG-05]

duration: 8min
completed: 2026-06-03
---

# Phase 11 Plan 08: Operator Surface Polish Summary

Closed IN-01 and IN-02: removed empty banner `<p>` placeholders; `PlaylistDetailPage` passes `navigate` into `RebuildBanner` for client-side series links from the modal.

**Tests:** 7 `RebuildBanner` tests (2 new).
