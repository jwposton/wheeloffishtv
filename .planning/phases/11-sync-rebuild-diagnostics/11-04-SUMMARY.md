---
phase: 11-sync-rebuild-diagnostics
plan: 04
subsystem: ui
tags: [react, vitest, diagnostics, dialog, rebuild]

requires:
  - phase: 11-sync-rebuild-diagnostics
    provides: Diagnostics TypeScript types on RebuildRunSummary (Plan 01)
provides:
  - shouldShowDiagnostics + runDiagnosticAction helpers
  - RebuildDiagnosticsDialog scrollable modal with four sections
affects: [11-05]

tech-stack:
  added: []
  patterns:
    - "API-driven diagnostic rows rendered via React text nodes (T-11-03)"
    - "Action dispatch centralized in runDiagnosticAction with noopener provider opens (T-11-02)"

key-files:
  created:
    - frontend/src/lib/rebuildDiagnostics.ts
    - frontend/src/lib/rebuildDiagnostics.test.ts
    - frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx
    - frontend/src/components/playlists/RebuildDiagnosticsDialog.test.tsx
  modified: []

key-decisions:
  - "Prune history rows use client-side event_type label + open_series affordance per RESEARCH discretion"
  - "Empty-state detection includes null diagnostics with no prune events"

patterns-established:
  - "shouldShowDiagnostics gates on partial/failed rebuild OR writeback (D-02)"
  - "Modal sections hide when empty; empty state shows run timestamp (D-10, D-12)"

requirements-completed: [DIAG-01, DIAG-02, DIAG-03, DIAG-04]

duration: 12min
completed: 2026-06-03
---

# Phase 11 Plan 04: Diagnostics Modal Summary

**Scrollable rebuild diagnostics modal with tested trigger helpers and API-driven action dispatch**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-03T01:43:00Z
- **Completed:** 2026-06-03T01:55:26Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `shouldShowDiagnostics` matching D-02 (partial/failed rebuild or writeback) and `runDiagnosticAction` for `remove_row`, `open_series`, and `open_provider` with safe no-ops.
- Built `RebuildDiagnosticsDialog` with four ordered sections, empty state, unknown-label id fallback, and metadata-driven action buttons.
- Eighteen unit tests green; `tsc --noEmit` passes.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1: rebuildDiagnostics lib helpers + tests** - `7d8e1c5` (test), `1778f3f` (feat)
2. **Task 2: RebuildDiagnosticsDialog modal + tests** - `31c7254` (test), `88d1cfc` (feat)

**Plan metadata:** `d5e389c` (docs: complete plan)

## Files Created/Modified

- `frontend/src/lib/rebuildDiagnostics.ts` - Trigger visibility + action runner
- `frontend/src/lib/rebuildDiagnostics.test.ts` - D-02 matrix and dispatch coverage
- `frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx` - Scrollable diagnostics modal
- `frontend/src/components/playlists/RebuildDiagnosticsDialog.test.tsx` - Section, empty state, action, and fallback tests

## Decisions Made

- Prune history uses humanized `event_type` labels with `View series` open_series action (client-side mapping).
- `runDiagnosticAction` prefers injected `navigate` over `window.location.assign` for testability.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 05 can wire `shouldShowDiagnostics` + `RebuildDiagnosticsDialog` into `RebuildBanner` with the View details trigger.

---
*Phase: 11-sync-rebuild-diagnostics*
*Completed: 2026-06-03*

## Self-Check: PASSED

- FOUND: frontend/src/lib/rebuildDiagnostics.ts
- FOUND: frontend/src/lib/rebuildDiagnostics.test.ts
- FOUND: frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx
- FOUND: frontend/src/components/playlists/RebuildDiagnosticsDialog.test.tsx
- FOUND: 7d8e1c5
- FOUND: 1778f3f
- FOUND: 31c7254
- FOUND: 88d1cfc
