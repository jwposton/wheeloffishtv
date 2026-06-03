---
phase: 11-sync-rebuild-diagnostics
plan: 06
gap_closure: true
subsystem: api
tags: [diagnostics, rebuild, writeback, pytest]

provides:
  - Resolver completeness for failed/empty error_message, writeback-only failure, unknown fetch codes
key-files:
  modified:
    - backend/src/wheeloffish/core/rebuild_diagnostics.py
    - backend/tests/unit/test_rebuild_diagnostics.py

requirements-completed: [DIAG-02]

duration: 12min
completed: 2026-06-03
---

# Phase 11 Plan 06: Resolver Gap Closure Summary

Closed WR-01, WR-02, WR-03 from verification: failed rebuilds always emit `rebuild_error`; whole-playlist writeback failures get a synthetic `episode_issues` row; unknown fetch reasons use `fetch_failure` catalog copy.

**Tests:** 16 unit tests in `test_rebuild_diagnostics.py` (3 new).
