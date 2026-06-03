---
phase: 11-sync-rebuild-diagnostics
plan: 07
gap_closure: true
subsystem: api,ui
tags: [orchestrator, underfill, diagnostics, rebuild]

provides:
  - Underfill rebuilds marked partial with slot_unfilled fetch_warnings
  - View details trigger when slots_filled < slots_requested
key-files:
  modified:
    - backend/src/wheeloffish/core/orchestrator.py
    - backend/src/wheeloffish/core/rebuild_diagnostics.py
    - backend/tests/unit/test_orchestrator.py
    - backend/tests/unit/test_rebuild_diagnostics.py
    - frontend/src/lib/rebuildDiagnostics.ts
    - frontend/src/lib/rebuildDiagnostics.test.ts

requirements-completed: [DIAG-01, DIAG-02]

duration: 20min
completed: 2026-06-03
---

# Phase 11 Plan 07: Underfill Diagnostics Summary

Closed UAT Test 1: orchestrator compares `allocate_slots` assignments to filled slot indices, appends `slot_unfilled` warnings, and sets `partial` when underfilled. Frontend `shouldShowDiagnostics` also gates on slot counts and existing diagnostic rows.

**Note:** Playlists with an old succeeded 19/20 run show View details immediately; Shows skipped rows appear after one new rebuild.

**Tests:** `test_underfill_marks_partial_and_slot_unfilled_warning`, `test_slot_unfilled_maps_to_show_issue`, 3 new frontend trigger tests.
