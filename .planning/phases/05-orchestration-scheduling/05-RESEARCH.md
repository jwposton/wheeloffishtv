# Phase 5: Orchestration & scheduling - Research

**Researched:** 2026-05-25
**Domain:** Nightly batch orchestration with APScheduler, playlist persistence (Alembic migrations), rebuild job state tracking, per-playlist cadence evaluation, failure isolation, minimal SPA for playlist CRUD
**Confidence:** HIGH

<user_constraints>
## User Constraints (from 05-CONTEXT.md)

### Locked Decisions (D-01 through D-26)

#### Global schedule & per-playlist cadence
- **D-01:** **Global nightly cron in install timezone** — default **04:00** local (`WOF_REBUILD_CRON=04:00`) in **`WOF_INSTALL_TIMEZONE`** (IANA, default `UTC`). Single install-wide timer; not per-user timezone.
- **D-02:** Each playlist declares **refresh cadence**: `daily` **or** `weekly` on a chosen **day of week** (Mon–Sun).
- **D-03:** Nightly job evaluates **which playlists are due** that night and rebuilds **only those** (not all playlists every night unless daily).
- **D-04:** **Default cadence for new playlists = daily**.
- **D-05:** **Missed window → skip until next due** — if container was down at scheduled local time, no catch-up pile-up.
- **D-06:** **Manual "Rebuild now"** runs immediately via same pipeline as scheduled (Phase 4 D-23); does **not** suppress or reset the next scheduled run.

#### Job runner & batch behavior
- **D-07:** **APScheduler inside FastAPI** lifespan — in-process, single Compose service (matches research recommendation).
- **D-08:** Due playlists processed **sequentially** one after another the same night.
- **D-09:** **Persist job state in DB** (`queued` / `running` / `succeeded` / `failed` / `partial` — exact enum at planner discretion).
- **D-10:** **No automatic same-night retry** on failure — log + surface status; next due window tries again.

#### Failure isolation & partial rebuilds
- **D-11:** **Single series fetch failure → skip row, finish playlist** — record row-level failure; remaining rows continue.
- **D-12:** **All series fail or all rows excluded → mark rebuild failed**, keep **last good snapshot** (do not wipe with empty output).
- **D-13:** **Provider entirely unreachable → skip all rebuilds that night**, log once; each due playlist gets provider-unavailable failure without retry hammering.
- **D-14:** **Empty episode snapshot (CR-01) → row-level `empty_snapshot` warning** — exclude row for this rebuild; do **not** treat as series-complete / silent REMOVE.

#### Output persistence & ownership
- **D-15:** Persist **full snapshot** per successful rebuild — episode list (ids, titles, series, slot order, row mode) + builder metadata (`slots_filled`, `slots_requested`, `rebuild_seed`, row outcomes, timestamps).
- **D-16:** Retain **last 3 rebuild runs** per playlist (rolling history); current = latest success.
- **D-17:** **Failed attempts store status + error message only** — last good output unchanged.
- **D-18:** Playlists and outputs are **per authenticated user** (`app_user_id` ownership).

#### SPA scope (Phase 5 minimal operator UI)
- **D-19:** Phase 5 includes **minimal operator UI** — playlist list, create/edit, view current output, status badge, Rebuild now (reuse Phase 3 design system).
- **D-20:** **Top-level `/playlists`** list and **`/playlists/:id`** detail (settings + output + status).
- **D-21:** Status UX: **badge on playlist card** (green / amber / red for success / partial / failed) + **detail banner** with `last_rebuild_at` and error text.
- **D-22:** **Rebuild now** callable by **playlist owner only** (no cross-user admin rebuild until WheelOfFish Phase 6).

#### Playlist config storage
- **D-23:** **DB tables mirror Phase 4 domain model** — `playlists` + `playlist_series_rows` map to `Playlist` / `PlaylistSeriesRow`; orchestrator loads → Pydantic → `PlaylistBuilder.build()`.
- **D-24:** Cadence storage: **`refresh_cadence` enum (`daily` | `weekly`)** + **`refresh_day_of_week` (0–6 | null)**; null DOW when daily.
- **D-25:** Add shows via **cached catalog browse with search/filter/select** — series from Phase 2 `cached_series` in scoped libraries; store provider `series_id` matching catalog (not free-text-only entry).
- **D-26:** **Expose Phase 4 advanced settings in Phase 5 UI** — `episode_count`, `slot_allocation` (Wild / Balanced / Round-robin labels), `default_completion_policy`, per-row completion override, ordered/disordered per row.

### Claude's Discretion
- Exact Alembic table/column names, job state enum values, APScheduler trigger wiring, snapshot JSON vs normalized episode rows, amber vs red threshold for partial (any row skip = amber), startup handling for `running` jobs interrupted by restart, env var names for cron UTC time, TanStack Query cache keys for playlist routes.

### Deferred Ideas (OUT OF SCOPE)
- **Per-playlist clock time** — only cadence (daily/weekly DOW), not "rebuild at 9pm"; global 04:00 UTC handles timing
- **Catch-up rebuilds** after downtime — explicitly rejected (D-05)
- **WheelOfFish** global playlist — Phase 6
- **Export playlist to Plex/Jellyfin** — out of scope MVP
- **Separate worker container / Celery** — defer unless scale demands
- **Job log / activity page** — deferred; badge + detail banner sufficient for Phase 5
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCH-01 | Daily schedule (timezone aware) | CronTrigger with timezone=WOF_INSTALL_TIMEZONE; WOF_REBUILD_CRON local HH:MM; weekly DOW in same TZ |
| SCH-02 | Multipart adjacency (already complete in Phase 4) | Phase 5 orchestration only — fetch inputs, call builder, persist |
| PLT-01 | Persistence glue for named playlists | Alembic migration: `playlists` table; FastAPI POST/PUT/DELETE routes |
| PLT-02 | Persistence glue for N episodes | `playlists.episode_count` column |
| PLT-03 | Persistence glue for add/remove series | `playlist_series_rows` table; junction pattern per Phase 2 libraries |
| WEB-01 (partial) | Playlist CRUD UI, status badges, rebuild now | Frontend `/playlists` routes, TanStack Query mutations, status enum → Badge variant |
</phase_requirements>

## Summary

Phase 5 delivers **end-to-end playlist rebuild orchestration** by wiring the Phase 4 pure builder to nightly APScheduler triggers, persistent DB storage (Alembic: playlists, series rows, rebuild snapshots, job state), and a minimal operator SPA for CRUD + status inspection. The orchestrator is a single nightly job at 04:00 UTC (env-configurable) that evaluates per-playlist cadence (daily / weekly DOW), fetches live episode snapshots via existing Phase 2 catalog/provider APIs, calls `PlaylistBuilder.build()`, persists results, and updates job state. Failure isolation (D-11–D-14) ensures single-row skips don't abort entire playlists; provider-unreachable halts all rebuilds that night without hammering. The SPA extends Phase 3 patterns with new `/playlists` routes (list, create/edit, detail with output + status badge) and reuses `AppShell`, shadcn components, and TanStack Query caching.

