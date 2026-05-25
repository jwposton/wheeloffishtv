---
phase: 05-orchestration-scheduling
plan: "02"
subsystem: scheduling
tags: [apscheduler, cron, cadence, timezone, lifespan, tdd]
dependency_graph:
  requires:
    - 05-01 (ORM models: RebuildRun, Playlist)
  provides:
    - APScheduler AsyncIOScheduler wired in FastAPI lifespan (D-07)
    - WOF_INSTALL_TIMEZONE + WOF_REBUILD_CRON config fields with install_tz() method
    - is_due(playlist, now_local) cadence filter in install TZ (D-02/D-03/D-04)
    - parse_cron_time() + now_in_tz() helpers
    - recover_interrupted_rebuilds() on startup
  affects:
    - 05-03 (orchestrator calls is_due + run_nightly_rebuilds)
tech_stack:
  added:
    - apscheduler~=3.11.2 (pinned per T-05-02-SC)
    - tzlocal~=5.3.1 (apscheduler transitive)
  patterns:
    - TDD RED/GREEN for cadence and scheduler factory
    - ZoneInfo IANA fallback pattern with structlog warning
    - max_instances=1 + coalesce=True APScheduler job config
key_files:
  created:
    - backend/src/wheeloffish/core/scheduler.py
    - backend/src/wheeloffish/core/playlist/cadence.py
    - backend/src/wheeloffish/core/orchestrator.py
    - backend/tests/unit/test_playlist_cadence.py
    - backend/tests/unit/test_scheduler.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/src/wheeloffish/core/config.py
    - backend/src/wheeloffish/main.py
decisions:
  - install_tz() is a regular method (not computed_field) — ZoneInfo is not JSON-serialisable; avoids Pydantic serialization issues
  - orchestrator.py created as stub no-op; run_nightly_rebuilds implemented in 05-03
  - recover_interrupted_rebuilds queries RebuildRun directly (not via ORM session dependency) to avoid async session at startup
metrics:
  duration: "~20 minutes"
  completed_date: "2026-05-25"
  tasks: 3
  files_changed: 9
---

# Phase 5 Plan 02: APScheduler + Cadence Evaluation Summary

**One-liner:** APScheduler AsyncIOScheduler wired in FastAPI lifespan with install-timezone CronTrigger and is_due() cadence filter backed by 21 passing TDD tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install APScheduler + schedule config fields | 1b93630 | pyproject.toml, uv.lock, config.py |
| 2 (RED) | Failing cadence tests | a342620 | test_playlist_cadence.py |
| 2 (GREEN) | Cadence evaluation in install timezone | a510ff7 | cadence.py |
| 3 (RED) | Failing scheduler tests | 926c835 | test_scheduler.py |
| 3 (GREEN) | Scheduler factory + lifespan wiring | cf0748a | scheduler.py, orchestrator.py, main.py |

## Verification Evidence

```
$ cd backend && uv run pytest tests/unit/test_playlist_cadence.py tests/unit/test_scheduler.py -q
.....................
21 passed in 0.01s

$ uv run ruff check src/wheeloffish/core/scheduler.py src/wheeloffish/core/playlist/cadence.py
All checks passed!

# Acceptance criteria checks:
$ grep -c 'scheduler.start' backend/src/wheeloffish/main.py
1
$ grep -c 'install_tz' backend/src/wheeloffish/core/scheduler.py
1
$ grep -c 'def is_due' backend/src/wheeloffish/core/playlist/cadence.py
1
```

All acceptance criteria met:
- `pyproject.toml` lists `apscheduler~=3.11.2` ✓
- `Settings` has `WOF_INSTALL_TIMEZONE` default `"UTC"` and `WOF_REBUILD_CRON` default `"04:00"` ✓
- No `WOF_REBUILD_CRON_UTC` field ✓
- `uv run pytest tests/unit/test_playlist_cadence.py -q` → 14 passed (≥5 required) ✓
- `grep -c 'def is_due' cadence.py` == 1 ✓
- is_due accepts timezone-aware datetime ✓
- `grep -c 'scheduler.start' main.py` == 1 ✓
- CronTrigger uses `settings.install_tz()` not hardcoded UTC ✓
- All scheduler tests pass ✓

## TDD Gate Compliance

Both TDD tasks followed correct RED → GREEN sequence:

- Task 2: `a342620` (test/RED) → `a510ff7` (feat/GREEN) ✓
- Task 3: `926c835` (test/RED) → `cf0748a` (feat/GREEN) ✓

## Deviations from Plan

### Auto-added Missing Critical Functionality (Rule 2)

**1. [Rule 2 - Missing] Created orchestrator.py stub**
- **Found during:** Task 3 implementation
- **Issue:** `main.py` must import `run_nightly_rebuilds` from `wheeloffish.core.orchestrator`, but the module did not exist yet (implemented in 05-03)
- **Fix:** Created `orchestrator.py` with a no-op async stub that logs when called
- **Files modified:** `backend/src/wheeloffish/core/orchestrator.py`
- **Commit:** cf0748a

## Known Stubs

**`wheeloffish/core/orchestrator.py` — `run_nightly_rebuilds()`**
- The function body is a no-op stub (logs and returns immediately)
- This is intentional: the real orchestration logic is the subject of Plan 05-03
- Wired correctly in `main.py` lifespan so the scheduler will call it on the nightly cron

## Threat Surface Scan

No new network endpoints or auth paths introduced. The scheduler runs in-process (no new socket). `recover_interrupted_rebuilds` writes to the `rebuild_runs` table only (per-user data, existing trust boundary). All threat model items addressed:

| Threat | Mitigation Applied |
|--------|--------------------|
| T-05-02-01 DoS job overlap | `max_instances=1` on nightly_rebuilds job |
| T-05-02-02 WOF_REBUILD_CRON parse | `parse_cron_time()` raises `ValueError` on invalid HH:MM, propagated at scheduler creation |
| T-05-02-03 WOF_INSTALL_TIMEZONE | `install_tz()` catches `ZoneInfoNotFoundError`, falls back to UTC with structlog warning |
| T-05-02-SC pip/uv deps | `apscheduler~=3.11.2` pinned in pyproject.toml |

## Self-Check: PASSED

Files exist:
- backend/src/wheeloffish/core/scheduler.py ✓
- backend/src/wheeloffish/core/playlist/cadence.py ✓
- backend/src/wheeloffish/core/orchestrator.py ✓
- backend/tests/unit/test_playlist_cadence.py ✓
- backend/tests/unit/test_scheduler.py ✓

Commits verified:
- 1b93630 ✓ (APScheduler install + config)
- a342620 ✓ (cadence RED tests)
- a510ff7 ✓ (cadence GREEN)
- 926c835 ✓ (scheduler RED tests)
- cf0748a ✓ (scheduler GREEN + lifespan)
