---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
plan: 02
subsystem: api
tags: [fastapi, watch-state, provider-integrations, pytest]
requires:
  - phase: 09-01
    provides: Provider watch-state mutation contract methods
provides:
  - Owner-scoped catalog watch-state mutation endpoint
  - Deterministic mutation result envelope for single and bulk targets
  - API route tests covering validation, auth, scope guard, and partial outcomes
affects: [library-ui, playlist-detail, watch-state-reconcile]
tech-stack:
  added: []
  patterns:
    - Normalized mutation response envelope with status and counts
    - Provider error mapping to client-actionable error_code values
key-files:
  created:
    - backend/tests/api/test_catalog_watch_mutations.py
  modified:
    - backend/src/wheeloffish/api/routes/catalog.py
    - backend/src/wheeloffish/api/schemas/catalog.py
    - backend/tests/api/test_catalog_watch_mutations.py
key-decisions:
  - "Support both target_id and target_ids in mutation payload so clients can use single or bulk calls with one contract."
  - "Return HTTP 200 with failed/partial envelope for provider/session failures to keep mutation handling reconciliation-friendly."
patterns-established:
  - "Watch mutation outcomes: status + updated_count + failed_count + failed_ids + error_code for all requests."
requirements-completed: [INT-01, INT-02, WEB-01]
duration: 4min
completed: 2026-05-28
---

# Phase 09 Plan 02: Catalog watch-state mutation routes Summary

**Catalog watch-state API now supports owner-scoped episode/season/series mutations with deterministic success/partial/failure envelopes for UI reconcile behavior.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-28T02:51:00Z
- **Completed:** 2026-05-28T02:54:29Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `/api/v1/connections/{connection_id}/watch-state` route with strict scope/action validation and connection ownership checks.
- Implemented provider/session/auth error normalization to `auth | forbidden | not_found | provider_error`.
- Added route contract tests that cover accepted payloads, validation failures, auth failures, cross-connection guardrails, and bulk partial outcomes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add watch-state mutation endpoint contracts and auth guards** - `ca5cddf` (feat)
2. **Task 2: Return reconciliation-friendly mutation outcomes** - `dbcb592` (feat)

## Files Created/Modified
- `backend/src/wheeloffish/api/routes/catalog.py` - watch mutation endpoint, provider dispatch, scoped validation, and outcome aggregation.
- `backend/src/wheeloffish/api/schemas/catalog.py` - mutation request/response contracts and target validation.
- `backend/tests/api/test_catalog_watch_mutations.py` - end-to-end API contract coverage for watch mutation flows.

## Decisions Made
- Bulk mutation requests are handled in the same endpoint contract by accepting either `target_id` or `target_ids`.
- Failed provider calls return a normalized API envelope instead of surfacing transport-level errors, enabling deterministic client reconcile behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Watch-state route contracts are in place for library and playlist detail UI mutation actions.
- Response semantics now support direct toast/error messaging plus selective refresh decisions.

## Self-Check: PASSED
- FOUND: `.planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/09-02-SUMMARY.md`
- FOUND: `ca5cddf`
- FOUND: `dbcb592`

---
*Phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p*
*Completed: 2026-05-28*