**Primary recommendation:** Use **APScheduler 3.11.2 AsyncIOScheduler** in FastAPI lifespan with a single CronTrigger (hour=4, timezone="UTC"). Orchestrator logic is a single async function invoked by the scheduled job — load due playlists from DB → for each: fetch inputs → build → persist snapshot + row outcomes → update job state. Alembic migrations add 4 new tables: `playlists`, `playlist_series_rows`, `rebuild_runs`, `rebuild_snapshots` (or denormalized snapshot JSON on `rebuild_runs` — planner discretion per D-15). Frontend follows Phase 3 vertical slice pattern: one route file, one query hook file, one page per CRUD screen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Scheduled trigger (cron) | APScheduler in FastAPI process | — | In-process scheduler (D-07) avoids Celery/Redis complexity |
| Playlist config CRUD | FastAPI `/api/v1/playlists` routes | DB (SQLAlchemy models) | Standard REST pattern; ownership by `app_user_id` (D-18) |
| Playlist + series membership persistence | SQLAlchemy ORM → Alembic migrations | — | Reuses Phase 1–2 DB patterns |
| Rebuild orchestration | `core/orchestrator.py` (new) | PlaylistBuilder + catalog/provider | Pure async function: fetch → build → persist loop (D-08) |
| Episode fetch at rebuild time | Phase 2 catalog routes (`/episodes` + `/resume`) | MediaProvider (Plex/Jellyfin) | Reuse existing live fetch contract |
| Rebuild output persistence | DB: `rebuild_runs` + snapshots | JSON blob or normalized episode rows | D-15 full snapshot; D-16 last 3 runs |
| Job state tracking | DB: `rebuild_runs.status` enum | — | D-09 queued/running/succeeded/failed/partial |
| Failure isolation | Orchestrator try/catch per series | — | D-11 row skip; D-12 fail if all excluded; D-13 provider check |
| Manual rebuild trigger | `POST /playlists/{id}/rebuild` | Orchestrator function | D-06 same pipeline; async Celery defer if needed (planner discretion) |
| Playlist list/detail SPA | Frontend `/playlists` routes | TanStack Query | D-19–D-21 minimal UI; Phase 3 design system |
| Status badge + polling | Frontend badge component | TanStack Query refetchInterval | D-21 green/amber/red; poll while running |

## Standard Stack

### Core (existing — no new runtime deps beyond APScheduler)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | ≥3.12 | Backend runtime | Project baseline (`pyproject.toml`) |
| FastAPI | ≥0.115 | API framework + lifespan | Already installed |
| SQLAlchemy | ≥2.0 | ORM for playlists + rebuild state | Phase 1–2 pattern |
| Alembic | ≥1.13 | Schema migrations | Phase 1 pattern |
| Pydantic v2 | (via FastAPI) | Domain models + request validation | Phase 4 `Playlist` domain |
| httpx | ≥0.27 | (Already used by Plex/Jellyfin providers) | Phase 2 |
| structlog | ≥24.0 | Structured logging | Phase 1 |
| **APScheduler** | **3.11.2** `[VERIFIED: PyPI 2026-05-25]` | Cron-style nightly batch | Industry standard for in-process scheduling |

### Supporting (new frontend deps — if not already installed in Phase 3)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| TanStack Query | (v4/v5 — check Phase 3) | Async state + cache | Playlist CRUD mutations + polling |
| TanStack Router | (Phase 3 uses react-router-dom) | SPA routing | `/playlists` and `/playlists/:id` routes |
| shadcn/ui | (Phase 3 installed) | Badge, Dialog, Select, RadioGroup, Input | Status badge, create/edit forms |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler in-process | Celery + Redis worker | More complexity; defer unless scale demands (deferred ideas) |
| CronTrigger UTC | Per-playlist timezone | D-01 global 04:00 UTC only; user-local time deferred |
| AsyncIOScheduler | BlockingScheduler | FastAPI is async; AsyncIO scheduler runs on same event loop |
| Snapshot JSON blob | Normalized episode rows | JSON simpler for D-15 full snapshot; normalized if querying snapshots needed |
| TanStack Query | SWR / React Query v3 | TanStack Query v4/v5 is Phase 3 baseline |

**Installation:**

```bash
cd backend && uv add apscheduler
```

**Version verification:** APScheduler 3.11.2 via `pip index versions apscheduler` (2026-05-25).

## Package Legitimacy Audit

> Phase 5 adds **one new runtime dependency** (APScheduler).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| apscheduler | PyPI | 10+ yrs | very high | github.com/agronholm/apscheduler | unavailable | Approved (industry standard; FastAPI docs cite AsyncIOScheduler) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck unavailable at research time — APScheduler tagged `[ASSUMED]` per registry verification only. Planner may add `checkpoint:human-verify` before install if strict enforcement needed.*

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│ APScheduler (in FastAPI lifespan)                                  │
│   CronTrigger(hour=4, timezone="UTC") → run_nightly_rebuilds()     │
└────────────────────┬───────────────────────────────────────────────┘
                     │ scheduled job invokes
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│ Orchestrator: run_nightly_rebuilds()                               │
│  1. Load due playlists (cadence + last_rebuild_at filter)          │
│  2. For each due playlist (sequential D-08):                        │
│      a. Create RebuildRun (status=queued → running)                 │
│      b. For each row: fetch episodes + on_deck via catalog API      │
│      c. Call PlaylistBuilder.build(playlist, inputs, rebuild_seed)  │
│      d. On success: persist snapshot (D-15), update status          │
│      e. On failure: log error, mark run failed (D-17)               │
│  3. Failure isolation (D-11–D-14): row skip / provider check        │
└────────────────────┬───────────────────────────────────────────────┘
                     │ calls existing Phase 4
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│ PlaylistBuilder.build() — pure domain (Phase 4)                    │
│   Returns: PlaylistBuildResult (episodes, row_outcomes, day_key)   │
└────────────────────┬───────────────────────────────────────────────┘
                     │ reads from
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│ catalog.py: GET /episodes + /resume (Phase 2)                      │
│   MediaProvider (Plex/Jellyfin) → live episode snapshots            │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ Frontend: /playlists routes (Phase 5 SPA)                          │
│   List → GET /api/v1/playlists (status badge per D-21)             │
│   Detail → GET /api/v1/playlists/{id} (output + last run)          │
│   Rebuild → POST /api/v1/playlists/{id}/rebuild (manual trigger)   │
└────────────────────┬───────────────────────────────────────────────┘
                     │ REST API
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│ FastAPI routes: /api/v1/playlists (CRUD + rebuild endpoint)        │
│   POST /playlists → create playlist                                 │
│   PUT /playlists/{id} → update config                               │
│   DELETE /playlists/{id} → soft-delete or cascade                   │
│   POST /playlists/{id}/rebuild → manual orchestrator call (D-06)   │
│   GET /playlists → list + status                                    │
│   GET /playlists/{id} → detail + last 3 runs (D-16)                │
└────────────────────┬───────────────────────────────────────────────┘
                     │ persists to
                     ▼
