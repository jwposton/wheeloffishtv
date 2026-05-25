---
phase: 04-playlist-mathematics
plan: 03
subsystem: domain
tags: [pydantic, playlist, completion-policy, resume, pytest]

requires:
  - phase: 04-playlist-mathematics
    provides: PlaylistSeriesRow, RowBuildOutcome, CompletionPolicy enums from 04-01
  - phase: 02-media-ingestion-catalogs
    provides: ResumeService series_complete detection via Episode DTOs
provides:
  - Playlist.default_completion_policy field for Phase 5 row creation (D-13)
  - evaluate_completion, apply_policy, resolve_row_policy pure functions (PLT-06)
  - Nine golden-vector tests proving D-11, D-12, D-14, D-15 semantics
affects:
  - 04-04 ordered picker (reads policy_applied == RESTART)
  - 04-06 builder orchestration (calls completion once per row before allocation)

tech-stack:
  added: []
  patterns:
    - "ResumeService as single source of truth for series_complete (Pitfall 1)"
    - "Composable evaluate_completion + apply_policy (no mid-build re-evaluation per D-15)"
    - "resolve_row_policy single hook for future per-playlist defaulting"

key-files:
  created:
    - backend/src/wheeloffish/core/playlist/completion.py
    - backend/tests/unit/test_completion_policies.py
  modified:
    - backend/src/wheeloffish/domain/playlist.py

key-decisions:
  - "Playlist.default_completion_policy defaults to REMOVE (D-12); row policy wins at evaluation (D-14)"
  - "Only SERIES_COMPLETE triggers in v1; season finish returns None (D-11)"
  - "RESTART sets effective_mode=ORDERED and policy_applied=RESTART; cursor reset deferred to 04-04 (D-17)"

patterns-established:
  - "Pattern 1: RowBuildOutcome records policy_applied for audit trails (T-04-03-02)"
  - "Pattern 2: Stateless completion functions invoked once per row at build start (D-15)"

requirements-completed: [PLT-06]

duration: 8min
completed: 2026-05-25
---

# Phase 4 Plan 03: Completion Policies Summary

**Series-complete detection via ResumeService with remove/restart/disordered RowBuildOutcome policies and per-playlist default_completion_policy hook**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-25T20:31:00Z
- **Completed:** 2026-05-25T20:39:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `Playlist.default_completion_policy: CompletionPolicy = CompletionPolicy.REMOVE` after `episode_count` (D-12/D-13)
- Implemented three pure functions in `core/playlist/completion.py` for Wave 3 builder consumption
- Proved SERIES_COMPLETE-only v1 restriction: season 1 complete with unwatched season 2 returns `None` (D-11)
- Proved per-row policy precedence over playlist default via `resolve_row_policy` (D-14)
- 15 unit tests green (6 model + 9 policy); ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add default_completion_policy model tests** - `191af19` (test)
2. **Task 1 GREEN: Add Playlist.default_completion_policy field** - `670f08a` (feat)
3. **Task 2 RED / Task 3: Golden-vector completion policy tests** - `407b0fd` (test)
4. **Task 2 GREEN: Implement completion.py functions** - `25adab5` (feat)

**Plan metadata:** `1a9e76b` (docs: complete plan)

## Wave 3 Function Signatures

```python
def evaluate_completion(
    row: PlaylistSeriesRow,
    episodes: list[Episode],
    on_deck: Episode | None,
) -> CompletionEvent | None

def apply_policy(
    row: PlaylistSeriesRow,
    completion_event: CompletionEvent | None,
) -> RowBuildOutcome

def resolve_row_policy(
    playlist: Playlist,
    row: PlaylistSeriesRow,
) -> CompletionPolicy
```

Import path: `from wheeloffish.core.playlist.completion import evaluate_completion, apply_policy, resolve_row_policy`

## SERIES_COMPLETE-Only Proof

- `evaluate_completion` returns `CompletionEvent.SERIES_COMPLETE` iff `ResumeService().compute(...).series_complete is True`
- `test_evaluate_completion_does_not_fire_on_season_finish_d11` proves season finish alone does not trigger completion
- `CompletionEvent.SEASON_COMPLETE` enum exists (04-01) but is never produced by Phase 4 logic

## Files Created/Modified

- `backend/src/wheeloffish/domain/playlist.py` — Added `default_completion_policy` field on `Playlist`
- `backend/src/wheeloffish/core/playlist/completion.py` — `evaluate_completion`, `apply_policy`, `resolve_row_policy`
- `backend/tests/unit/test_playlist_models.py` — Two new default policy tests (6 total)
- `backend/tests/unit/test_completion_policies.py` — Nine golden-vector policy tests

## Decisions Made

- Tests for completion policies authored during Task 2 TDD RED phase (committed before implementation) — Task 3 verification satisfied by same commit
- `apply_policy` uses structural match on `CompletionPolicy` for exhaustive mapping
- Fallback passthrough outcome for unknown completion events (defensive; unreachable in v1)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 3 builder (04-06) can import `evaluate_completion` + `apply_policy` per row before slot allocation
- 04-04 ordered picker should read `policy_applied == RESTART` to reset cursor to index 0
- Phase 5 can use `Playlist.default_completion_policy` when creating new rows

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/completion.py
- FOUND: backend/tests/unit/test_completion_policies.py
- FOUND: .planning/phases/04-playlist-mathematics/04-03-SUMMARY.md
- FOUND: commits 191af19, 670f08a, 407b0fd, 25adab5 (verified via git cat-file)

---
*Phase: 04-playlist-mathematics*
*Completed: 2026-05-25*
