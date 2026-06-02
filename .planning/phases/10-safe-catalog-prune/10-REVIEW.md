---
phase: 10-safe-catalog-prune
reviewed: 2026-06-02T23:45:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - backend/alembic/versions/011_prune_state_audit.py
  - backend/src/wheeloffish/db/models/playlist_prune_event.py
  - backend/src/wheeloffish/db/models/playlist_series_row.py
  - backend/src/wheeloffish/db/models/__init__.py
  - backend/src/wheeloffish/core/catalog_prune.py
  - backend/src/wheeloffish/core/playlist/rebuild_inputs.py
  - backend/src/wheeloffish/core/orchestrator.py
  - backend/src/wheeloffish/core/catalog_sync.py
  - backend/src/wheeloffish/api/schemas/playlists.py
  - backend/src/wheeloffish/api/routes/playlists.py
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
status: clean
---

# Phase 10: Code Review Report

**Reviewed:** 2026-06-02T23:45:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** clean

## Summary

Phase 10 delivers a coherent prune pipeline: schema/migration 011, centralized `catalog_prune.py`, sync and rebuild integration, nightly sync-before-rebuild ordering, and playlist-detail audit embed. Core single-user flows and unit/integration tests align with D-01–D-06.

Two **critical** issues affect the nightly batch path: SQLAlchemy session staleness after `run_chunked_sync` can **overwrite** sync evidence counts during rebuild, and nightly grouping/sync/reset is scoped to one arbitrary `UserMediaLink` per connection instead of per `(connection, app_user)` — breaking D-04/D-05 on multi-user installs (supported elsewhere in the codebase).

Migration 011, API embed, and manual-delete audit wiring look correct. No security vulnerabilities found in reviewed source.

## Critical Issues

### CR-01: Nightly rebuild overwrites sync absence counts (stale session)

**File:** `backend/src/wheeloffish/core/orchestrator.py:258-327`, `backend/src/wheeloffish/core/catalog_prune.py:77-87`
**Issue:** `run_nightly_batch` loads due playlists into session A, then `await run_chunked_sync(...)` commits prune evidence in a **separate** session B. `rebuild_playlist(db, ...)` reuses session A and builds `orm_rows_by_series` from cached `playlist_orm.rows` without refresh. `record_rebuild_row_absence` does `row.absence_count += 1` on stale in-memory values and flushes, which can **clobber** higher counts written by sync (e.g. DB=2 after sync, stale=0 → flush writes 1). Auto-prune may also see wrong thresholds on the same stale objects.
**Fix:**
```python
# orchestrator.py — after await run_chunked_sync(...)
await run_chunked_sync(connection_id, app_user_id)
db.expire_all()  # or db.refresh(p) for each playlist in the group

for p in playlists:
    await rebuild_playlist(db, p.id, trigger="nightly")
```

### CR-02: Nightly batch sync/reset scoped to one user per connection

**File:** `backend/src/wheeloffish/core/orchestrator.py:261-321`
**Issue:** Due playlists are grouped by `connection_id` only. `first_link = db.query(UserMediaLink).filter(...).first()` picks an arbitrary user; `run_chunked_sync`, `reset_absence_counters_for_connection`, and unreachable handling all use that single `app_user_id`. The install model allows multiple `AppUser`s linked to the same connection (`Connection` is unique per `provider_type`; catalog data is per `app_user_id`). Other users' playlists in the same nightly group never receive catalog-sync evidence (D-05), and their absence counters are **not** reset on unreachable sync (D-04).
**Fix:** Group by `(connection_id, playlist.app_user_id)` and run sync/reset/rebuild per owner:
```python
by_key: dict[tuple[str, str], list[PlaylistOrm]] = {}
for p in due_playlists:
    ...
    by_key.setdefault((connection_id, p.app_user_id), []).append(p)

for (connection_id, app_user_id), playlists in by_key.items():
    ...
    await run_chunked_sync(connection_id, app_user_id)
    db.expire_all()
    for p in playlists:
        await rebuild_playlist(db, p.id, trigger="nightly")
```

## Warnings

### WR-01: Malformed `series_id` crashes entire connection prune block

**File:** `backend/src/wheeloffish/core/catalog_prune.py:48-52`, `183-187`
**Issue:** `_rows_for_connection` and the `execute_auto_prune` connection filter call `parse_composite_id(row.series_id)` without catching `ValueError`. One malformed row anywhere in the user's playlists aborts `record_catalog_sync_absence`, recovery, reset, and auto-prune for the whole connection. The exception is swallowed in `catalog_sync` (`catalog_sync_prune_error`), so sync completes but prune state is not updated — silent skip.
**Fix:**
```python
def _connection_id_for_row(row: PlaylistSeriesRow) -> str | None:
    try:
        return parse_composite_id(row.series_id)[0]
    except ValueError:
        return None

# In list comprehensions:
if _connection_id_for_row(row) == connection_id
```

### WR-02: Per-library `ProviderUnauthorized` still completes sync and accumulates absence

**File:** `backend/src/wheeloffish/core/catalog_sync.py:515-523`, `561-570`
**Issue:** When `list_series` raises `ProviderUnauthorized` for one library, the inner loop `break`s but sync still marks `status="complete"`, purges `CachedSeries` not refreshed this run, and runs absence increment + auto-prune. Series in skipped libraries can be purged from cache and counted absent even though the sync was not fully authoritative. Prune amplifies this pre-existing partial-sync behavior; D-04 intent ("partial catalog sync resets counters") is not enforced here.
**Fix:** Treat unauthorized mid-sync as a failed sync (reset counters, set `status="failed"`) or track per-library completion and skip purge/prune until all in-scope libraries succeed.

## Info

### IN-01: Audit retention loads all events per playlist

**File:** `backend/src/wheeloffish/core/catalog_prune.py:141-150`
**Issue:** `write_prune_event` queries `.all()` events for retention trimming. Correctness is fine at 50-row cap; query could use `OFFSET MAX` instead of loading full history.
**Fix:** Optional — use a subquery or `limit(MAX+1)` pattern for trim-only reads.

---

_Reviewed: 2026-06-02T23:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
