---
phase: 05-orchestration-scheduling
plan: "04"
subsystem: api
tags: [api, playlists, crud, ownership, rebuild]
dependency_graph:
  requires: ["05-03"]
  provides: ["REST playlist CRUD", "rebuild trigger endpoint"]
  affects: ["main.py router mount", "integration test suite"]
tech_stack:
  added: []
  patterns: ["FastAPI APIRouter", "SQLAlchemy ownership filter", "AsyncMock in tests"]
key_files:
  created:
    - backend/src/wheeloffish/api/schemas/playlists.py
    - backend/src/wheeloffish/api/routes/playlists.py
    - backend/tests/integration/test_playlists_api.py
  modified:
    - backend/src/wheeloffish/main.py
decisions:
  - "D-18 ownership enforced via _get_owned_playlist helper returning 404 (not 403) to avoid existence leakage"
  - "Rebuild endpoint co-located in playlists.py (not separate file) for cohesion"
  - "Integration tests use _set_user() helper to switch overrides per-call, avoiding shared TestClient fixture collision"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-25"
  tasks_completed: 4
  tasks_total: 4
---

# Phase 05 Plan 04: Playlist REST API Summary

**One-liner:** FastAPI playlist CRUD with per-user ownership scoping, rebuild trigger (409 guard), snapshot detail, and 13 integration tests.

---

## Tasks Completed

| # | Name | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Pydantic schemas | c3cd894 | `api/schemas/playlists.py` |
| 2 | CRUD routes + main mount | 23fdc04 | `api/routes/playlists.py`, `main.py` |
| 3 | Rebuild endpoint | 23fdc04 | `api/routes/playlists.py` (co-located) |
| 4 | Integration tests | 793cdc1 | `tests/integration/test_playlists_api.py` |

---

## What Was Built

### Schemas (`api/schemas/playlists.py`)

- `PlaylistCreateRequest` — name (min=1), episode_count (ge=1, default 20), slot_allocation, default_completion_policy, refresh_cadence (daily|weekly pattern), refresh_day_of_week (0–6), rows
- `PlaylistUpdateRequest` — same fields all optional
- `PlaylistSeriesRowRequest` — series_id + RowMode/CompletionPolicy/CompletionEvent from domain enums
- `RebuildRunSummary` — id, status, started_at/finished_at, error_message, slots_filled/requested
- `SnapshotEpisode` — episode_id, title, series_id, series_title (from CachedSeries), slot_index, row_mode
- `PlaylistDetailResponse` — full playlist config + current snapshot + last_rebuild + recent_runs (max 3)
- `PlaylistListItem` — id, name, refresh_cadence, refresh_day_of_week, last_rebuild_status/at for badges (D-21)
- `@model_validator` on both request types: weekly cadence requires refresh_day_of_week 0–6

### Router (`api/routes/playlists.py`)

- `GET  /api/v1/playlists` — list owned playlists with last rebuild status (D-21)
- `POST /api/v1/playlists` — create; defaults refresh_cadence=daily, episode_count=20 (D-04)
- `GET  /api/v1/playlists/{id}` — detail with snapshot from latest succeeded/partial run (D-16)
- `PUT  /api/v1/playlists/{id}` — replace rows; clear orphan rows; ownership gate (D-18)
- `DELETE /api/v1/playlists/{id}` — cascade delete via ORM; ownership gate (D-18)
- `POST /api/v1/playlists/{id}/rebuild` — 409 if running; calls `run_manual_rebuild`; owner-only (D-06, D-22)
- `_get_owned_playlist()` helper raises 404 for wrong owner or missing playlist

### Threat mitigations applied (all from plan threat_model)

| Threat | Mitigation | Where |
|--------|-----------|-------|
| T-05-04-01 Information Disclosure | 404 for non-owner GET | `_get_owned_playlist` |
| T-05-04-02 Tampering (rebuild) | Owner-only; rejects cross-user | `rebuild_playlist` route |
| T-05-04-03 Tampering (PUT body) | Pydantic ge=1, StrEnum validation | `PlaylistUpdateRequest` |
| T-05-04-04 Spoofing (unauth CRUD) | `Depends(get_current_user)` on all routes | all handlers |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TestClient fixture collision in cross-user tests**
- **Found during:** Task 4 (integration tests)
- **Issue:** Two user fixtures (`client_a`, `client_b`) shared one `base_client` object and one `app.dependency_overrides[get_current_user]` slot. The second fixture always overrode the first, causing ownership tests to see wrong user.
- **Fix:** Replaced two-fixture pattern with a single `base_client` + `_set_user(user)` helper called inline per request section in each test.
- **Files modified:** `tests/integration/test_playlists_api.py`
- **Commit:** 793cdc1

### Plan Conformance

Tasks 2 and 3 were committed together (one commit) because the rebuild endpoint was implemented in the same `playlists.py` file as the CRUD routes — co-location is correct per the plan's `key_links` spec.

---

## Known Stubs

None — all routes are wired to live DB queries and the orchestrator.

---

## Threat Flags

None — no new surface beyond the plan's threat model.

---

## Self-Check

```
backend/src/wheeloffish/api/schemas/playlists.py  FOUND
backend/src/wheeloffish/api/routes/playlists.py   FOUND
backend/tests/integration/test_playlists_api.py   FOUND
c3cd894 FOUND (git log)
23fdc04 FOUND (git log)
793cdc1 FOUND (git log)
13/13 integration tests PASS
ruff: All checks passed
```

## Self-Check: PASSED
