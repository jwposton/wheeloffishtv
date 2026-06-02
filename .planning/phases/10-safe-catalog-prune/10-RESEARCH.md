# Phase 10: Safe Catalog Prune — Research

**Researched:** 2026-06-02  
**Domain:** Python/FastAPI backend — SQLAlchemy ORM, Alembic migrations, async orchestration  
**Confidence:** HIGH (codebase read directly; no external package installation required)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Safety policy:**
- D-01: Auto-prune after **3 qualifying evidence events per playlist row**
- D-02: Qualifying evidence (+1): catalog sync absence (series absent from `CachedSeries` for user/connection but row exists) OR rebuild with provider **reachable** and that row returns `empty_snapshot` or `ProviderNotFound`
- D-03: Absence streak starts on first qualifying catalog-sync absence
- D-04: Failed/partial/stalled catalog sync resets counter to 0 for all prune candidates on that connection. Rebuild batch with provider unreachable must not increment any row.
- D-05: Full catalog sync before nightly rebuild for each connection
- D-06: Auto-prune trigger at end of successful catalog sync OR successful rebuild (playlist completed without total provider failure). Delete rows at 3/3 and write audit events.
- D-07: Sub-threshold rows remain non-destructive (existing `fetch_failure`/`empty_snapshot` warnings in `row_outcomes_json`)

**Stale state:**
- D-08: Persist prune state on `playlist_series_rows` (counter, timestamps, last evidence source). No separate prune-state table required unless planner prefers.
- D-09: Internal stale begins after first qualifying evidence (counter ≥ 1). No operator-facing stale badge.
- D-10: Server removal and out-of-scope library absences use same counter rules; distinguish in audit `reason` only.
- D-11: When series reappears (back in cache or rebuild fetch succeeds), clear prune state immediately (counter → 0). Optional `evidence_cleared` audit event.

**Operator visibility:**
- D-12: No prune-specific UI (no Keep, Remove now, snooze, sync-now, stale badges) in Phase 10.
- D-13: Rebuild banner copy unchanged.
- D-14: Silent auto-prune — no toast/banner; row disappears on next load.
- D-15: PRUNE-01 satisfied by not deleting on first miss + existing rebuild warnings until 3/3.

**Audit (PRUNE-03):**
- D-16: `playlist_prune_events` table: `playlist_id`, `series_id`, `event_type`, `reason`, `timestamp`, optional metadata.
- D-17: Log material events only: `auto_pruned`, `manual_removed`, optionally `evidence_cleared`. Do NOT log every +1 tick.
- D-18: Retain last 50 events per playlist; API embed returns most recent 10–20 on playlist detail GET as `recent_prune_events[]`.
- D-19: No dedicated prune UI in Phase 10.

### Claude's Discretion
- Exact column names and migration shape on `playlist_series_rows`
- Whether `manual_removed` is inferred from existing delete endpoint vs explicit event type in handler
- Structlog fields mirroring `auto_pruned` for operators tailing Docker logs
- Ordering of sync-then-rebuild in nightly batch (same connection session vs separate tasks) as long as D-05/D-06 hold

### Deferred Ideas (OUT OF SCOPE)
- Phase 11 diagnostics modal consuming prune event API payload
- Explicit "Sync catalog now" on playlist surfaces
- Operator toasts when auto-prune runs (explicitly rejected — silent removal)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRUNE-01 | Operator sees playlist rows for confidently absent series marked stale (not silently deleted on first failed sync) | Evidence counter (D-01/D-02) prevents first-miss deletion; existing `empty_snapshot`/`fetch_failure` warnings surface stale state until threshold |
| PRUNE-02 | System auto-removes stale playlist rows only after documented safety policy | 3-event counter + reset on failed/partial/stalled sync gate; D-04 reset logic in `run_chunked_sync` exception handlers and `_mark_sync_stale_failed` |
| PRUNE-03 | Operator can audit prune decisions (reason + timestamp) via API | `playlist_prune_events` table + `recent_prune_events[]` embedded in `GET /playlists/{id}` response |
| PRUNE-04 | Rebuild warnings for stale or unfetchable rows remain actionable and non-destructive until prune confidence is met | No behavior change to `fetch_warnings` in `row_outcomes_json`; `empty_snapshot`/`fetch_failure` existing paths unchanged |
</phase_requirements>

---

## Summary

Phase 10 is a pure-backend feature: add a counter-based prune evidence pipeline to the existing playlist rebuild and catalog sync flows. The frontend requires zero changes. The work is well-contained in five existing files plus two new files (core module + ORM model) and one Alembic migration.

The codebase is clean and provides clear hook points. `run_chunked_sync` already purges stale `CachedSeries` rows on successful sync (lines 554–558) — this is the natural trigger for absence detection. `rebuild_playlist` already collects `fetch_warnings` per row including `empty_snapshot` reason codes. The main design challenge is **differentiating `ProviderNotFound` from generic `fetch_failure`** in `fetch_rebuild_inputs_for_row` — currently both return `None` and are labeled "fetch_failure", but D-02 requires only `ProviderNotFound` to count as qualifying rebuild evidence.

