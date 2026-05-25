# Phase 5: Orchestration & scheduling - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 05-orchestration-scheduling
**Areas discussed:** Nightly schedule model, Job runner placement, Failure isolation, Output persistence, Phase 5 UI boundary, Playlist definition storage

---

## 1. Nightly schedule model

| Option | Description | Selected |
|--------|-------------|----------|
| Global nightly window | One cron; all due playlists refresh in window | ✓ |
| Per-playlist clock time | Each playlist picks hour/timezone | |
| Global + per-playlist override | Shared default with overrides | |

**User's choice:** Global nightly timer at **04:00 UTC**. Per-playlist **cadence** only: **Daily** or **Weekly (day of week)** e.g. Saturday, Monday. Nightly job determines which playlists are due.
**Notes:** Default cadence for new playlists = **Daily**. Missed window = **skip until next due**. Manual rebuild = **immediate**, does not suppress next scheduled run.

---

## 2. Job runner placement

| Option | Description | Selected |
|--------|-------------|----------|
| APScheduler in FastAPI | In-process, single container | ✓ |
| Separate worker container | Second service | |
| OS cron + CLI | External trigger | |

**User's choice:** APScheduler in FastAPI; **sequential** playlist processing; **persist job state** in DB; **no same-night retry**.
**Notes:** Matches self-host Compose single-service model.

---

## 3. Failure isolation & partial rebuilds

| Option | Description | Selected |
|--------|-------------|----------|
| Skip failed row, finish playlist | Row-level failure recorded | ✓ |
| Fail whole playlist on one series error | | |
| Empty snapshot = row warning | CR-01 fix; not silent REMOVE | ✓ |

**User's choice:** Skip row on single series failure; all-fail keeps last good snapshot; provider down skips all with one log; empty snapshot gets `empty_snapshot` reason.
**Notes:** Addresses code review CR-01 from Phase 4.

---

## 4. Output persistence & history

| Option | Description | Selected |
|--------|-------------|----------|
| Full snapshot | Episodes + metadata for rendering | ✓ |
| Latest only | Single current snapshot | |
| Last 3 runs | Rolling history | ✓ |
| Per-user ownership | Each OAuth user owns playlists | ✓ |

**User's choice:** Full snapshot; **last 3 runs** history; failed attempts = status + error only (keep last good output); per-user ownership.

---

## 5. Phase 5 UI boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal operator UI | List, CRUD, output, badge, Rebuild now | ✓ |
| API only | No SPA this phase | |
| Top-level /playlists | List + detail routes | ✓ |
| Badge + detail banner | Green/amber/red status | ✓ |
| Owner-only Rebuild now | | ✓ |

**User's choice:** All recommended (option 1) for each question in batch response.

---

## 6. Playlist definition storage

| Option | Description | Selected |
|--------|-------------|----------|
| DB tables mirror domain model | playlists + playlist_series_rows | ✓ |
| Enum + DOW for cadence | daily \| weekly + day_of_week | ✓ |
| Catalog search/filter/select | Pick from cached_series | ✓ |
| Expose all advanced settings | N, slot allocation, policies | ✓ |

**User's choice:** Q11, Q21, Q32 (catalog picker with search/filter/select UX), Q41.
**Notes:** User clarified series selection is browse/search from catalog, not free-text-only.

---

## Claude's Discretion

Alembic schema details, job state enum, snapshot storage shape (JSON vs normalized), partial-status threshold, interrupted-job startup handling, env var naming.

## Deferred Ideas

- Per-playlist clock times (hour-of-day)
- Catch-up after missed cron
- Dedicated job log page
- Celery/Redis worker
- WheelOfFish (Phase 6)
- Plex/Jellyfin export
