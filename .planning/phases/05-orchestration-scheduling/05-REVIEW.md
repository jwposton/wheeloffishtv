---
phase: 05-orchestration-scheduling
reviewed: 2026-05-25T22:44:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - backend/src/wheeloffish/db/models/playlist.py
  - backend/src/wheeloffish/db/models/playlist_series_row.py
  - backend/src/wheeloffish/db/models/rebuild_run.py
  - backend/alembic/versions/008_playlists_rebuilds.py
  - backend/src/wheeloffish/core/playlist/mappers.py
  - backend/src/wheeloffish/db/models/__init__.py
  - backend/src/wheeloffish/core/scheduler.py
  - backend/src/wheeloffish/core/playlist/cadence.py
  - backend/src/wheeloffish/core/orchestrator.py
  - backend/src/wheeloffish/core/config.py
  - backend/src/wheeloffish/main.py
  - backend/src/wheeloffish/core/playlist/rebuild_inputs.py
  - backend/src/wheeloffish/api/schemas/playlists.py
  - backend/src/wheeloffish/api/routes/playlists.py
  - frontend/src/api/playlists.ts
  - frontend/src/api/types.ts
  - frontend/src/components/playlists/StatusBadge.tsx
  - frontend/src/components/playlists/PlaylistCard.tsx
  - frontend/src/pages/PlaylistsPage.tsx
  - frontend/src/App.tsx
  - frontend/src/components/layout/AppShell.tsx
  - frontend/src/components/playlists/SeriesPicker.tsx
  - frontend/src/components/playlists/PlaylistForm.tsx
  - frontend/src/components/playlists/RebuildBanner.tsx
  - frontend/src/components/playlists/OutputList.tsx
  - frontend/src/pages/PlaylistFormPage.tsx
  - frontend/src/pages/PlaylistDetailPage.tsx
findings:
  critical: 2
  warning: 7
  info: 3
  total: 12
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-05-25T22:44:00Z
**Depth:** standard
**Files Reviewed:** 27 (test files excluded per review policy)
**Status:** issues_found

## Summary

Phase 5 implements the full playlist orchestration stack: SQLAlchemy ORM models, Alembic migration, APScheduler nightly cron, rebuild orchestrator with per-row failure isolation, REST CRUD API, and a React SPA covering list/detail/form/rebuild flows. The backend Python code is structurally sound and the ORM/migration/cadence layer is clean. Two blockers were found that prevent shipped features from working correctly in production: every playlist update request will return 405 (HTTP method mismatch), and every weekly playlist will rebuild on the wrong day of the week (day-of-week convention mismatch between frontend and backend). Seven warnings cover dead/duplicate code, an indefinitely-growing failed-run table, a type mismatch in the rebuild trigger API surface, and a missing range guard on cron parsing.

---

## Critical Issues

### CR-01: Frontend uses PATCH, backend only registers PUT — every playlist update returns 405

**File:** `frontend/src/api/playlists.ts:105`
**Issue:** `updatePlaylist()` sends `method: "PATCH"`, but the backend router registers the endpoint as `@router.put("/{playlist_id}", ...)`. FastAPI will return `405 Method Not Allowed` for every edit-form submission. The `PlaylistUpdateRequest` schema uses all-optional fields (semantically a PATCH contract), yet the handler is PUT-only — the mismatch is between the API contract intent and the HTTP method registered.

**Backend declaration:**
```python
# backend/src/wheeloffish/api/routes/playlists.py:240
@router.put("/{playlist_id}", response_model=PlaylistDetailResponse)
def update_playlist(...):
```

**Frontend call:**
```typescript
// frontend/src/api/playlists.ts:104-108
export async function updatePlaylist(id: string, payload: PlaylistUpdatePayload): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(`/playlists/${id}`, {
    method: "PATCH",   // ← PATCH sent, PUT registered on server
    body: JSON.stringify(payload),
  })
}
```

**Fix (Option A — align backend to frontend intent):**
```python
# routes/playlists.py
@router.patch("/{playlist_id}", response_model=PlaylistDetailResponse)
def update_playlist(...):
```

