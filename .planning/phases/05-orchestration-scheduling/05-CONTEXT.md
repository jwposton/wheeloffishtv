# Phase 5: Orchestration & scheduling - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver **playlist persistence, rebuild orchestration, and operator UI** so users can define playlists, receive nightly (or manual) rebuilds via `PlaylistBuilder.build()`, and inspect output + job status.

**In scope:** Alembic migrations for playlist config + rebuild snapshots + job state; APScheduler nightly batch; per-playlist refresh cadence (daily / weekly DOW); live episode fetch at rebuild time; REST API; minimal SPA (`/playlists` CRUD, output view, status badges, Rebuild now); failure isolation; CR-01 guard for empty snapshots; last-3-run history.

**Out of scope:** WheelOfFish admin playlist (Phase 6); export/push playlists to Plex/Jellyfin; per-playlist clock times (only cadence, not hour); catch-up rebuilds after missed windows; Celery/Redis worker; episode SQLite cache; full WEB-01 polish / Lighthouse pass (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Global schedule & per-playlist cadence
- **D-01:** **Global nightly cron at 04:00 UTC** — single install-wide timer (env-configurable default `WOF_REBUILD_CRON_UTC=04:00` or equivalent).
- **D-02:** Each playlist declares **refresh cadence**: `daily` **or** `weekly` on a chosen **day of week** (Mon–Sun).
- **D-03:** Nightly job evaluates **which playlists are due** that night and rebuilds **only those** (not all playlists every night unless daily).
- **D-04:** **Default cadence for new playlists = daily**.
- **D-05:** **Missed window → skip until next due** — if container was down at 04:00 UTC, no catch-up pile-up (daily: next night; weekly: next matching DOW).
- **D-06:** **Manual “Rebuild now”** runs immediately via same pipeline as scheduled (Phase 4 D-23); does **not** suppress or reset the next scheduled run.

### Job runner & batch behavior
- **D-07:** **APScheduler inside FastAPI** lifespan — in-process, single Compose service (matches research recommendation).
- **D-08:** Due playlists processed **sequentially** one after another the same night.
- **D-09:** **Persist job state in DB** (`queued` / `running` / `succeeded` / `failed` / `partial` — exact enum at planner discretion).
- **D-10:** **No automatic same-night retry** on failure — log + surface status; next due window tries again.

### Failure isolation & partial rebuilds
- **D-11:** **Single series fetch failure → skip row, finish playlist** — record row-level failure; remaining rows continue.
- **D-12:** **All series fail or all rows excluded → mark rebuild failed**, keep **last good snapshot** (do not wipe with empty output).
- **D-13:** **Provider entirely unreachable → skip all rebuilds that night**, log once; each due playlist gets provider-unavailable failure without retry hammering.
- **D-14:** **Empty episode snapshot (CR-01) → row-level `empty_snapshot` warning** — exclude row for this rebuild; do **not** treat as series-complete / silent REMOVE.

### Output persistence & ownership
- **D-15:** Persist **full snapshot** per successful rebuild — episode list (ids, titles, series, slot order, row mode) + builder metadata (`slots_filled`, `slots_requested`, `rebuild_seed`, row outcomes, timestamps).
- **D-16:** Retain **last 3 rebuild runs** per playlist (rolling history); current = latest success.
- **D-17:** **Failed attempts store status + error message only** — last good output unchanged.
- **D-18:** Playlists and outputs are **per authenticated user** (`app_user_id` ownership).

### SPA scope (Phase 5 minimal operator UI)
- **D-19:** Phase 5 includes **minimal operator UI** — playlist list, create/edit, view current output, status badge, Rebuild now (reuse Phase 3 design system).
- **D-20:** **Top-level `/playlists`** list and **`/playlists/:id`** detail (settings + output + status).
- **D-21:** Status UX: **badge on playlist card** (green / amber / red for success / partial / failed) + **detail banner** with `last_rebuild_at` and error text.
- **D-22:** **Rebuild now** callable by **playlist owner only** (no cross-user admin rebuild until WheelOfFish Phase 6).

### Playlist config storage
- **D-23:** **DB tables mirror Phase 4 domain model** — `playlists` + `playlist_series_rows` map to `Playlist` / `PlaylistSeriesRow`; orchestrator loads → Pydantic → `PlaylistBuilder.build()`.
- **D-24:** Cadence storage: **`refresh_cadence` enum (`daily` | `weekly`)** + **`refresh_day_of_week` (0–6 | null)**; null DOW when daily.
- **D-25:** Add shows via **cached catalog browse with search/filter/select** — series from Phase 2 `cached_series` in scoped libraries; store provider `series_id` matching catalog (not free-text-only entry).
- **D-26:** **Expose Phase 4 advanced settings in Phase 5 UI** — `episode_count`, `slot_allocation` (Wild / Balanced / Round-robin labels), `default_completion_policy`, per-row completion override, ordered/disordered per row.

### Claude's Discretion
- Exact Alembic table/column names, job state enum values, APScheduler trigger wiring, snapshot JSON vs normalized episode rows, amber vs red threshold for partial (any row skip = amber), startup handling for `running` jobs interrupted by restart, env var names for cron UTC time, TanStack Query cache keys for playlist routes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Product vision, daily rebuild scheduler
- `.planning/REQUIREMENTS.md` — SCH-01 (daily schedule), WEB-01 (partial), PLT-01–03 persistence glue
- `.planning/ROADMAP.md` — Phase 5 goal and success criteria
- `.planning/research/SUMMARY.md` — APScheduler in-proc recommendation

### Prior phase context
- `.planning/phases/04-playlist-mathematics/04-CONTEXT.md` — Builder contract D-22–D-24, manual=scheduled pipeline
- `.planning/phases/04-playlist-mathematics/04-RESEARCH.md` — Phase 5 orchestrator wiring pattern
- `.planning/phases/04-playlist-mathematics/04-SECURITY.md` — CR-01 advisory → D-14 guard
- `.planning/phases/04-playlist-mathematics/04-REVIEW.md` — CR-01 empty snapshot finding
- `.planning/phases/02-media-ingestion-catalogs/02-CONTEXT.md` — D-15 live episode fetch, D-14 no episode cache
- `.planning/phases/03-minimal-operator-spa-shell/03-CONTEXT.md` — SPA patterns, auth, nav shell

### Existing code (reuse — do not reimplement)
- `backend/src/wheeloffish/core/playlist/builder.py` — `PlaylistBuilder.build()`
- `backend/src/wheeloffish/domain/playlist.py` — Domain models
- `backend/src/wheeloffish/api/routes/catalog.py` — Live episode + on-deck fetch
- `backend/src/wheeloffish/db/models/cached_series.py` — Series picker source
- `backend/src/wheeloffish/core/config.py` — Settings pattern for new env vars
- `backend/src/wheeloffish/main.py` — Lifespan hook for scheduler start/stop

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlaylistBuilder.build(playlist, inputs, rebuild_seed)` — sole rebuild entry point
- Catalog routes + Plex/Jellyfin providers — fetch episodes + on_deck per series at rebuild time
- `cached_series` / browse SPA patterns — series picker with search (extend for playlist membership)
- Session auth + `app_user` model — per-user ownership
- Structlog request logging — extend for rebuild job logging

### Established Patterns
- SQLAlchemy models + Alembic migrations under `backend/alembic/`
- FastAPI routers under `api/routes/` with `/api/v1` prefix
- React SPA with TanStack Query (Phase 3)
- Pydantic domain DTOs separate from ORM (load ORM → domain → builder)

### Integration Points
- **Nightly job:** query due playlists → for each: load config, fetch live inputs, call builder, persist snapshot, update job status
- **Manual rebuild API:** `POST /api/v1/playlists/{id}/rebuild` — same orchestrator function
- **SPA:** new `/playlists` routes in frontend router; status from `GET /api/v1/playlists/{id}` or list endpoint

</code_context>

<specifics>
## Specific Ideas

- Global refresh runs at **4am UTC**; user sets per-playlist **Daily** or **Weekly on Saturday / Monday** etc.
- Adding shows: **search, filter, select** from catalog (not paste-only IDs)
- Status badges: green success, amber partial (row skips), red failed
- Keep **3 rebuild snapshots** for debugging “what changed”

</specifics>

<deferred>
## Deferred Ideas

- **Per-playlist clock time** — only cadence (daily/weekly DOW), not “rebuild at 9pm”; global 04:00 UTC handles timing
- **Catch-up rebuilds** after downtime — explicitly rejected (D-05)
- **WheelOfFish** global playlist — Phase 6
- **Export playlist to Plex/Jellyfin** — out of scope MVP
- **Separate worker container / Celery** — defer unless scale demands
- **Job log / activity page** — deferred; badge + detail banner sufficient for Phase 5

</deferred>

---

*Phase: 05-orchestration-scheduling*
*Context gathered: 2026-05-25*