A secondary challenge is **nightly batch ordering**: the current `run_nightly_batch` in `orchestrator.py` does only rebuilds; it must now trigger catalog sync per connection before rebuilding that connection's playlists (D-05).

**Primary recommendation:** Add three new columns to `playlist_series_rows` (`absence_count`, `first_absence_at`, `last_absence_at`/`last_evidence_source`) and create a new `playlist_prune_events` audit table, expose both via a thin `core/catalog_prune.py` service, then wire it into the sync and rebuild flows.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Evidence accumulation (catalog sync absence) | API / Backend | — | Post-sync DB query; no provider call needed after sync completes |
| Evidence accumulation (rebuild absent row) | API / Backend | — | Per-row result in `rebuild_playlist`; already has provider context |
| Counter reset on failed sync | API / Backend | — | Exception handlers in `run_chunked_sync` and `_mark_sync_stale_failed` |
| Auto-prune trigger | API / Backend | — | Runs at end of successful sync / successful rebuild |
| Prune state persistence | Database / Storage | — | New columns on `playlist_series_rows`; append-only audit table |
| Audit API embed | API / Backend | — | Embedded in existing `GET /playlists/{id}` via `_playlist_to_detail` |
| Stale UX | — (none) | — | Silent removal per D-12/D-14; no frontend tier involvement |

---

## Standard Stack

### Core (no new packages — all already in project)

| Library | In Use | Purpose | Notes |
|---------|--------|---------|-------|
| SQLAlchemy 2.x | ✓ | ORM + queries | `Mapped`/`mapped_column` pattern already established |
| Alembic | ✓ | Schema migrations | 10 revisions already committed; next is `011_...` |
| FastAPI | ✓ | REST API | Schema embedding via Pydantic |
| Pydantic v2 | ✓ | Response schemas | `BaseModel` with optional fields |
| structlog | ✓ | Structured logging | All modules use `structlog.get_logger(__name__)` |
| pytest + pytest-asyncio | ✓ | Testing | `asyncio_mode = "auto"` in `pyproject.toml` |

**No new packages required.** [VERIFIED: codebase]

---

## Architecture Patterns

### System Architecture Diagram

```
Nightly Batch (run_nightly_batch)
  │
  ├─► FOR each connection:
  │     ├─► await run_chunked_sync(connection_id, app_user_id)
  │     │     ├─► [on complete] record_catalog_sync_absence()  ← NEW
  │     │     │     └─► execute_auto_prune()                  ← NEW
  │     │     └─► [on failure] reset_absence_counters()        ← NEW
  │     │
  │     └─► FOR each due playlist on connection:
  │           └─► await rebuild_playlist(playlist_id)
  │                 ├─► check_provider_reachable(provider) → reachable flag ← NEW
  │                 ├─► FOR each row:
  │                 │     └─► fetch_rebuild_inputs_for_row() → FetchResult ← MODIFIED
  │                 │           ├─► ok → valid_inputs
  │                 │           ├─► empty_snapshot → warning + evidence if reachable ← NEW
  │                 │           ├─► not_found → warning + evidence if reachable    ← NEW
  │                 │           └─► fetch_failure → warning, no evidence
  │                 └─► [on succeed/partial] execute_auto_prune(playlist_id) ← NEW

Manual Rebuild (POST /playlists/{id}/rebuild)
  └─► rebuild_playlist() → same evidence logic (check_provider_reachable inline)

DELETE /playlists/{id}/rows/{series_id}
  └─► write_prune_event(event_type="manual_removed")  ← NEW

GET /playlists/{id}
  └─► _playlist_to_detail() → embed recent_prune_events[]  ← NEW
```

### Recommended Project Structure

```
backend/src/wheeloffish/
├── core/
│   ├── catalog_sync.py          # Modified: hook absence + reset
│   ├── orchestrator.py          # Modified: FetchResult typing, reachable gate, nightly sync
│   ├── catalog_prune.py         # NEW: evidence, reset, auto-prune, audit write
│   └── playlist/
│       └── rebuild_inputs.py    # Modified: FetchResult return type, ProviderNotFound handling
├── db/
│   └── models/
│       ├── playlist_series_row.py    # Modified: 4 new columns
│       ├── playlist_prune_event.py   # NEW: audit table ORM
│       └── __init__.py              # Modified: export new model
└── api/
    ├── routes/
    │   └── playlists.py         # Modified: manual_removed audit, embed recent_prune_events
    └── schemas/
        └── playlists.py         # Modified: PruneEventResponse, PlaylistDetailResponse update

backend/alembic/versions/
└── 011_prune_state_audit.py     # NEW: migration

backend/tests/unit/
└── test_catalog_prune.py        # NEW: unit tests for prune service
```

### Pattern 1: `FetchResult` typed return from `fetch_rebuild_inputs_for_row`

**What:** Replace `SeriesRebuildInput | None` return type with a typed dataclass to distinguish `ProviderNotFound` from generic `fetch_failure`. [ASSUMED — design recommendation, not yet in codebase]

