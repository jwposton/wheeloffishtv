---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
plan: 01
subsystem: api
tags: [plex, jellyfin, watch-state, integrations]
requires:
  - phase: 07-provider-playlist-writeback
    provides: plex guid-to-ratingKey resolution patterns
provides:
  - Typed provider watch-state mutation contract
  - Plex and Jellyfin watch mutation adapter methods
  - Unit coverage for mutation dispatch and error propagation
affects: [catalog-api, series-detail-watch-actions, provider-integration]
tech-stack:
  added: []
  patterns: [provider mutation request enum contract, adapter-level request mapping]
key-files:
  created:
    - backend/tests/unit/test_watch_writeback_services.py
  modified:
    - backend/src/wheeloffish/integrations/base.py
    - backend/src/wheeloffish/integrations/plex/client.py
    - backend/src/wheeloffish/integrations/jellyfin/client.py
key-decisions:
  - "Use a shared WatchMutationRequest with explicit scope/action enums to prevent contract drift."
  - "Expose one mutate_watch_state provider method and keep provider-specific endpoint mapping inside adapters."
patterns-established:
  - "Provider contract mutation requests use StrEnum-backed scope/action values."
  - "Plex mutations resolve composite ids to ratingKey before scrobble/unscrobble."
requirements-completed: [INT-01, INT-02]
duration: 1 min
completed: 2026-05-27
---

# Phase 9 Plan 1: Add provider watch-state mutation contract and adapters Summary

**Provider-level watched/unwatched mutation primitives now exist for Plex and Jellyfin using a typed shared contract plus adapter-specific endpoint routing.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-27T22:42:15-04:00
- **Completed:** 2026-05-27T22:43:19-04:00
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `WatchScope`, `WatchAction`, and `WatchMutationRequest` in provider base integration contract.
- Added `MediaProvider.mutate_watch_state(...)` protocol method for a uniform write-path API.
- Implemented Plex adapter mutation behavior using `:/scrobble`/`:/unscrobble` and composite-id key resolution.
- Implemented Jellyfin adapter mutation behavior using `POST/DELETE /UserPlayedItems/{itemId}`.
- Added dedicated unit tests for contract validation, adapter dispatch, and auth error propagation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add typed provider watch-state mutation contract** - `ef8d8ac` (test), `b2fbcf3` (feat)
2. **Task 2: Implement Plex/Jellyfin watch-state adapter methods** - `17ec564` (feat)

## Files Created/Modified
- `backend/src/wheeloffish/integrations/base.py` - added watch mutation enums/request type and protocol method.
- `backend/src/wheeloffish/integrations/plex/client.py` - added `mutate_watch_state` with ratingKey resolution and scrobble endpoint calls.
- `backend/src/wheeloffish/integrations/jellyfin/client.py` - added `mutate_watch_state` with UserPlayedItems POST/DELETE calls.
- `backend/tests/unit/test_watch_writeback_services.py` - added contract and adapter request/error tests.

## Verification Results
- `cd backend && uv run python -m pytest tests/unit/test_watch_writeback_services.py -q` -> **PASS** (15 passed)

## Decisions Made
- Used `from_values(...)` constructor on `WatchMutationRequest` to enforce explicit invalid scope/action rejection.
- Kept adapter methods exception-transparent so provider auth failures propagate and cannot report false success.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Backend test environment missing dependencies**
- **Found during:** Task 1 (RED test run)
- **Issue:** `pytest` failed with `ModuleNotFoundError: alembic` before contract assertions could run.
- **Fix:** Bootstrapped backend environment via `cd backend && uv sync` and executed tests via `uv run`.
- **Files modified:** None
- **Verification:** Red-to-green test cycle completed and final verification passed.
- **Committed in:** N/A (environment-only)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope change; environment fix was required to run mandated tests.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Provider mutation contract is ready for API route integration in `09-02-PLAN.md`.

## Self-Check: PASSED
- Found created file: `backend/tests/unit/test_watch_writeback_services.py`
- Found commits: `ef8d8ac`, `b2fbcf3`, `17ec564`