**Fix (Option B — align frontend to backend):**
```typescript
// playlists.ts
method: "PUT",
```
Option A is semantically correct (all fields optional = PATCH) and preferred.

---

### CR-02: Day-of-week convention mismatch — weekly playlists rebuild on the wrong day

**File:** `backend/src/wheeloffish/core/playlist/cadence.py:31` and `frontend/src/components/playlists/PlaylistForm.tsx:29-36`
**Issue:** The frontend's `DOW_OPTIONS` and `WEEKDAY_NAMES` use **Sunday = 0, Monday = 1 … Saturday = 6** (JavaScript `Date.getDay()` convention). The backend's `is_due()` compares against `datetime.weekday()` which returns **Monday = 0, Tuesday = 1 … Sunday = 6** (Python convention). The stored integer means different days to each side.

Concrete impact table (what value is stored vs when it fires):

| User selects | Value stored | `is_due` fires when weekday() == value | Actual day that triggers |
|---|---|---|---|
| Sunday (value 0) | 0 | Monday | Monday |
| Monday (value 1) | 1 | Tuesday | Tuesday |
| Tuesday (value 2) | 2 | Wednesday | Wednesday |
| Saturday (value 6) | 6 | Sunday | Sunday |

Every weekly playlist fires one calendar day later than the user selected. Sunday selections fire on Monday instead.

**Backend:**
```python
# cadence.py:31 — Python weekday(): Mon=0, Sun=6
return now_local.weekday() == dow   # interprets stored value as Mon=0
```

**Frontend form:**
```typescript
// PlaylistForm.tsx:29-36 — Sunday=0, Mon=1, Sat=6
const DOW_OPTIONS = [
  { value: 1, label: "Monday" },  // stores 1 → backend fires on Tuesday
  { value: 0, label: "Sunday" },  // stores 0 → backend fires on Monday
  ...
]
```

**Fix:** Align `DOW_OPTIONS` in `PlaylistForm.tsx` (and `WEEKDAY_NAMES` in `playlists.ts`) to the Python `weekday()` convention (Monday = 0):

```typescript
// PlaylistForm.tsx — replace DOW_OPTIONS
const DOW_OPTIONS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
]

// playlists.ts — replace WEEKDAY_NAMES to match
const WEEKDAY_NAMES = [
  "Monday",    // 0
  "Tuesday",   // 1
  "Wednesday", // 2
  "Thursday",  // 3
  "Friday",    // 4
  "Saturday",  // 5
  "Sunday",    // 6
] as const
```

Existing playlists in the DB that are already `refresh_cadence="weekly"` will also need a data migration to shift stored DOW values by -1 (mod 7) to match the corrected convention.

---

## Warnings

### WR-01: `recover_interrupted_rebuilds` duplicated in `main.py` — orchestrator version is dead code

**File:** `backend/src/wheeloffish/main.py:29` / `backend/src/wheeloffish/core/orchestrator.py:269`
**Issue:** An identical function `recover_interrupted_rebuilds` exists in both modules. `main.py` defines and calls its own local copy (line 53). The orchestrator's version (lines 269–284) is never imported or invoked — it is dead code. The two implementations silently diverge: `main.py` uses error message `"Interrupted by restart"` while `orchestrator.py` uses `"Interrupted by server restart"`. If a developer updates the orchestrator version, startup behaviour will not change.

**Fix:** Delete the local copy in `main.py` and import from the orchestrator:
```python
# main.py — remove lines 29-43, add import:
from wheeloffish.core.orchestrator import recover_interrupted_rebuilds, run_nightly_rebuilds
```

---

### WR-02: `formatRelativeTime` duplicated in two frontend components

**File:** `frontend/src/components/playlists/PlaylistCard.tsx:8` and `frontend/src/components/playlists/RebuildBanner.tsx:5`
**Issue:** The same 10-line `formatRelativeTime` helper is copy-pasted verbatim into both files. Any future change to bucketing logic (e.g., adding "weeks" bucket) must be applied in two places.