┌────────────────────────────────────────────────────────────────────┐
│ DB tables (SQLAlchemy + Alembic):                                  │
│   - playlists (id, app_user_id, name, episode_count, cadence, …)   │
│   - playlist_series_rows (playlist_id, series_id, mode, policy, …) │
│   - rebuild_runs (id, playlist_id, status, error_msg, created_at)  │
│   - rebuild_snapshots (run_id, snapshot_json or normalized rows)    │
└────────────────────────────────────────────────────────────────────┘
```

**Data flow:** Nightly cron → orchestrator queries due playlists → fetch live episodes per row → call builder → persist snapshot + state → API serves to SPA → user sees status badge + output list.

### Recommended Project Structure

```
backend/src/wheeloffish/
├── core/
│   ├── orchestrator.py          # NEW: run_nightly_rebuilds, run_manual_rebuild
│   ├── playlist_cadence.py      # NEW: is_due(playlist, now) per D-02–D-04
│   └── playlist/                # Phase 4 (existing)
│       └── builder.py
├── db/models/
│   ├── playlist.py              # NEW: Playlist ORM
│   ├── playlist_series_row.py  # NEW: PlaylistSeriesRow ORM
│   ├── rebuild_run.py           # NEW: RebuildRun ORM + RebuildStatus enum
│   └── rebuild_snapshot.py      # NEW: snapshot storage (or JSON on rebuild_run)
├── api/routes/
│   └── playlists.py             # NEW: CRUD + rebuild endpoints
├── api/schemas/
│   └── playlist.py              # NEW: request/response DTOs
└── main.py                       # MODIFY: add scheduler lifespan, include playlists router

backend/alembic/versions/
└── 008_playlists_rebuilds.py    # NEW migration (D-23 + D-15)

frontend/src/
├── api/
│   └── playlists.ts             # NEW: fetch/create/update/rebuild mutations
├── pages/
│   ├── PlaylistListPage.tsx    # NEW: /playlists
│   ├── PlaylistCreatePage.tsx  # NEW: /playlists/new
│   └── PlaylistDetailPage.tsx  # NEW: /playlists/:id
├── components/playlists/
│   ├── PlaylistCard.tsx         # NEW: card + status badge
│   ├── PlaylistForm.tsx         # NEW: create/edit form (D-26 advanced settings)
│   ├── PlaylistOutput.tsx       # NEW: ordered episode list from snapshot
│   └── StatusBadge.tsx          # NEW: green/amber/red per D-21
└── App.tsx                       # MODIFY: add /playlists routes
```

### Pattern 1: APScheduler in FastAPI lifespan (D-07)

**What:** Initialize AsyncIOScheduler in lifespan context manager, add CronTrigger job, start before yield, shutdown after yield.

**When to use:** Single-service deployment (D-07); global 04:00 UTC cron (D-01).

```python
# backend/src/wheeloffish/main.py (modify existing lifespan)
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from wheeloffish.core.orchestrator import run_nightly_rebuilds
from wheeloffish.core.config import Settings, get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    session_factory = get_session_factory(settings)
    db = session_factory()
    try:
        sync_connection_from_env(db, settings)
    finally:
        db.close()
    get_logger("wheeloffish").info("application_startup", environment=settings.ENVIRONMENT)
    
    # NEW: APScheduler setup
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Parse cron from env: "04:00" → hour=4, minute=0
    cron_hour, cron_minute = parse_cron_time(settings.WOF_REBUILD_CRON_UTC)
    scheduler.add_job(
        run_nightly_rebuilds,
        trigger=CronTrigger(hour=cron_hour, minute=cron_minute, timezone="UTC"),
        id="nightly_rebuilds",
        name="Nightly playlist rebuilds",
        max_instances=1,  # D-08 sequential processing
        coalesce=True,    # D-05 skip missed executions
        misfire_grace_time=None,  # D-05 no catch-up
    )
    scheduler.start()
    get_logger("wheeloffish").info("scheduler_started", cron_hour=cron_hour, cron_minute=cron_minute)
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown(wait=True)
    get_logger("wheeloffish").info("scheduler_shutdown")
