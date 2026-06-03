---
phase: 11-sync-rebuild-diagnostics
plan: 02
subsystem: api
tags: [diagnostics, rebuild, pydantic, structlog, tdd]

requires:
  - phase: 11-sync-rebuild-diagnostics
    plan: 01
    provides: Pydantic diagnostics models and RED test scaffold
provides:
  - REASON_CATALOG with operator-facing copy and action templates
  - DiagnosticsContext and pure build_rebuild_diagnostics resolver
  - GREEN unit tests for fetch/writeback/rebuild_error normalization
affects: [11-03, 11-04, 11-05]

tech-stack:
  added: []
  patterns:
    - "Central reason catalog keeps copy out of routes and SPA (D-17)"
    - "Writeback reasons normalized via substring heuristics before catalog lookup (D-18)"
    - "Episode titles merged from run.snapshot_json plus ctx maps (Pitfall 2)"

key-files:
  created:
    - backend/src/wheeloffish/core/rebuild_diagnostics.py
  modified:
    - backend/tests/unit/test_rebuild_diagnostics.py

key-decisions:
  - "rebuild_failed reason_text uses run.error_message for modal detail (D-07)"
  - "Info writeback notices without episode_id are excluded from episode_issues"
  - "open_provider actions only emitted when DiagnosticsContext.provider_open_url is set (T-11-02)"

patterns-established:
  - "DiagnosticAction built from catalog templates with series/episode/url filled from warning + ctx"
  - "Unknown writeback strings fall back to writeback_warning without raising"

requirements-completed: [DIAG-02, DIAG-03, DIAG-04]

duration: 12min
completed: 2026-06-02
---

# Phase 11 Plan 02: Rebuild diagnostics resolver Summary

**Pure backend resolver normalizes fetch/writeback warnings and failed rebuild errors into catalog-backed diagnostic rows with labels, hints, and actions**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-02T12:00:00Z
- **Completed:** 2026-06-02T12:12:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `wheeloffish/core/rebuild_diagnostics.py` with `REASON_CATALOG`, frozen `DiagnosticsContext`, and `build_rebuild_diagnostics`.
- Normalized heterogeneous writeback `reason` strings (404/not found → `episode_not_found`; unknown → `writeback_warning`).
- Extended unit tests to 12 cases covering catalog copy, actions, label fallbacks, info-notice exclusion, and snapshot title merge.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend RED tests to full resolver behavior coverage** - `93b459c` (test)
2. **Task 2: Implement reason catalog + build_rebuild_diagnostics** - `4f81948` (feat)

**Prior RED gate (Plan 01):** `12d31af` (test)

**Plan metadata:** pending docs commit

## TDD Gate Compliance

- RED: `12d31af` (Plan 01 scaffold) + `93b459c` (extended behavior matrix)
- GREEN: `4f81948` (resolver implementation)
- REFACTOR: none

## Files Created/Modified

- `backend/src/wheeloffish/core/rebuild_diagnostics.py` - Reason catalog, context dataclass, pure resolver
- `backend/tests/unit/test_rebuild_diagnostics.py` - Full GREEN behavior matrix (12 tests)

## Decisions Made

- `rebuild_failed` rows surface `run.error_message` as `reason_text` for operator modal detail.
- Episode labels merge `ctx.episode_title_map` with titles from `run.snapshot_json` entries.
- `open_provider` URL is taken only from `ctx.provider_open_url`, never from warning text.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Plan 03 can wire `build_rebuild_diagnostics` into `_playlist_to_detail` for `last_rebuild` only (D-24).
- Frontend plans 04–05 can consume resolved `diagnostics` rows and `actions[]`.

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/rebuild_diagnostics.py
- FOUND: backend/tests/unit/test_rebuild_diagnostics.py
- FOUND: 93b459c
- FOUND: 4f81948
- FOUND: 12d31af

---
*Phase: 11-sync-rebuild-diagnostics*
*Completed: 2026-06-02*