**Fix:** Extract to a shared utility:
```typescript
// frontend/src/lib/formatRelativeTime.ts
export function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "Never"
  const diffMs = Date.now() - new Date(isoString).getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}
```

---

### WR-03: `triggerRebuild` declares wrong response type — `rebuild_run_id` field does not exist

**File:** `frontend/src/api/playlists.ts:115`
**Issue:** The function signature declares `Promise<{ rebuild_run_id: string }>` but the backend `rebuild_playlist` endpoint returns a `RebuildRunSummary` object whose ID field is `id`, not `rebuild_run_id`. The field `rebuild_run_id` does not exist in the response. `useRebuildPlaylist` discards `_data` so this is currently harmless at runtime, but the incorrect type will mislead any future caller that consumes the return value.

```typescript
// current — wrong field name in declared type
export async function triggerRebuild(id: string): Promise<{ rebuild_run_id: string }> {

// fix — use RebuildRunSummary or the correct field
export async function triggerRebuild(id: string): Promise<RebuildRunSummary> {
  return fetchJson<RebuildRunSummary>(`/playlists/${id}/rebuild`, { method: "POST" })
}
```

Import `RebuildRunSummary` from the same file (it is already defined there).

---

### WR-04: Failed rebuild runs without snapshots are never pruned — table grows without bound

**File:** `backend/src/wheeloffish/core/orchestrator.py:34`
**Issue:** `prune_rebuild_history` only queries and deletes runs where `snapshot_json IS NOT NULL`:
```python
.filter(
    RebuildRun.playlist_id == playlist_id,
    RebuildRun.snapshot_json.isnot(None),   # only pruned runs
)
```
Runs that fail before reaching the snapshot stage (connection missing, all rows failed, provider unreachable) have `snapshot_json=None` and are never deleted. In a long-running installation with frequent provider errors, the `rebuild_runs` table grows indefinitely.

**Fix:** Add a separate retention window for failed runs without snapshots, or extend the existing prune to also cap total run count per playlist:
```python
def prune_rebuild_history(db: Session, playlist_id: str, keep: int = 3) -> None:
    # Prune runs with snapshots — keep 3
    runs_with_snapshot = (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist_id, RebuildRun.snapshot_json.isnot(None))
        .order_by(RebuildRun.finished_at.desc())
        .all()
    )
    for run in runs_with_snapshot[keep:]:
        db.delete(run)

    # Also cap total run count per playlist (e.g., keep 20)
    all_runs = (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist_id)
        .order_by(RebuildRun.created_at.desc())
        .all()
    )
    for run in all_runs[20:]:
        db.delete(run)

    db.flush()
```

---

### WR-05: `parse_cron_time` does not validate hour/minute ranges

**File:** `backend/src/wheeloffish/core/playlist/cadence.py:35`
**Issue:** `parse_cron_time("99:99")` succeeds and returns `(99, 99)`. APScheduler will then raise an obscure internal error when `create_scheduler` calls `CronTrigger(hour=99, minute=99, ...)`, producing a confusing startup crash with no indication of which environment variable is the cause.

**Fix:**
```python
def parse_cron_time(cron_str: str) -> tuple[int, int]:
    try:
        parts = cron_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Expected HH:MM format, got: {cron_str!r}")
        hour = int(parts[0])
        minute = int(parts[1])
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid cron time {cron_str!r}: {exc}") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(
            f"Cron time out of range in {cron_str!r}: hour must be 0–23, minute 0–59"
        )
    return (hour, minute)
```

---

### WR-06: API allows `rows=[]` on PUT — no backend guard against zero-row playlists

**File:** `backend/src/wheeloffish/api/routes/playlists.py:263`
**Issue:** `update_playlist` accepts `rows=[]` (empty list) and replaces all existing rows with none, leaving the playlist in a permanently broken rebuild state. The frontend validates "at least one series" but the API has no such constraint. Any direct API call with `"rows": []` results in a playlist that will always fail with "Playlist has no rows or series IDs are malformed".

**Fix:** Add a validator in `PlaylistUpdateRequest` or a check in the route:
```python
# In update_playlist, before deleting rows:
if body.rows is not None and len(body.rows) == 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Playlist must contain at least one series row",
    )
```

