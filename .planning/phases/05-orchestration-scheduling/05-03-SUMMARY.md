---
phase: 05-orchestration-scheduling
plan: "03"
subsystem: orchestrator
tags: [orchestrator, rebuild, failure-isolation, snapshot, tdd]
dependency_graph:
  requires:
    - 05-01 (ORM: RebuildRun, Playlist, PlaylistSeriesRow)
    - 05-02 (cadence: is_due, now_in_tz; scheduler stub)
    - 04-xx (PlaylistBuilder.build sole generation path)
  provides:
    - rebuild_inputs.py: fetch_rebuild_inputs_for_row, check_provider_reachable
    - orchestrator.py: rebuild_playlist, run_nightly_rebuilds, run_manual_rebuild, recover_interrupted_rebuilds
    - prune_rebuild_history (rolling 3-run snapshot retention)
    - run_nightly_batch (testable inner function for nightly rebuild loop)
  affects:
    - 05-04 (REST API calls run_manual_rebuild + reads RebuildRun)
    - 05-05 (SPA status badges read RebuildRun.status + snapshot_json)
tech_stack:
  added: []
  patterns:
    - fetch_rebuild_inputs_for_row mirrors catalog route episode/on_deck pattern (no HTTP-call-self)
    - Provider ping-based reachability guard before nightly batch (D-13)
    - PlaylistBuilder.build() sole generation entry point (D-23, SCH-02)
    - TDD RED/GREEN for all four tasks
key_files:
  created:
    - backend/src/wheeloffish/core/playlist/rebuild_inputs.py
    - backend/tests/unit/test_orchestrator.py
    - backend/tests/integration/test_rebuild_e2e.py
  modified:
    - backend/src/wheeloffish/core/orchestrator.py
decisions:
  - "run_nightly_batch exposed as public function for test isolation (avoids session factory mock complexity)"
  - "empty_snapshot rows excluded from valid_inputs to avoid silent REMOVE semantics (D-14); annotated as fetch_warning in row_outcomes_json"
  - "row_outcomes_json stores merged builder outcomes + fetch_warnings dict; keys: outcomes, fetch_warnings"
  - "recover_interrupted_rebuilds is sync (uses passed db session, no async needed)"
  - "SecretsVault created inside rebuild_playlist from get_settings() — orchestrator is self-contained"
metrics:
  duration: "~25 minutes"
  completed_date: "2026-05-25"
  tasks: 4
  files_changed: 4
---

# Phase 5 Plan 03: Rebuild Orchestrator Summary

**One-liner:** Live episode fetch + PlaylistBuilder wiring with per-row failure isolation, snapshot persistence, 3-run rolling history, and nightly batch sequencing backed by 6 passing TDD tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extract fetch_rebuild_inputs helper | c46a238 | rebuild_inputs.py |
| 2 | rebuild_playlist core loop | 46d3d1c | orchestrator.py |
| 3 | Failure isolation unit tests | 966b16a | test_orchestrator.py |
| 4 | Integration test with builder golden path | 954f226 | test_rebuild_e2e.py |

## Deviations from Plan

### Auto-added

**1. [Rule 2 - Missing critical functionality] Exposed `run_nightly_batch` as public function**
- **Found during:** Task 3 (`test_nightly_skips_non_due_weekly`)
- **Issue:** `run_nightly_rebuilds()` creates its own DB session via `get_session_factory()`, making it untestable without monkeypatching session infrastructure
- **Fix:** Extracted inner loop logic into `run_nightly_batch(db, settings)` callable directly by tests; `run_nightly_rebuilds` delegates to it
- **Files modified:** orchestrator.py

None — plan executed correctly for all 4 tasks.

## Architecture Notes

`rebuild_inputs.py` replicates the catalog route's `_cached_series_context` + `_list_episodes`/`_get_on_deck_episode` pattern without any FastAPI HTTP layer. Handles both `rating_key`/`library_native_id` kwargs (for Plex) and positional-only fallback via `TypeError` catch.

`orchestrator.py` persists structured `row_outcomes_json` with two keys:
- `outcomes`: list of builder RowBuildOutcome dicts, annotated with `fetch_warning` when the orchestrator detected failure/empty
- `fetch_warnings`: list of `{series_id, reason}` dicts with reasons `fetch_failure` | `empty_snapshot`

## Decision: D-14 Empty Snapshot Guard

Empty-episode inputs (provider returned `[]`) are NOT passed to `PlaylistBuilder.build()`. This prevents the builder from applying `REMOVE` semantics (series_complete → excluded), which D-14 explicitly forbids ("do NOT treat as series-complete"). Instead, the orchestrator excludes the row and annotates it as `empty_snapshot` in `fetch_warnings`.

## Self-Check

**Created files:**

- [x] `backend/src/wheeloffish/core/playlist/rebuild_inputs.py` — FOUND
- [x] `backend/src/wheeloffish/core/orchestrator.py` — FOUND (replaced stub)
- [x] `backend/tests/unit/test_orchestrator.py` — FOUND
- [x] `backend/tests/integration/test_rebuild_e2e.py` — FOUND

**Commits verified:**

- [x] c46a238 — feat(05-03): extract fetch_rebuild_inputs helper
- [x] 46d3d1c — feat(05-03): rebuild_playlist core loop + orchestrator pipeline
- [x] 966b16a — test(05-03): failure isolation unit tests for orchestrator
- [x] 954f226 — test(05-03): integration test for rebuild_playlist golden path

**Test results:** 5 unit + 1 integration = 6 total passed (0 failures)

## Self-Check: PASSED
