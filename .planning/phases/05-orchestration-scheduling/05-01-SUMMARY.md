---
phase: 05-orchestration-scheduling
plan: "01"
subsystem: persistence
tags: [orm, alembic, migration, mappers, playlists]
dependency_graph:
  requires:
    - 04-playlist-mathematics (domain model)
    - 007_cached_series_composite_pk (migration chain)
  provides:
    - playlists table with episode_count, slot_allocation, refresh_cadence
    - playlist_series_rows table with sort_order and UniqueConstraint
    - rebuild_runs table with status enum and snapshot_json
    - orm_to_playlist mapper for orchestrator consumption
  affects:
    - 05-02 onward (scheduler, API, SPA)
tech_stack:
  added:
    - SQLAlchemy Mapped/mapped_column ORM pattern for three new models
  patterns:
    - ORM → domain mapper separating persistence from business logic
    - TDD RED/GREEN cycle for mapper tests
key_files:
  created:
    - backend/src/wheeloffish/db/models/playlist.py
    - backend/src/wheeloffish/db/models/playlist_series_row.py
    - backend/src/wheeloffish/db/models/rebuild_run.py
    - backend/alembic/versions/008_playlists_rebuilds.py
    - backend/src/wheeloffish/core/playlist/mappers.py
  modified:
    - backend/src/wheeloffish/db/models/__init__.py
    - backend/tests/unit/test_playlist_models.py
    - .env.example
decisions:
  - SQLAlchemy constructors used in tests (not __new__) — SQLAlchemy attribute instrumentation requires proper init
  - rebuild_run.py uses created_at (not started_at) as the always-present timestamp; started_at is nullable for queued state
metrics:
  duration: "~20 minutes"
  completed_date: "2026-05-25"
  tasks: 5
  files_changed: 8
---

# Phase 5 Plan 01: ORM Models, Migration, and Mappers Summary

**One-liner:** SQLAlchemy ORM models for playlists/series-rows/rebuild-runs, Alembic migration 008, and orm_to_playlist mapper with TDD green tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add ORM models and enums | e15493c | playlist.py, playlist_series_row.py, rebuild_run.py, __init__.py |
| 2 | Alembic migration 008 | e32487f | 008_playlists_rebuilds.py |
| 3 | Apply migration | (no new files) | DB upgraded to 008_playlists_rebuilds (head) |
| 4 (RED) | Failing ORM mapper tests | d1d26d1 | test_playlist_models.py |
| 4 (GREEN) | orm_to_playlist mapper + fix tests | 0415c1e | mappers.py, test_playlist_models.py |
| 5 | Document schedule env vars | e0fc129 | .env.example |
| style | Fix ruff import sort | 9063af6 | rebuild_run.py |

## Verification Evidence

```
$ cd backend && uv run alembic current
008_playlists_rebuilds (head)

$ uv run pytest tests/unit/test_playlist_models.py -q
.............
13 passed in 0.02s
```

All acceptance criteria met:
- `Playlist.__tablename__ == "playlists"` ✓
- `RebuildRun.__tablename__ == "rebuild_runs"` ✓
- `alembic current` shows `008_playlists_rebuilds (head)` ✓
- `orm_to_playlist` in mappers.py ✓
- mappers.py does not import FastAPI or httpx ✓
- `WOF_INSTALL_TIMEZONE` and `WOF_REBUILD_CRON` in .env.example ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SQLAlchemy __new__ constructor fails for instrumented attributes**
- **Found during:** Task 4 GREEN phase (test run)
- **Issue:** Using `PlaylistOrm.__new__(PlaylistOrm)` bypasses `__init__`, leaving SQLAlchemy instance state uninitialized; setting attributes raises `AttributeError: 'NoneType' object has no attribute 'set'`
- **Fix:** Changed test helpers to use proper constructors `PlaylistOrm(id=..., app_user_id=..., ...)` which correctly initialize instrumented attributes
- **Files modified:** `backend/tests/unit/test_playlist_models.py`
- **Commit:** 0415c1e

**2. [Rule 1 - Style] Ruff import sort violation in rebuild_run.py**
- **Found during:** Overall verification ruff check
- **Issue:** `JSON` import placed after `Integer` instead of correct alphabetical order in sqlalchemy imports
- **Fix:** `uv run ruff check --fix rebuild_run.py`
- **Files modified:** `backend/src/wheeloffish/db/models/rebuild_run.py`
- **Commit:** 9063af6

### Out-of-Scope Lint (deferred)

- `connection.py` has a pre-existing `I001` ruff import sort violation — not introduced by this plan, logged but not fixed per scope boundary rule.

## Known Stubs

None — no stub values, placeholder text, or unwired components in this plan. All ORM fields have concrete defaults; mapper converts all string columns to StrEnum values.

## Threat Surface Scan

No new network endpoints or auth paths introduced. Schema is per-user (`app_user_id` FK on `playlists`) per T-05-01-02/D-18. `episode_count` has `nullable=False` with `server_default="20"` per T-05-01-01 mitigation.

## Self-Check: PASSED

Files exist:
- backend/src/wheeloffish/db/models/playlist.py ✓
- backend/src/wheeloffish/db/models/playlist_series_row.py ✓
- backend/src/wheeloffish/db/models/rebuild_run.py ✓
- backend/alembic/versions/008_playlists_rebuilds.py ✓
- backend/src/wheeloffish/core/playlist/mappers.py ✓

Commits verified:
- e15493c ✓ (ORM models)
- e32487f ✓ (migration)
- d1d26d1 ✓ (RED tests)
- 0415c1e ✓ (GREEN mapper)
- e0fc129 ✓ (.env.example)
- 9063af6 ✓ (style fix)