**Why:** Currently `ProviderNotFound` falls into the generic `ProviderError` handler in `_fetch_episodes` and returns `None`, labeled "fetch_failure" in the orchestrator. D-02 requires `ProviderNotFound` to count as qualifying rebuild evidence; generic `fetch_failure` must NOT count.

**When to use:** Only in `rebuild_inputs.py` and `orchestrator.py`.

```python
# Source: rebuild_inputs.py — proposed addition
from dataclasses import dataclass

@dataclass
class FetchResult:
    input: SeriesRebuildInput | None
    reason: str  # "ok" | "empty_snapshot" | "not_found" | "fetch_failure"
```

```python
# In fetch_rebuild_inputs_for_row — catch ProviderNotFound before generic ProviderError:
if isinstance(episodes_result, ProviderNotFound):
    logger.warning("fetch_episodes_not_found", series_id=series_id)
    return FetchResult(input=None, reason="not_found")
if isinstance(episodes_result, ProviderError):
    logger.warning("fetch_episodes_provider_error", series_id=series_id)
    return FetchResult(input=None, reason="fetch_failure")
```

### Pattern 2: Prune Evidence Service (`catalog_prune.py`)

**What:** Centralized service for all prune state mutations — keeps sync and rebuild integrations thin. [ASSUMED — design recommendation]

**Why:** Evidence from two sources (sync, rebuild) with shared reset/prune/audit logic — centralizing avoids duplicating state management.

```python
# backend/src/wheeloffish/core/catalog_prune.py — proposed interface

PRUNE_THRESHOLD = 3  # D-01
MAX_AUDIT_EVENTS_PER_PLAYLIST = 50  # D-18

def record_catalog_sync_absence(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> int:
    """Increment absence_count for all playlist rows whose series_id is absent
    from CachedSeries for this connection/user after a successful full sync.
    Returns count of rows incremented. Called after CachedSeries purge."""
    ...

def record_rebuild_row_absence(
    db: Session,
    row: PlaylistSeriesRow,
    source: str,  # "rebuild"
) -> None:
    """Increment absence_count for a single row (provider reachable + not_found/empty_snapshot)."""
    ...

def clear_prune_state_for_recovered(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> None:
    """Reset counter to 0 for rows whose series IS now present in CachedSeries.
    Called after successful sync so recovered series are un-staled."""
    ...

def reset_absence_counters_for_connection(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> None:
    """Reset absence_count=0 for all playlist rows on this connection.
    Called on failed/partial/stalled sync (D-04)."""
    ...

def execute_auto_prune(
    db: Session,
    connection_id: str,
    app_user_id: str,
    trigger: str,  # "catalog_sync" | "rebuild"
) -> list[str]:
    """Delete all playlist rows with absence_count >= PRUNE_THRESHOLD
    across all playlists owned by app_user_id for this connection.
    Write auto_pruned audit events. Returns list of deleted series_ids."""
    ...

def write_prune_event(
    db: Session,
    playlist_id: str,
    series_id: str,
    event_type: str,  # "auto_pruned" | "manual_removed" | "evidence_cleared"
    reason: str,
    metadata: dict | None = None,
) -> None:
    """Append a prune audit event and enforce 50-event retention per playlist (D-17/D-18)."""
    ...
```

### Pattern 3: New columns on `playlist_series_rows`