---

### WR-07: `_get_provider_context` native_id fallback ignores connection_id — can return wrong series in multi-connection setups

**File:** `backend/src/wheeloffish/core/playlist/rebuild_inputs.py:36`
**Issue:** When the primary lookup by composite `CachedSeries.id` fails, the fallback queries by `native_id` alone (without filtering by connection or library):
```python
row = (
    db.query(CachedSeries)
    .filter(
        CachedSeries.app_user_id == app_user_id,
        CachedSeries.native_id == native_id,   # no connection_id filter
    )
    .one_or_none()
)
```
If a user has two connections (e.g., Plex and Jellyfin) where both have a series with the same native_id (common for popular shows), the fallback may return the wrong connection's series and supply incorrect `rating_key`/`library_native_id` to the episode fetch. This will silently cause episode fetches to fail or return wrong results.

**Fix:** Add the `connection_id` extracted from the composite ID to the fallback filter:
```python
_, connection_id_part, native_id = parse_composite_id(canonical_id)
row = (
    db.query(CachedSeries)
    .filter(
        CachedSeries.app_user_id == app_user_id,
        CachedSeries.connection_id == connection_id_part,
        CachedSeries.native_id == native_id,
    )
    .one_or_none()
)
```

---

## Info

### IN-01: `orm_to_playlist` raises unhandled `ValueError` on stale enum values in DB

**File:** `backend/src/wheeloffish/core/playlist/mappers.py:17`
**Issue:** `RowMode(row.mode)`, `CompletionPolicy(row.completion_policy)`, `SlotAllocation(orm.slot_allocation)` etc. all raise `ValueError` if the DB contains a value that is no longer in the enum (e.g., after a domain enum rename without a data migration). This exception propagates to the orchestrator and causes the entire rebuild to fail with an unrelated-looking error.

**Fix:** Wrap enum coercions in the mapper or add a comment documenting the constraint, and ensure any enum value renames include a migration:
```python
try:
    return Playlist(
        ...
        slot_allocation=SlotAllocation(orm.slot_allocation),
        ...
    )
except ValueError as exc:
    raise ValueError(
        f"Playlist {orm.id!r} contains invalid enum value: {exc}"
    ) from exc
```

---

### IN-02: `TypeError` fallback in `_fetch_episodes`/`_fetch_on_deck` is too broad

**File:** `backend/src/wheeloffish/core/playlist/rebuild_inputs.py:63-68`
**Issue:** The `except TypeError` catch is intended to handle providers that don't accept keyword arguments, but it also silently swallows TypeErrors from inside `list_episodes`/`get_on_deck_episode` (e.g., wrong argument type from a bug in the provider implementation). This masks provider bugs and makes debugging difficult.

**Fix:** The fallback should ideally only apply on "unexpected keyword argument" TypeErrors. Since that's difficult to check portably, at minimum log the caught TypeError before falling back:
```python
except TypeError as te:
    logger.debug("provider_kwargs_not_supported", error=str(te), series_id=series_id)
    return await provider.list_episodes(series_id)
```

---

### IN-03: TOCTOU race in rebuild 409 guard — two concurrent requests can start two rebuilds

**File:** `backend/src/wheeloffish/api/routes/playlists.py:307`
**Issue:** The 409 check (query for `status=="running"`) and the `run_manual_rebuild` call are not atomic. Two concurrent POST `/rebuild` requests for the same playlist can both pass the running check before either creates a `RebuildRun` row, resulting in two simultaneous rebuilds and two DB commits. In the current SQLite deployment this is serialised by the write lock and benign; on PostgreSQL it could occur.

**Fix:** Use a SELECT FOR UPDATE or an explicit DB-level unique constraint on `(playlist_id, status)` for "running" rows, or serialize rebuilds in an in-memory lock:
```python
# lightweight approach — unique index on (playlist_id, status='running') via partial index
# Or: use asyncio.Lock keyed on playlist_id for the check+create span
```
This can be deferred until a PostgreSQL migration is planned.

---

_Reviewed: 2026-05-25T22:44:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