```

**Cron parsing helper:**

```python
def parse_cron_time(cron_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' UTC time string into (hour, minute)."""
    hour, minute = cron_str.split(":")
    return int(hour), int(minute)
```

**Env config (add to Settings):**

```python
# backend/src/wheeloffish/core/config.py
class Settings(BaseSettings):
    # ... existing fields
    WOF_REBUILD_CRON_UTC: str = "04:00"  # D-01 default
```

### Pattern 2: Orchestrator function (D-08 sequential, D-11–D-14 failure isolation)

**What:** Single async function invoked by APScheduler; loads due playlists, calls builder, persists results.

**When to use:** Every scheduled job and manual rebuild endpoint.

```python
# backend/src/wheeloffish/core/orchestrator.py
from wheeloffish.core.playlist.builder import PlaylistBuilder
from wheeloffish.db.models.playlist import Playlist as PlaylistORM
from wheeloffish.db.models.rebuild_run import RebuildRun, RebuildStatus
from wheeloffish.domain.playlist import Playlist, SeriesRebuildInput
from wheeloffish.core.playlist_cadence import is_due
from wheeloffish.api.routes.catalog import _fetch_resume_data, _cached_series_context
from sqlalchemy.orm import Session
import structlog
from datetime import datetime, UTC

logger = structlog.get_logger("wheeloffish.orchestrator")

async def run_nightly_rebuilds():
    """Nightly job: rebuild all due playlists (D-08 sequential)."""
    db = get_session_factory(get_settings())()
    try:
        now = datetime.now(UTC)
        due_playlists = (
            db.query(PlaylistORM)
            .filter(PlaylistORM.deleted_at.is_(None))
            .all()
        )
        due_playlists = [p for p in due_playlists if is_due(p, now)]
        
        logger.info("nightly_rebuild_start", due_count=len(due_playlists))
        
        for playlist_orm in due_playlists:
            await rebuild_playlist(db, playlist_orm.id, scheduled=True)
    finally:
        db.close()

async def rebuild_playlist(db: Session, playlist_id: str, scheduled: bool = False) -> RebuildRun:
    """Core orchestrator: load config → fetch inputs → build → persist (D-06 shared)."""
    playlist_orm = db.query(PlaylistORM).filter(PlaylistORM.id == playlist_id).one()
    
    # Create RebuildRun
    run = RebuildRun(
        playlist_id=playlist_id,
        status=RebuildStatus.QUEUED,
        scheduled=scheduled,
    )
    db.add(run)
    db.commit()
    
    try:
        run.status = RebuildStatus.RUNNING
        db.commit()
        
        # Convert ORM → Pydantic domain
        playlist = orm_to_pydantic(playlist_orm)
        
        # Fetch live episode inputs per row (D-11 row-level try/catch)
        inputs = []
        row_errors = []
        for row in playlist.rows:
            try:
                episodes, on_deck = await fetch_row_episodes(db, playlist_orm.app_user_id, row.series_id)
                inputs.append(SeriesRebuildInput(series_id=row.series_id, episodes=episodes, on_deck=on_deck))
            except ProviderError as e:
                logger.warning("row_fetch_failed", series_id=row.series_id, error=str(e))
                row_errors.append((row.series_id, str(e)))
                # D-11: skip row, continue
        
        # D-13 provider entirely unreachable check (all rows failed)
        if row_errors and len(row_errors) == len(playlist.rows):
            raise ProviderError("All series failed to fetch — provider unreachable")
        
        # Call builder
        rebuild_seed = datetime.now(UTC).strftime("%Y-%m-%d")
        result = PlaylistBuilder.build(playlist, inputs, rebuild_seed)
        
        # D-12 / D-14 empty output guard
        if result.slots_filled == 0:
            run.status = RebuildStatus.FAILED
            run.error_message = "No episodes emitted — all rows excluded or empty snapshots"
            db.commit()
            return run
        
        # Persist snapshot (D-15, D-16 rolling last 3)
        persist_snapshot(db, run.id, result)
        prune_old_snapshots(db, playlist_id, keep=3)
        
        # D-11 partial if row errors
        run.status = RebuildStatus.PARTIAL if row_errors else RebuildStatus.SUCCEEDED
        run.completed_at = datetime.now(UTC)
        db.commit()
        
        logger.info("rebuild_success", playlist_id=playlist_id, status=run.status.value)
        return run
    
    except Exception as e:
        run.status = RebuildStatus.FAILED
        run.error_message = str(e)
        run.completed_at = datetime.now(UTC)
        db.commit()
        logger.error("rebuild_failed", playlist_id=playlist_id, error=str(e))
        return run
```

**Helper: cadence evaluation (D-02–D-04):**

```python
# backend/src/wheeloffish/core/playlist_cadence.py
from wheeloffish.db.models.playlist import Playlist, RefreshCadence
from datetime import datetime

def is_due(playlist: Playlist, now: datetime) -> bool:
    """Evaluate if playlist is due for rebuild at `now` (D-03)."""
    if playlist.refresh_cadence == RefreshCadence.DAILY:
        return True
    
    # Weekly: check day of week (0=Mon, 6=Sun)
    if playlist.refresh_cadence == RefreshCadence.WEEKLY:
        return now.weekday() == playlist.refresh_day_of_week
    
    return False
```

### Pattern 3: DB schema (D-23, D-09, D-15–D-16)

**What:** 4 new tables mirroring Phase 4 domain + rebuild state + snapshots.

**When to use:** Alembic migration Wave 0.

```python
# backend/alembic/versions/008_playlists_rebuilds.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON  # or postgresql.JSONB

revision = "008_playlists_rebuilds"
down_revision = "007_cached_series_composite_pk"

def upgrade() -> None:
    # D-24 cadence enum
    op.execute("CREATE TYPE refresh_cadence AS ENUM ('daily', 'weekly')")
    op.execute("CREATE TYPE rebuild_status AS ENUM ('queued', 'running', 'succeeded', 'failed', 'partial')")
    op.execute("CREATE TYPE row_mode AS ENUM ('ordered', 'disordered')")
    op.execute("CREATE TYPE completion_policy AS ENUM ('remove', 'restart', 'disordered')")
    op.execute("CREATE TYPE slot_allocation AS ENUM ('wild', 'balanced', 'round_robin')")
    
    # Playlists table (D-23)
    op.create_table(
        "playlists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("app_user_id", sa.String(36), sa.ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("episode_count", sa.Integer, nullable=False, default=20),
        sa.Column("slot_allocation", sa.Enum("wild", "balanced", "round_robin", name="slot_allocation"), nullable=False, server_default="wild"),
        sa.Column("default_completion_policy", sa.Enum("remove", "restart", "disordered", name="completion_policy"), nullable=False, server_default="remove"),
        sa.Column("refresh_cadence", sa.Enum("daily", "weekly", name="refresh_cadence"), nullable=False, server_default="daily"),
        sa.Column("refresh_day_of_week", sa.Integer, nullable=True),  # 0-6 or null
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("ix_playlists_app_user", "app_user_id", "deleted_at"),
    )
    
    # Series rows (D-23, D-26)
    op.create_table(
        "playlist_series_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("playlist_id", sa.String(36), sa.ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("series_id", sa.String(512), nullable=False),  # composite id from catalog
        sa.Column("mode", sa.Enum("ordered", "disordered", name="row_mode"), nullable=False, server_default="ordered"),
        sa.Column("completion_policy", sa.Enum("remove", "restart", "disordered", name="completion_policy"), nullable=True),  # null = use playlist default
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index("ix_playlist_series_rows_playlist", "playlist_id"),
    )
    
    # Rebuild runs (D-09, D-16)
    op.create_table(
        "rebuild_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("playlist_id", sa.String(36), sa.ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("queued", "running", "succeeded", "failed", "partial", name="rebuild_status"), nullable=False),
        sa.Column("scheduled", sa.Boolean, nullable=False, default=False),  # D-06 scheduled vs manual
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Index("ix_rebuild_runs_playlist_created", "playlist_id", "created_at"),
    )
    
    # Rebuild snapshots (D-15 — planner chooses JSON vs normalized)
    op.create_table(
        "rebuild_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("rebuild_runs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("snapshot_json", JSON, nullable=False),  # PlaylistBuildResult as JSON
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("rebuild_snapshots")
    op.drop_table("rebuild_runs")
    op.drop_table("playlist_series_rows")
    op.drop_table("playlists")
    op.execute("DROP TYPE slot_allocation")
    op.execute("DROP TYPE completion_policy")
    op.execute("DROP TYPE row_mode")
    op.execute("DROP TYPE rebuild_status")
    op.execute("DROP TYPE refresh_cadence")
```

**SQLAlchemy models:**

```python
# backend/src/wheeloffish/db/models/playlist.py
from enum import StrEnum
from sqlalchemy import String, Integer, Enum as SAEnum, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from wheeloffish.db.models.base import Base
from datetime import datetime, UTC

class RefreshCadence(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"

class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        Index("ix_playlists_app_user", "app_user_id", "deleted_at"),
    )
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    app_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    slot_allocation: Mapped[str] = mapped_column(String, nullable=False, default="wild")
    default_completion_policy: Mapped[str] = mapped_column(String, nullable=False, default="remove")
    refresh_cadence: Mapped[RefreshCadence] = mapped_column(SAEnum(RefreshCadence), nullable=False, default=RefreshCadence.DAILY)
    refresh_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    rows: Mapped[list["PlaylistSeriesRow"]] = relationship("PlaylistSeriesRow", back_populates="playlist", cascade="all, delete-orphan")
    rebuild_runs: Mapped[list["RebuildRun"]] = relationship("RebuildRun", back_populates="playlist")
```

### Pattern 4: REST API (CRUD + manual rebuild D-06, D-22)

**What:** FastAPI routes for playlist CRUD + `POST /playlists/{id}/rebuild`.

**When to use:** All SPA interactions.

```python
# backend/src/wheeloffish/api/routes/playlists.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from wheeloffish.api.deps import get_db, get_app_user_id
from wheeloffish.db.models.playlist import Playlist as PlaylistORM
from wheeloffish.api.schemas.playlist import PlaylistCreateRequest, PlaylistResponse, PlaylistDetailResponse
from wheeloffish.core.orchestrator import rebuild_playlist
import uuid

router = APIRouter(prefix="/playlists", tags=["playlists"])

@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(
    body: PlaylistCreateRequest,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> PlaylistResponse:
    """Create new playlist (D-23, D-24, D-25)."""
    playlist = PlaylistORM(
        id=str(uuid.uuid4()),
        app_user_id=app_user_id,
        name=body.name,
        episode_count=body.episode_count,
        refresh_cadence=body.refresh_cadence,
        refresh_day_of_week=body.refresh_day_of_week,
        # ... other fields from body
    )
    db.add(playlist)
    # Add rows
    for row_data in body.rows:
        row = PlaylistSeriesRow(id=str(uuid.uuid4()), playlist_id=playlist.id, **row_data.model_dump())
        db.add(row)
    db.commit()
    return orm_to_response(playlist)

@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
def get_playlist_detail(
    playlist_id: str,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> PlaylistDetailResponse:
    """Fetch playlist config + last 3 runs (D-16, D-17)."""
    playlist = db.query(PlaylistORM).filter(
        PlaylistORM.id == playlist_id,
        PlaylistORM.app_user_id == app_user_id,
        PlaylistORM.deleted_at.is_(None),
    ).one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Load last 3 runs
    runs = (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist_id)
        .order_by(RebuildRun.created_at.desc())
        .limit(3)
        .all()
    )
    return PlaylistDetailResponse(
        playlist=orm_to_response(playlist),
        last_runs=[run_to_response(r) for r in runs],
    )

@router.post("/{playlist_id}/rebuild", status_code=status.HTTP_202_ACCEPTED)
async def manual_rebuild(
    playlist_id: str,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
):
    """Manual rebuild trigger (D-06, D-22 owner-only)."""
    playlist = db.query(PlaylistORM).filter(
        PlaylistORM.id == playlist_id,
        PlaylistORM.app_user_id == app_user_id,
        PlaylistORM.deleted_at.is_(None),
    ).one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # D-06: same pipeline as scheduled
    await rebuild_playlist(db, playlist_id, scheduled=False)
    return {"status": "accepted"}
```

### Pattern 5: SPA vertical slice (Phase 3 pattern, D-19–D-21)

**What:** One page per route, TanStack Query hooks, shadcn forms.

**When to use:** All playlist UI.

```tsx
// frontend/src/pages/PlaylistListPage.tsx
import { useQuery } from "@tanstack/react-query"
import { fetchPlaylists } from "@/api/playlists"
import { PlaylistCard } from "@/components/playlists/PlaylistCard"

export function PlaylistListPage() {
  const { data: playlists, isLoading } = useQuery({
    queryKey: ["playlists"],
    queryFn: fetchPlaylists,
  })
  
  if (isLoading) return <div>Loading playlists...</div>
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {playlists?.map((p) => <PlaylistCard key={p.id} playlist={p} />)}
    </div>
  )
}
```

**Status badge component (D-21):**

```tsx
// frontend/src/components/playlists/StatusBadge.tsx
import { Badge } from "@/components/ui/badge"

type RebuildStatus = "succeeded" | "partial" | "failed" | "running" | "never"

export function StatusBadge({ status }: { status: RebuildStatus }) {
  const variants = {
    succeeded: "default",  // green
    partial: "secondary",  // amber
    failed: "destructive", // red
    running: "outline",
    never: "outline",
  } as const
  
  return <Badge variant={variants[status]}>{status}</Badge>
}
```

**Polling while running (D-21):**

```tsx
// frontend/src/api/playlists.ts
import { useQuery } from "@tanstack/react-query"

export function usePlaylistStatus(playlistId: string) {
  const { data: playlist } = useQuery({
    queryKey: ["playlists", playlistId],
    queryFn: () => fetchPlaylist(playlistId),
    refetchInterval: (data) => {
      return data?.last_run?.status === "running" ? 5000 : false
    },
  })
  return playlist
}
```

### Anti-Patterns to Avoid

- **Starting scheduler before DB migrations run:** Lifespan startup order matters — sync DB schema first.
- **Global RNG or unseeded day_key:** Builder requires deterministic seed; orchestrator passes ISO date string.
- **Catch-up pile-up (D-05):** Do not use `misfire_grace_time` — set to `None` so missed runs skip cleanly.
- **Hammering provider on failure (D-13):** Check provider reachable once per night; skip all rebuilds if unreachable.
- **Wiping last good snapshot on failure (D-17):** Failed runs store error only; snapshot unchanged.
- **Inline HTML/Markdown in error_message:** Structured log + plain text; SPA renders safely.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron scheduling | Custom sleep loop + threading | APScheduler AsyncIOScheduler | Handles DST, misfire grace, concurrency, shutdown |
| Job state tracking | Ad-hoc status flags | Enum + DB persistence (D-09) | Standardized terminal states, audit trail |
| Episode fetch at rebuild time | Custom HTTP client | Phase 2 catalog routes + MediaProvider | Already handles auth, rate limiting, on-deck |
| Playlist domain validation | Manual field checks | Pydantic models from Phase 4 | `Field(ge=1)` constraints, enum validation |
| SPA routing | Regex + switch statements | TanStack Router / react-router-dom | Phase 3 baseline |
| Status polling | setInterval in component | TanStack Query refetchInterval | Automatic cache invalidation, backoff |

**Key insight:** Phase 5 is composition — APScheduler for cron, Phase 2 for episode fetches, Phase 4 for build logic, Phase 3 for SPA patterns. The only new logic is orchestrator loop + failure isolation (D-11–D-14).

## Common Pitfalls

### Pitfall 1: Scheduler restarts with `running` jobs (startup handling)

**What goes wrong:** Container restart leaves `rebuild_runs.status = running`; scheduler doesn't recover.

**Why it happens:** No startup cleanup query.

**How to avoid:** In lifespan startup (before scheduler.start), query `running` jobs and mark them `failed`:

```python
db.query(RebuildRun).filter(RebuildRun.status == RebuildStatus.RUNNING).update(
    {"status": RebuildStatus.FAILED, "error_message": "Interrupted by restart"}
)
db.commit()
```

**Warning signs:** UI shows perpetual "running" badge after pod restart.

### Pitfall 2: Missed cron window → retry storm (D-05 violation)

**What goes wrong:** Container down at 04:00 UTC; scheduler attempts catch-up on next boot.

**Why it happens:** Default APScheduler `misfire_grace_time` allows stale runs.

**How to avoid:** Set `misfire_grace_time=None` and `coalesce=True` in `add_job` (Pattern 1).

**Warning signs:** Multiple nightly runs trigger in quick succession after downtime.

### Pitfall 3: Provider fetch failure aborts entire rebuild (D-11 violation)

**What goes wrong:** One series 404 causes whole playlist to fail.

**Why it happens:** No try/catch per row in orchestrator.

**How to avoid:** Pattern 2 wraps each `fetch_row_episodes` in try/except; append to `row_errors` list; D-11 skip row.

**Warning signs:** Playlist with 5 series fails because 1 series is unavailable.

### Pitfall 4: Empty snapshot treated as success (CR-01 / D-14 violation)

**What goes wrong:** Builder returns `slots_filled=0`; orchestrator marks success; last good output lost.

**Why it happens:** No empty guard in orchestrator.

**How to avoid:** Pattern 2 checks `result.slots_filled == 0` → mark `FAILED`, keep last snapshot (D-17).

**Warning signs:** Playlist output disappears after all rows excluded.

### Pitfall 5: Manual rebuild suppresses next scheduled run (D-06 violation)

**What goes wrong:** User clicks "Rebuild now"; next nightly cron doesn't run.

**Why it happens:** Cadence evaluation checks `last_rebuild_at` without distinguishing scheduled vs manual.

**How to avoid:** Cadence filter ignores manual runs (check `rebuild_runs.scheduled=True` only).

**Warning signs:** Daily playlist stops rebuilding after manual trigger.

### Pitfall 6: Snapshot pruning deletes current output (D-16 violation)

**What goes wrong:** Keep-last-3 logic prunes the wrong runs.

**Why it happens:** Sorting by `created_at` instead of `completed_at`; or deleting before new snapshot committed.

**How to avoid:** Prune **after** new snapshot persisted; order by `completed_at.desc()` and keep top 3 `succeeded` or `partial` runs only.

**Warning signs:** Playlist shows no output after successful rebuild.

### Pitfall 7: Cross-user rebuild (D-22 violation)

**What goes wrong:** Admin rebuilds another user's playlist via manual endpoint.

**Why it happens:** Missing ownership check in `POST /playlists/{id}/rebuild`.

**How to avoid:** Pattern 4 filters by `app_user_id` before rebuild; 404 if not owned.

**Warning signs:** Phase 6 WheelOfFish admin logic leaks into Phase 5.

## Code Examples

### Existing code to reuse

**PlaylistBuilder.build() — Phase 4 contract:**

```67:98:backend/src/wheeloffish/core/playlist/builder.py
class PlaylistBuilder:
    @staticmethod
    def build(
        playlist: Playlist,
        inputs: list[SeriesRebuildInput],
        rebuild_seed: str,
    ) -> PlaylistBuildResult:
        inputs_by_series = {inp.series_id: inp for inp in inputs}

        row_outcomes = []
        for row in playlist.rows:
            inp = inputs_by_series.get(row.series_id)
            episodes = inp.episodes if inp is not None else []
            on_deck = inp.on_deck if inp is not None else None
            completion_event = evaluate_completion(row, episodes, on_deck)
            row_outcomes.append(apply_policy(row, completion_event))

        active_series_ids = [
            outcome.series_id
            for outcome in row_outcomes
            if not outcome.excluded
        ]

        if not active_series_ids:
            return PlaylistBuildResult(
                episodes=[],
                row_outcomes=row_outcomes,
                day_key=rebuild_seed,
                slots_requested=playlist.episode_count,
                slots_filled=0,
            )
```

**Catalog episode fetch — Phase 2 existing:**

```199:244:backend/src/wheeloffish/api/routes/catalog.py
async def _fetch_resume_data(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> tuple[list[Episode], Episode | None]:
    episodes_coro = _list_episodes(
        provider,
        series_id,
        rating_key=rating_key,
        library_native_id=library_native_id,
    )
    on_deck_coro = _get_on_deck_episode(
        provider,
        series_id,
        rating_key=rating_key,
        library_native_id=library_native_id,
    )

    episodes_result, on_deck_result = await asyncio.gather(
        episodes_coro,
        on_deck_coro,
        return_exceptions=True,
    )

    episodes: list[Episode] = []
    on_deck: Episode | None = None

    if isinstance(episodes_result, BaseException):
        if not isinstance(on_deck_result, BaseException):
            on_deck = on_deck_result
        elif isinstance(episodes_result, ProviderError):
            raise episodes_result
        else:
            raise ProviderError(str(episodes_result)) from episodes_result
    else:
        episodes = episodes_result

    if isinstance(on_deck_result, BaseException):
        if not isinstance(on_deck_result, ProviderError):
            raise ProviderError(str(on_deck_result)) from on_deck_result
    else:
        on_deck = on_deck_result

    return episodes, on_deck
```

**Settings pattern — Phase 1:**

```8:51:backend/src/wheeloffish/core/config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    WOF_SECRET_KEY: str = Field(..., min_length=64, max_length=64)
    DATABASE_URL: str = "sqlite:////data/wheeloffish.db"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENVIRONMENT: str = "production"
    WOF_PROVIDER: Literal["plex", "jellyfin"] = "plex"
    WOF_MEDIA_SERVER_URL: str = "http://localhost:32400"
    WOF_MEDIA_SERVER_DISPLAY_NAME: str = "Media Server"
    WOF_VERIFY_SSL: bool = True
    WOF_ADMIN_PROVIDER_USER_ID: str = ""
    WOF_ADMIN_USERNAME: str = ""
    WOF_SESSION_DAYS: int | None = None
    WOF_ENABLED_PROVIDERS: str = "plex,jellyfin"
    WOF_PLEX_PRODUCT_NAME: str = "Wheel of Fish TV"
    WOF_OAUTH_CALLBACK_BASE: str = "http://localhost:8000"
    WOF_CATALOG_SYNC_CHUNK_SIZE: int = 500
    WOF_CATALOG_PAGE_DEFAULT: int = 50
    WOF_SCOPED_LIBRARY_IDS: str = ""
    WOF_ARTWORK_CACHE_DIR: str = "/data/artwork"
    WOF_ARTWORK_CACHE_TTL_DAYS: int = 30
    SPA_DIST_DIR: str = "/app/static/spa"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enabled_providers_set(self) -> set[str]:
        legacy = {p.strip() for p in self.WOF_ENABLED_PROVIDERS.split(",") if p.strip()}
        if len(legacy) > 1:
            return legacy
        return {self.WOF_PROVIDER}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def session_max_age_seconds(self) -> int | None:
        if self.WOF_SESSION_DAYS is None:
            return None
        return self.WOF_SESSION_DAYS * 86400
```

**SQLAlchemy model pattern — Phase 2:**

```16:53:backend/src/wheeloffish/db/models/cached_series.py
class CachedSeries(Base):
    __tablename__ = "cached_series"
    __table_args__ = (
        UniqueConstraint(
            "app_user_id",
            "connection_id",
            "native_id",
            name="uq_cached_series_user_connection_native",
        ),
    )

    id: Mapped[str] = mapped_column(String(512), primary_key=True)
    app_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    library_native_id: Mapped[str] = mapped_column(String(128), nullable=False)
    native_id: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_sort: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    app_user: Mapped[AppUser] = relationship("AppUser")
    connection: Mapped[Connection] = relationship("Connection", back_populates="cached_series")
```

**Alembic migration pattern — Phase 2:**

```1:24:backend/alembic/versions/007_cached_series_composite_pk.py
"""Composite primary key on cached_series for per-user rows sharing series ids."""

import sqlalchemy as sa

from alembic import op

revision = "007_cached_series_composite_pk"
down_revision = "006_per_user_libraries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cached_series", recreate="always") as batch:
        batch.create_primary_key(
            "pk_cached_series_app_user_id",
            ["app_user_id", "id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("cached_series", recreate="always") as batch:
        batch.create_primary_key("pk_cached_series", ["id"])
```

**Frontend SPA routing — Phase 3:**

```26:49:frontend/src/App.tsx
function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route element={<LibraryScopeGuard />}>
            <Route path="/browse" element={<BrowsePage />} />
            <Route path="/series" element={<SeriesDetailPage />} />
            <Route path="/series/:seriesId" element={<SeriesDetailPage />} />
          </Route>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/setup/admin" element={<AdminSetupPage />} />
          <Route element={<AdminRoute />}>
            <Route path="/setup/libraries" element={<AdminLibrarySetupPage />} />
            <Route path="/settings/libraries" element={<SettingsLibrariesPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
```

### Orchestrator pseudocode with all D- decision points

```python
async def run_nightly_rebuilds():
    # D-01: global 04:00 UTC cron trigger invokes this
    db = get_session()
    now = datetime.now(UTC)
    
    # D-03: filter playlists due tonight (cadence + last_rebuild)
    due_playlists = [p for p in all_playlists if is_due(p, now)]
    
    # D-08: sequential processing (no parallelization)
    for playlist in due_playlists:
        try:
            # D-09: create RebuildRun, status=queued → running
            run = RebuildRun(playlist_id=playlist.id, status="queued")
            db.add(run)
            db.commit()
            
            run.status = "running"
            db.commit()
            
            # D-13: provider reachability check
            if not await provider_reachable():
                mark_all_failed(db, "Provider unreachable")
                break
            
            # Fetch inputs per row
            inputs = []
            row_errors = []
            for row in playlist.rows:
                try:
                    episodes, on_deck = await fetch_row_episodes(row.series_id)
                    # D-14: CR-01 empty snapshot guard
                    if not episodes:
                        row_errors.append((row.series_id, "empty_snapshot"))
                        continue  # D-11: skip row, continue
                    inputs.append(SeriesRebuildInput(series_id=row.series_id, episodes=episodes, on_deck=on_deck))
                except ProviderError as e:
                    row_errors.append((row.series_id, str(e)))
                    # D-11: skip row, continue
            
            # D-12: all rows excluded → fail, keep last good snapshot
            if not inputs:
                run.status = "failed"
                run.error_message = "All rows excluded"
                db.commit()
                continue
            
            # Call Phase 4 builder
            rebuild_seed = now.strftime("%Y-%m-%d")
            result = PlaylistBuilder.build(playlist, inputs, rebuild_seed)
            
            # D-15: persist full snapshot (episodes + metadata)
            persist_snapshot(db, run.id, result)
            
            # D-16: prune old snapshots (keep last 3)
            prune_old_snapshots(db, playlist.id, keep=3)
            
            # D-11: partial if row errors
            run.status = "partial" if row_errors else "succeeded"
            run.completed_at = now
            db.commit()
        
        except Exception as e:
            # D-17: failed attempts store error only, last good snapshot unchanged
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = now
            db.commit()
            # D-10: no automatic retry — next due window tries again

# D-06: manual rebuild uses same pipeline
async def manual_rebuild(playlist_id: str):
    # Same logic as scheduled, but `RebuildRun.scheduled=False`
    # Does NOT suppress next scheduled run (cadence unaffected)
    pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| APScheduler 3.x BackgroundScheduler | AsyncIOScheduler with FastAPI lifespan | 2023+ FastAPI patterns | No threading; same event loop as Uvicorn |
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93+ | Mandatory migration path |
| Manual job state tracking | Enum + SQLAlchemy model | Industry standard (Airflow, SkyPilot) | Standardized terminal states |
| Catch-up on missed cron | D-05 explicit skip | Project decision | No pile-up after downtime |

**Deprecated/outdated:**
- `fastapi_utils.tasks.repeat_every` — incompatible with lifespan; use APScheduler instead
- SQLAlchemy 1.x `sa.Column()` — Phase 1–2 use 2.0 `Mapped[]` + `mapped_column()`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | APScheduler 3.11.2 AsyncIOScheduler is standard for FastAPI | Standard Stack | Newer 4.x incompatible API; 3.x stable 2026 |
| A2 | Snapshot as JSON blob simpler than normalized rows | Pattern 3 | Normalized rows needed if querying snapshots (planner discretion) |
| A3 | Sequential playlist rebuilds (D-08) finish within nightly window | Summary | 1000+ playlists might exceed window; parallelization deferred Phase 6+ |
| A4 | Global 04:00 UTC cron sufficient (D-01) | Pattern 1 | Per-playlist clock time deferred; env-configurable covers |
| A5 | Phase 3 installed TanStack Query v4/v5 | Standard Stack | Verify in frontend package.json; v3 incompatible |
| A6 | SQLite enum support via VARCHAR | Pattern 3 | PostgreSQL native enum; SQLite stores as string (acceptable D-07) |
| A7 | Manual rebuild via sync endpoint acceptable (D-06) | Pattern 4 | Async Celery defer if rebuild >30s; planner discretion |
| A8 | D-05 no catch-up explicit | Pitfall 2 | User may expect nightly catch-up; document in WEB-01 tooltip |

## Open Questions

1. **Snapshot storage: JSON blob vs normalized rows?**
   - What we know: D-15 requires full snapshot; D-16 last 3 runs.
   - What's unclear: Query snapshots for analytics (Phase 7)?
   - Recommendation: Start with JSON blob (simpler); normalized rows if Phase 7 needs historical queries.

2. **Manual rebuild async or sync endpoint?**
   - What we know: D-06 same pipeline as scheduled; UI expects 202 Accepted.
   - What's unclear: Rebuild duration — 5s or 60s?
   - Recommendation: Start sync (Pattern 4); add Celery task if planner sees >30s rebuilds in testing.

3. **Startup `running` job recovery: mark failed or retry?**
   - What we know: Pitfall 1 needs cleanup.
   - Recommendation: Mark failed with "Interrupted by restart" message (D-17 error only); next due window retries (D-10).

4. **Amber vs red threshold for partial (D-09 discretion)?**
   - What we know: D-11 row skip → partial; all excluded → failed.
   - Recommendation: Any row skip = amber (partial); zero output = red (failed).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| APScheduler | Nightly cron (D-07) | ✗ (new install) | 3.11.2 | — |
| FastAPI | Lifespan, routes | ✓ | ≥0.115 | — |
| SQLAlchemy | ORM, migrations | ✓ | ≥2.0 | — |
| Alembic | Schema migrations | ✓ | ≥1.13 | — |
| httpx | (Phase 2 providers) | ✓ | ≥0.27 | — |
| TanStack Query | SPA state management | ✓ (Phase 3) | v4/v5 | — |
| shadcn/ui | Badge, Dialog, forms | ✓ (Phase 3) | — | — |

**Missing dependencies with no fallback:**
- APScheduler — install in Wave 0: `cd backend && uv add apscheduler`

**Missing dependencies with fallback:**
- None

## Validation Architecture

> Nyquist validation enabled per `.planning/config.json` `workflow.nyquist_validation: true`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥8.0 + pytest-asyncio ≥0.24 |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd backend && uv run pytest tests/unit/test_orchestrator.py tests/unit/test_playlist_cadence.py -q` |
| Full suite command | `cd backend && uv run ruff check . && uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCH-01 | Nightly cron triggers at 04:00 UTC | integration | Manual (APScheduler lifespan check) | ❌ Wave 0 (scheduler init test) |
| PLT-01 | Create playlist persists to DB | unit | `pytest tests/unit/test_playlist_models.py -k create -x` | ❌ Wave 1 |
| PLT-02 | episode_count persists and validates ≥1 | unit | `pytest tests/unit/test_playlist_models.py -k episode_count -x` | ❌ Wave 1 |
| PLT-03 | Add/remove series rows | unit | `pytest tests/unit/test_playlist_models.py -k series_rows -x` | ❌ Wave 1 |
| D-03 | Cadence filter (daily / weekly DOW) | unit | `pytest tests/unit/test_playlist_cadence.py -x` | ❌ Wave 2 |
| D-11 | Row skip on fetch failure | unit | `pytest tests/unit/test_orchestrator.py -k row_skip -x` | ❌ Wave 3 |
| D-12 | All rows excluded → failed | unit | `pytest tests/unit/test_orchestrator.py -k all_excluded -x` | ❌ Wave 3 |
| D-14 | Empty snapshot → row warning | unit | `pytest tests/unit/test_orchestrator.py -k empty_snapshot -x` | ❌ Wave 3 |
| D-15 | Persist full snapshot | integration | `pytest tests/integration/test_rebuild_e2e.py -k snapshot -x` | ❌ Wave 4 |
| D-16 | Rolling last 3 runs | unit | `pytest tests/unit/test_orchestrator.py -k prune -x` | ❌ Wave 3 |
| WEB-01 | Status badge polling | manual | Manual UAT — SPA status badge green/amber/red | ❌ Wave 5 (SPA vertical slice) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/test_<module>.py -q`
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** Full `uv run pytest` green + manual UAT for SPA status before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_orchestrator.py` — orchestrator loop, failure isolation (D-11–D-14)
- [ ] `tests/unit/test_playlist_cadence.py` — is_due logic per D-02–D-04
- [ ] `tests/unit/test_playlist_models.py` — Pydantic validation, ORM→domain conversion
- [ ] APScheduler lifespan smoke test (scheduler starts, adds job, shuts down cleanly)
- [ ] Install APScheduler: `uv add apscheduler`

## Security Domain

> `security_enforcement` enabled per GSD defaults.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Session auth (Phase 3); `app_user_id` ownership filter (D-18) |
| V3 Session Management | yes | FastAPI SessionMiddleware (Phase 3) |
| V4 Access Control | yes | D-22 owner-only rebuild; filter playlists by `app_user_id` |
| V5 Input Validation | yes | Pydantic `PlaylistCreateRequest`, `Field(ge=1)` on episode_count |
| V6 Cryptography | no | No new secrets; reuse Phase 1 MediaProvider tokens |

### Known Threat Patterns for FastAPI + APScheduler

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unauthorized playlist access (cross-user) | Information Disclosure | Filter by `app_user_id` in all routes (D-18) |
| Manual rebuild CSRF | Tampering | SessionMiddleware CSRF token (Phase 3 existing) |
| SQL injection in playlist name | Tampering | SQLAlchemy parameterized queries |
| Job state race (concurrent manual + scheduled) | Denial of Service | APScheduler `max_instances=1` (Pattern 1) |
| Empty snapshot wipes last good output (CR-01) | Tampering | D-14 + D-17 guards (Pitfall 4) |

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory found in workspace — no additional project-specific enforcement beyond user rules and GSD config (`nyquist_validation: true`, `commit_docs: true`, `project_mode: "mvp"`).

## Sources

### Primary (HIGH confidence)

- APScheduler 3.11.2 PyPI registry verification (2026-05-25) `[VERIFIED: pip index versions]`
- APScheduler official docs: CronTrigger, AsyncIOScheduler, lifespan integration `[CITED: apscheduler.readthedocs.io]`
- FastAPI official docs: lifespan events, context managers `[CITED: fastapi.tiangolo.com/advanced/events]`
- `backend/src/wheeloffish/core/playlist/builder.py` — Phase 4 builder contract `[VERIFIED: codebase]`
- `backend/src/wheeloffish/api/routes/catalog.py` — Phase 2 episode fetch `[VERIFIED: codebase]`
- `backend/src/wheeloffish/db/models/cached_series.py` — SQLAlchemy model pattern `[VERIFIED: codebase]`
- `backend/alembic/versions/007_cached_series_composite_pk.py` — Alembic migration pattern `[VERIFIED: codebase]`
- `frontend/src/App.tsx` — Phase 3 SPA routing `[VERIFIED: codebase]`
- `.planning/phases/05-orchestration-scheduling/05-CONTEXT.md` — D-01 through D-26 locked decisions `[VERIFIED: project docs]`
- `.planning/phases/04-playlist-mathematics/04-RESEARCH.md` — Phase 4 boundary, builder input contract `[VERIFIED: project docs]`

### Secondary (MEDIUM confidence)

- WebSearch: APScheduler + FastAPI lifespan integration patterns (2026 guides) `[CITED: multiple sources]`
- WebSearch: SQLAlchemy enum job state patterns (Airflow, SkyPilot examples) `[CITED: github.com/apache/airflow, github.com/skypilot-org]`
- `.planning/REQUIREMENTS.md` — SCH-01, PLT-01–03, WEB-01 partial `[CITED: project docs]`

### Tertiary (LOW confidence — validate in planner)

- Snapshot JSON blob vs normalized rows (A2)
- Manual rebuild sync vs async endpoint (A7)
- Amber vs red threshold for partial status (D-09 discretion)

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — APScheduler 3.11.2 verified PyPI + FastAPI lifespan standard pattern
- Architecture: **HIGH** — Phase 2 catalog + Phase 4 builder contracts proven; orchestrator is glue
- Pitfalls: **HIGH** — startup recovery (Pitfall 1), D-05 catch-up prevention (Pitfall 2), failure isolation (D-11–D-14) explicitly designed
- SPA patterns: **MEDIUM** — extends Phase 3 baseline; polling + status badge new but TanStack Query standard

**Research date:** 2026-05-25
**Valid until:** 2026-06-25