**What:** Four nullable columns added to existing `PlaylistSeriesRow` ORM. Nullable so no backfill required and existing rows start at a clean-slate (counter=0 by default). [ASSUMED — column name choices are Claude's Discretion per CONTEXT.md]

```python
# playlist_series_row.py additions:
absence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
first_absence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
last_absence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
last_evidence_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
# last_evidence_source values: "catalog_sync" | "rebuild"
```

### Pattern 4: `PlaylistPruneEvent` ORM model

**What:** New append-only audit table. [ASSUMED — design recommendation]

```python
# backend/src/wheeloffish/db/models/playlist_prune_event.py
class PlaylistPruneEvent(Base):
    __tablename__ = "playlist_prune_events"
    __table_args__ = (
        Index("ix_prune_events_playlist_ts", "playlist_id", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    playlist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    series_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # event_type values: "auto_pruned" | "manual_removed" | "evidence_cleared"
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    # reason values: "catalog_sync" | "rebuild" | "operator"
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # e.g. {"absence_count": 3, "trigger": "catalog_sync"}
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
```

Note: column is named `event_metadata` (not `metadata`) to avoid collision with SQLAlchemy's reserved `metadata` attribute on ORM classes.

### Pattern 5: Alembic migration `011_prune_state_audit`

Following the established pattern (see `010_lib_added_at.py` and `008_playlists_rebuilds.py`):

```python
revision = "011_prune_state_audit"
down_revision = "010_lib_added_at"

def upgrade() -> None:
    # Add columns to playlist_series_rows
    op.add_column("playlist_series_rows",
        sa.Column("absence_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("playlist_series_rows",
        sa.Column("first_absence_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("playlist_series_rows",
        sa.Column("last_absence_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("playlist_series_rows",
        sa.Column("last_evidence_source", sa.String(32), nullable=True))

    # Create playlist_prune_events table
    op.create_table("playlist_prune_events", ...)
    op.create_index("ix_prune_events_playlist_ts", "playlist_prune_events",
                    ["playlist_id", "timestamp"])
```

### Pattern 6: Nightly batch sync-before-rebuild ordering (D-05)

**The gap:** `run_nightly_batch` currently calls only `rebuild_playlist` for due playlists. There is no catalog sync in the nightly path. `trigger_sync` uses `asyncio.create_task` (fire-and-forget) — not usable for ordered nightly batch.

**Solution:** Call `await run_chunked_sync(connection_id, app_user_id)` directly inside `run_nightly_batch` before the rebuild loop. `run_chunked_sync` manages its own DB session, so it can be awaited from the batch without session conflicts.

**Architecture note:** The current `run_nightly_batch` uses only the **first** connection for reachability gating and rebuilds ALL playlists. For Phase 10, we need to group playlists by connection so we can sync each connection before rebuilding that connection's playlists. This requires modest refactoring of the batch inner loop.

```python
# Proposed nightly batch structure:
async def run_nightly_batch(db: Session, settings) -> None:
    # Group due playlists by connection_id
    for connection_id in distinct_connection_ids:
        # 1. Reachability check
        reachable = await check_provider_reachable(provider_for_connection)
        if not reachable:
            # fail runs + reset counters (D-04)
            reset_absence_counters_for_connection(db, connection_id, app_user_id)
            continue

        # 2. Catalog sync (D-05)
        await run_chunked_sync(connection_id, app_user_id)
        # catalog_sync hook already calls record_catalog_sync_absence + execute_auto_prune

        # 3. Rebuild due playlists on this connection
        for playlist in due_playlists_for_connection:
            await rebuild_playlist(db, playlist.id, trigger="nightly")
```

### Pattern 7: `execute_auto_prune` scope

**Scope question:** Auto-prune is triggered at end of successful catalog sync OR successful rebuild. The trigger determines the scope:

- **Catalog sync trigger:** Scope = all playlists owned by `app_user_id` that have rows on `connection_id`. The sync is connection-scoped.
- **Rebuild trigger:** Scope = single playlist. After `rebuild_playlist` completes successfully/partially, check rows in that playlist only.

Both call `execute_auto_prune` but with different scopes. The service function should accept either `playlist_id` (rebuild scope) or `(connection_id, app_user_id)` (sync scope) — or two separate entry points.

### Anti-Patterns to Avoid

- **Incrementing on `fetch_failure`:** Generic timeouts/5xx/auth errors must never increment absence counter. Only `empty_snapshot` and `not_found` when provider is reachable count (D-02).
- **Counting rebuild evidence when provider is unreachable:** `check_provider_reachable` must gate ALL rebuild evidence increments (D-04).
- **Using `asyncio.create_task` for nightly sync:** Fire-and-forget breaks ordering guarantee (D-05). Call `await run_chunked_sync(...)` directly.
- **Resetting counters in orchestrator for failed rebuild:** D-04 only says failed/partial/stalled *catalog sync* resets counters. A failed rebuild does NOT reset counters (provider may just be transiently down for that one playlist).
- **Naming the JSON column `metadata`:** Conflicts with SQLAlchemy `DeclarativeBase.metadata`. Use `event_metadata`.
- **Retention via trigger/constraint:** Implement retention in Python (`write_prune_event` queries and deletes old events) not in DB constraints, consistent with `prune_rebuild_history` pattern in `orchestrator.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Soft-delete / stale flag | Custom stale state table | New columns on existing `playlist_series_rows` | Single source of truth; D-08 explicitly permits this |
| Event retention | DB trigger or CRON | Python `write_prune_event` enforces 50-per-playlist after each insert | Matches `prune_rebuild_history` pattern already in codebase |
| Absence detection | Per-row provider call | Query `CachedSeries` after sync purge | Provider already told us (sync just deleted absent series from cache) |
| Recovery detection | Separate "seen again" table | Query `CachedSeries` for rows with `absence_count > 0` | Data is already there |

**Key insight:** The `CachedSeries` purge at the end of `run_chunked_sync` (line 554–558) is the authoritative absence signal — series not updated by the sync are deleted. After that purge, any `playlist_series_rows` row whose `series_id` is NOT in `CachedSeries` for that connection/user is a confirmed catalog-sync absence.

---

## Common Pitfalls

### Pitfall 1: Counting `ProviderNotFound` the same as `fetch_failure` (currently)
**What goes wrong:** Operator removes a show from Plex/Jellyfin → `ProviderNotFound` during rebuild → currently labeled "fetch_failure" → no evidence accumulates → show stays in playlist forever.  
**Why it happens:** Both `ProviderNotFound` and generic errors are caught by the same `ProviderError` handler in `_fetch_episodes`, returning `None` from `fetch_rebuild_inputs_for_row`.  
**How to avoid:** Catch `ProviderNotFound` before the generic `ProviderError` guard; return `FetchResult(reason="not_found")` instead of `None`.  
**Warning signs:** Series that should prune never reaching threshold even after multiple nightly runs.

### Pitfall 2: Session isolation between `run_chunked_sync` and `run_nightly_batch`
**What goes wrong:** `run_chunked_sync` creates its own session internally. If the planner tries to share the `run_nightly_batch` db session, you get "session already closed" or stale reads.  
**Why it happens:** `run_chunked_sync` calls `db.close()` in its `finally` block (line 608 of `catalog_sync.py`).  
**How to avoid:** Always call `await run_chunked_sync(connection_id, app_user_id)` as a standalone coroutine — it manages its own session. After it returns, the nightly batch's own session reads fresh state from DB.

### Pitfall 3: Resetting counters on rebuild failure (wrong trigger)
**What goes wrong:** A rebuild fails for one playlist → planner adds counter reset → all playlists on the connection lose their absence evidence.  
**Why it happens:** D-04 is specifically about *catalog sync* failures, not rebuild failures. Rebuild failures (provider down for a moment) should not nullify sync-based evidence.  
**How to avoid:** Reset only in catalog sync failure paths (`ProviderUnauthorized`, `ProviderError`, `_mark_sync_stale_failed`). Never in `rebuild_playlist` or nightly rebuild loop.

### Pitfall 4: Auto-prune running before `execute_auto_prune` sees updated counters
**What goes wrong:** `record_catalog_sync_absence` increments counters then `execute_auto_prune` runs, but the DB hasn't committed yet.  
**Why it happens:** Both functions share the same session; if you don't `db.commit()` between record and prune, the prune query may not see the new counts.  
**How to avoid:** `record_catalog_sync_absence` must commit (or flush + query in same session) before `execute_auto_prune` queries. Alternatively, run in a single function that commits at end. See `run_chunked_sync` which commits per page — the prune logic runs after the final `db.commit()` on line 559.

### Pitfall 5: `manual_removed` audit timing
**What goes wrong:** `remove_playlist_row` deletes the row first, then tries to write the audit event — but the row is already gone and the series_id is lost.  
**Why it happens:** `db.delete(row)` + `db.commit()` before writing the event.  
**How to avoid:** Capture `series_id = row.series_id` before `db.delete(row)`, write audit event before or in same commit.

### Pitfall 6: Multi-user scenarios in `execute_auto_prune`
**What goes wrong:** Two users share a connection; sync for user A prunes rows that belong to user B's playlists.  
**Why it happens:** Playlist rows are user-scoped via `playlist → app_user_id`, but series IDs cross-reference connection-scoped catalog data.  
**How to avoid:** `execute_auto_prune` must filter by `playlist.app_user_id == app_user_id` — only prune rows belonging to the user whose sync just ran. The current single-user deployment reduces urgency but correctness requires this gate.

### Pitfall 7: `absence_count` drift after operator manually removes then re-adds a series
**What goes wrong:** Operator removes a series with `absence_count=2` via the editor. Series is re-added (re-appears on server). New row has `absence_count=0`. This is correct — but the audit trail shows `manual_removed` for the old row even though the new row has no history.  
**Why it happens:** The column starts at 0 on new row creation (default). This is the correct behavior.  
**How to avoid:** No action needed — default 0 is correct. Just verify `append_playlist_row` / `PUT /playlists/{id}` don't carry over old row state.

---

## Integration Points — Exact File/Function Map

### `catalog_sync.py`

| Location | Action | Decision |
|----------|--------|----------|
| After line 558 (`db.commit()` post-purge) in `run_chunked_sync` | Call `clear_prune_state_for_recovered(db, connection_id, app_user_id)` then `record_catalog_sync_absence(db, connection_id, app_user_id)` then `execute_auto_prune(db, connection_id, app_user_id, trigger="catalog_sync")` then `db.commit()` | D-02/D-06 |
| `except ProviderUnauthorized` block (line 572) | Call `reset_absence_counters_for_connection(db, connection_id, app_user_id)` before `db.commit()` | D-04 |
| `except (ProviderError, ValueError, Exception)` block (line 594) | Call `reset_absence_counters_for_connection(db, connection_id, app_user_id)` before `db.commit()` | D-04 |
| `_mark_sync_stale_failed` function | Call `reset_absence_counters_for_connection(db, connection_id, app_user_id)` — requires passing these args in (currently only takes `state` and `now`) | D-04 (stalled = 180s timeout) |

**Note on `_mark_sync_stale_failed`:** This function is called from `get_sync_status` (line 434) and doesn't currently receive `connection_id`/`app_user_id`. Adding the reset here requires passing those args or querying them from `state`. Simpler alternative: when stale sync is detected, the status is set to "failed" — and the failed-sync path will handle the reset on the next call to `run_chunked_sync`.

Actually, `_mark_sync_stale_failed` is called lazily from `get_sync_status` (not from `run_chunked_sync`). The `run_chunked_sync` exception handlers are the primary reset paths. The stale detection happens only when someone calls `get_sync_status`. This is an edge case — the reset triggered by `get_sync_status` calling `_mark_sync_stale_failed` is a nice-to-have; the primary D-04 reset coverage is via `run_chunked_sync` exception handlers. The planner should document this as a follow-up if thorough D-04 coverage is needed.

### `rebuild_inputs.py`

| Location | Action | Decision |
|----------|--------|----------|
| `_fetch_episodes` inner function | Catch `ProviderNotFound` and re-raise it (or let it propagate before generic `ProviderError`) | D-02 |
| `fetch_rebuild_inputs_for_row` | Change return type to `FetchResult`; add `not_found` case before generic `ProviderError` | D-02 |
| All call sites in `orchestrator.py` | Update to handle `FetchResult` instead of `SeriesRebuildInput | None` | D-02 |
| Existing tests in `test_orchestrator.py` | Update mock side effects to return `FetchResult` | Backward compat |

### `orchestrator.py`

| Location | Action | Decision |
|----------|--------|----------|
| Top of `rebuild_playlist` (after provider is built) | `reachable = await check_provider_reachable(provider)` | D-04 (gate for rebuild evidence) |
| Per-row loop (currently line 127) | Update to use `FetchResult`; for `empty_snapshot` and `not_found` when `reachable`, call `record_rebuild_row_absence(db, row_orm, "rebuild")` | D-02 |
| After `db.commit()` on final run state (line ~204) | For `status in ("succeeded", "partial")`: call `execute_auto_prune(db, playlist_id_scope, app_user_id, trigger="rebuild")` | D-06 |
| `run_nightly_batch` | Refactor: group playlists by connection; call `await run_chunked_sync` per connection before rebuilding that connection's due playlists | D-05 |
| `run_nightly_batch` provider-unreachable path (line 237) | Add `reset_absence_counters_for_connection` (nightly unreachable = failed sync context) | D-04 |

**Note on `rebuild_playlist` row access:** The current orchestrator loop uses `domain_playlist.rows` (domain objects, not ORM). To call `record_rebuild_row_absence(db, row_orm, ...)` we need the ORM row. Either query it: `db.query(PlaylistSeriesRowOrm).filter(...series_id...).one_or_none()`, or pass both domain and ORM rows. Simplest: look up ORM rows by playlist_id and series_id in bulk before the loop.

### `playlists.py` (API routes)

| Location | Action | Decision |
|----------|--------|----------|
| `remove_playlist_row` handler | Capture `series_id` before delete; call `write_prune_event(db, playlist_id, series_id, "manual_removed", "operator")` before or in same commit | D-17 |
| `_playlist_to_detail` | Query last 10–20 `PlaylistPruneEvent` for playlist; embed as `recent_prune_events` | D-18 |
| `PlaylistDetailResponse` schema | Add `recent_prune_events: list[PruneEventResponse] = []` | D-18 |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 + pytest-asyncio |
| Config file | `backend/pyproject.toml` (`asyncio_mode = "auto"`) |
| Quick run command | `cd backend && python3 -m pytest tests/unit/test_catalog_prune.py -x` |
| Full suite command | `cd backend && python3 -m pytest -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRUNE-01 | Counter at 1 or 2 does NOT delete row | unit | `pytest tests/unit/test_catalog_prune.py::test_sub_threshold_no_prune -x` | ❌ Wave 0 |
| PRUNE-01 | `fetch_failure` does NOT increment counter | unit | `pytest tests/unit/test_catalog_prune.py::test_fetch_failure_no_increment -x` | ❌ Wave 0 |
| PRUNE-02 | Counter reaches 3 → row deleted, audit written | unit | `pytest tests/unit/test_catalog_prune.py::test_auto_prune_at_threshold -x` | ❌ Wave 0 |
| PRUNE-02 | Failed catalog sync resets counters to 0 | unit | `pytest tests/unit/test_catalog_prune.py::test_reset_on_failed_sync -x` | ❌ Wave 0 |
| PRUNE-02 | Provider unreachable in rebuild → no counter increment | unit | `pytest tests/unit/test_catalog_prune.py::test_no_increment_when_unreachable -x` | ❌ Wave 0 |
| PRUNE-02 | Series reappears → counter reset to 0 | unit | `pytest tests/unit/test_catalog_prune.py::test_clear_on_recovery -x` | ❌ Wave 0 |
| PRUNE-02 | `ProviderNotFound` increments when provider reachable | unit | `pytest tests/unit/test_catalog_prune.py::test_not_found_increments` | ❌ Wave 0 |
| PRUNE-03 | `manual_removed` event written on row delete | unit | `pytest tests/integration/test_playlists_api.py::test_manual_removed_audit -x` | ❌ Wave 0 |
| PRUNE-03 | `recent_prune_events` embedded in playlist detail GET | unit | `pytest tests/integration/test_playlists_api.py::test_prune_events_in_detail -x` | ❌ Wave 0 |
| PRUNE-03 | Audit retention: max 50 events per playlist | unit | `pytest tests/unit/test_catalog_prune.py::test_audit_retention_50 -x` | ❌ Wave 0 |
| PRUNE-04 | `empty_snapshot` warning still in `row_outcomes_json` at counter < 3 | unit | `pytest tests/unit/test_orchestrator.py::test_empty_snapshot_row_warning` | ✅ (existing) |
| PRUNE-04 | `fetch_failure` warning still in `row_outcomes_json` | unit | `pytest tests/unit/test_orchestrator.py::test_row_skip_on_fetch_failure` | ✅ (existing) |
| PRUNE-02 | `ProviderNotFound` treated as "not_found" reason (not "fetch_failure") | unit | `pytest tests/unit/test_catalog_prune.py::test_not_found_fetch_result -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python3 -m pytest tests/unit/test_catalog_prune.py -x`
- **Per wave merge:** `cd backend && python3 -m pytest tests/unit/ tests/integration/ -x`
- **Phase gate:** `cd backend && python3 -m pytest -x` (full suite green)

### Wave 0 Gaps
- [ ] `tests/unit/test_catalog_prune.py` — covers PRUNE-01, PRUNE-02, PRUNE-03 unit cases
- [ ] `tests/unit/test_catalog_prune.py` — `db_session` fixture already available via `conftest.py`
- [ ] Existing `tests/unit/test_orchestrator.py` will need updating for `FetchResult` return type (not new file, just updated mocks)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes | `_get_owned_playlist` ownership check already in all playlist routes |
| V5 Input Validation | no | No new user inputs; event_type/reason are internal enum-like strings |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR on prune events API embed | Information Disclosure | `recent_prune_events` embedded via `_playlist_to_detail` which is already gated by `_get_owned_playlist(db, playlist_id, user.id)` — no new auth surface |
| Prune cascade from malicious sync | Spoofing/Tampering | Counter threshold (3) + reset on any sync failure; provider reachability gate on rebuild evidence |
| Audit log flooding | Denial of Service | 50-event retention cap per playlist in `write_prune_event`; only 3 material event types logged |

**Assessment:** Phase 10 adds no new authentication surface. The prune pipeline runs server-side only in the sync/rebuild background flows. The API embed is ownership-gated by the existing `_get_owned_playlist` pattern. No new input endpoints are added.

---

## Recommended Plan Wave Breakdown

| Wave | Plans | Dependencies | Can Parallelize? |
|------|-------|--------------|-----------------|
| Wave 0 | DB migration (`011_...`), new `PlaylistPruneEvent` ORM, update `PlaylistSeriesRow` ORM, update `__init__.py` | None (blocking) | All Wave 0 plans commit together in one migration |
| Wave 1 | `catalog_prune.py` service module + unit tests in `test_catalog_prune.py` | Wave 0 (needs new columns/table) | No — Wave 2/3 import this module |
| Wave 2 | `rebuild_inputs.py` `FetchResult` typing + update orchestrator per-row loop + update existing orchestrator tests | Wave 1 | Parallel with Wave 3? No — Wave 3 needs Wave 2 typed results |
| Wave 3 | `catalog_sync.py` integration (absence detection, reset, prune trigger) | Wave 1 | Can run parallel with Wave 2 since they touch different files |
| Wave 4 | `orchestrator.py` nightly batch sync-before-rebuild refactor + rebuild `execute_auto_prune` call | Wave 1, Wave 2 | — |
| Wave 5 | `playlists.py` manual_removed audit + `schemas/playlists.py` PruneEventResponse + `_playlist_to_detail` embed | Wave 1 | Can run parallel with Wave 2/3/4 |

**Recommended plan numbering:**
- 10-01: DB schema (migration + ORM models)
- 10-02: `catalog_prune.py` service + unit tests
- 10-03: `rebuild_inputs.py` FetchResult + orchestrator rebuild integration
- 10-04: `catalog_sync.py` integration (absence + reset + prune)
- 10-05: Nightly batch sync-before-rebuild ordering
- 10-06: API schema + embed + manual_removed audit

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All backend | ✓ | 3.x (confirmed by pytest 8.4.1 execution) | — |
| pytest + pytest-asyncio | Tests | ✓ | 8.4.1 | — |
| SQLite (test) / Postgres (prod) | Alembic + tests | ✓ | Alembic migrations run on SQLite in tests (conftest.py) | — |

No new external dependencies. All required tools available. [VERIFIED: codebase + shell]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `FetchResult` dataclass design for typed return from `fetch_rebuild_inputs_for_row` | Architecture Patterns | Planner may choose alternate approach (e.g., typed sentinel, exception propagation); existing tests will need updates regardless |
| A2 | `catalog_prune.py` as standalone module (not embedded in `catalog_sync.py` or `orchestrator.py`) | Architecture Patterns | Cosmetic — logic is identical regardless of file; planner has discretion |
| A3 | `event_metadata` column name on `PlaylistPruneEvent` (avoids SQLAlchemy `metadata` conflict) | Architecture Patterns | Using `metadata` would cause ORM errors; `event_metadata` is safe alternative |
| A4 | `run_chunked_sync` can be safely awaited directly from `run_nightly_batch` despite managing its own session | Architecture Patterns, Common Pitfalls | If the session factory is not re-entrant or there are global state issues, may need a different approach |
| A5 | Nightly batch needs connection-level grouping refactor | Architecture Patterns | Current single-connection assumption may already suffice for the single-operator use case; planner can decide minimal refactor scope |
| A6 | `_mark_sync_stale_failed` counter reset is lower priority (lazy trigger from `get_sync_status`) | Integration Points | If stalled syncs are common, counter drift could occur until next `run_chunked_sync` failure path runs the reset |

---

## Open Questions (RESOLVED)

1. **`run_nightly_batch` multi-connection scope**
   - RESOLVED: Implement connection-grouped nightly loop per D-05 (plan 10-05); multi-connection is supported even if uncommon.

2. **`_mark_sync_stale_failed` and D-04 coverage**
   - RESOLVED: Add counter reset to `_mark_sync_stale_failed` with `connection_id` / `app_user_id` from `CatalogSyncState` (plan 10-04).

3. **`execute_auto_prune` granularity: playlist-scoped vs connection-scoped after rebuild**
   - RESOLVED: Playlist-scoped prune after rebuild; connection-scoped prune at catalog sync end (plans 10-03, 10-04).

---

## Sources

### Primary (HIGH confidence)
- Codebase direct read: `catalog_sync.py`, `orchestrator.py`, `rebuild_inputs.py`, `playlist_series_row.py`, `rebuild_run.py`, `playlists.py`, `schemas/playlists.py`, `errors.py` — [VERIFIED: codebase]
- Codebase direct read: All 10 Alembic migration files — revision chain and migration pattern confirmed [VERIFIED: codebase]
- Codebase direct read: `tests/conftest.py`, `tests/unit/test_orchestrator.py` — test infrastructure pattern confirmed [VERIFIED: codebase]
- `pytest --version` in backend: 8.4.1 [VERIFIED: shell]

### Secondary (MEDIUM confidence)
- SQLAlchemy `mapped_column` / `Mapped` pattern from existing models [VERIFIED: codebase patterns]
- `structlog.get_logger` pattern from all existing modules [VERIFIED: codebase]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all existing dependencies verified in codebase
- Architecture: HIGH — hook points confirmed by reading all canonical source files
- Pitfalls: HIGH — identified from actual code patterns (session lifecycle, `ProviderNotFound` fall-through, `metadata` SQLAlchemy conflict)
- Test strategy: HIGH — pytest 8.4.1 confirmed; `db_session` fixture established in `conftest.py`

**Research date:** 2026-06-02  
**Valid until:** Stable — pure Python/SQLAlchemy backend with no fast-moving external dependencies

---

## RESEARCH COMPLETE

**Phase:** 10 - Safe Catalog Prune  
**Confidence:** HIGH

### Key Findings

1. **No new packages needed.** All implementation uses existing stack (SQLAlchemy, Alembic, FastAPI, structlog, pytest). Pure backend feature — zero frontend changes.

2. **Critical gap in `fetch_rebuild_inputs_for_row`:** `ProviderNotFound` currently falls through the same `ProviderError` catch as generic failures, both returning `None` labeled "fetch_failure". Phase 10 requires a typed `FetchResult` return to distinguish `not_found` (qualifies as rebuild evidence, D-02) from `fetch_failure` (does NOT qualify). This is the most impactful code change.

3. **Nightly batch must be refactored for sync-before-rebuild ordering (D-05).** Current `run_nightly_batch` has no catalog sync step. Needs connection-grouped loop: `check_reachable` → `await run_chunked_sync(...)` → rebuild due playlists per connection.

4. **Two hook points in `catalog_sync.py` after the `CachedSeries` purge (lines 554–558):** Absence detection reads "which `playlist_series_rows` point to series IDs no longer in `CachedSeries`?" — clean, no provider calls needed. Reset logic goes in the three exception handlers.

5. **`event_metadata` naming required** — SQLAlchemy ORM reserves `metadata` as a class attribute; the audit table column must be named differently (e.g., `event_metadata`).

6. **Recommended 6 plans / 5 waves:** Wave 0 (DB schema), Wave 1 (prune service), Wave 2+3 (sync/rebuild integration, parallelizable), Wave 4 (nightly ordering), Wave 5 (API embed). Each plan is independently committable.

### File Created
`.planning/phases/10-safe-catalog-prune/10-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | No new packages; all libraries verified in codebase |
| Architecture | HIGH | All hook points confirmed by reading canonical source files |
| FetchResult design | HIGH | ProviderNotFound fall-through confirmed in current code |
| Nightly batch gap | HIGH | `run_nightly_batch` confirmed to have no catalog sync call |
| Pitfalls | HIGH | Most identified from actual code patterns |
| Test strategy | HIGH | pytest infrastructure confirmed; `db_session` fixture established |

### Ready for Planning
Research complete. Planner can now create PLAN.md files for the 6 recommended plans.
