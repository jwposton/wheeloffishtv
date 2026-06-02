# Phase 10: Safe catalog prune - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

As an operator, shows removed from Plex/Jellyfin eventually leave Wheel of Fish playlists without transient sync or rebuild failures causing data loss. Phase 10 adds a **safe, mostly invisible** prune pipeline: evidence accumulates in the backend, rows auto-remove only after policy is met, and material actions are auditable via API. Operators are **not** given new prune-management UI; existing playlist row actions and rebuild warning copy stay as they are today.

</domain>

<decisions>
## Implementation Decisions

### Safety policy (evidence, cadence, triggers)

- **D-01:** Auto-prune after **3 qualifying evidence events per playlist row** (not 3 logins).
- **D-02:** Qualifying evidence (each +1 for that row):
  - **Catalog sync:** Successful full catalog sync completes; series absent from `CachedSeries` for that user/connection but `playlist_series_rows` row still exists.
  - **Rebuild:** Provider is **reachable** for the batch (`check_provider_reachable` or equivalent), and that row’s live fetch indicates **gone**: `empty_snapshot` or **`ProviderNotFound`** — **not** generic `fetch_failure` (timeouts, 5xx, auth).
- **D-03:** Absence streak **starts** on the **first** qualifying catalog-sync absence (not on first rebuild warning alone).
- **D-04:** On any **failed**, **partial**, or **stalled** catalog sync for a connection, **reset absence counter to 0** for all prune candidates on that connection. Rebuild batch with provider unreachable must **not** increment any row.
- **D-05:** **Cadence:** Run **full catalog sync before nightly rebuild** for each connection in the batch. Manual playlist rebuild continues to run as today and can add per-row rebuild evidence.
- **D-06:** **Auto-prune trigger:** At end of **successful catalog sync** OR **successful rebuild** (playlist completed without total provider failure), delete rows that have reached **3/3** and write audit events.
- **D-07:** Rebuild behavior for sub-threshold rows remains **non-destructive** (existing `fetch_failure` / `empty_snapshot` warnings in `row_outcomes_json`; PRUNE-04).

### Stale state (backend only)

- **D-08:** Persist prune state on **`playlist_series_rows`** (e.g. absence counter, internal stale flag, timestamps, last evidence source). No separate prune-state table required unless planner prefers normalization.
- **D-09:** Internal “stale” begins after **first** qualifying evidence (counter ≥ 1). **No operator-facing stale badge, copy, or controls** — user wants same UX as any other row (remove/reorder/edit only).
- **D-10:** **Server removal** and **out-of-scope library** absences use the **same** counter rules; distinguish in audit `reason` / structured fields if useful, but do not fork policy.
- **D-11:** When series reappears (back in cache after sync or rebuild fetch succeeds), **clear prune state immediately** (counter 0, not stale). Optional `evidence_cleared` audit event only if useful for debugging.

### Operator visibility (minimal)

- **D-12:** **No** prune-specific UI: no “Keep”, “Remove now”, snooze, sync-now button, or stale badges in Phase 10.
- **D-13:** **Rebuild banner copy unchanged** — still generic partial-rebuild warning.
- **D-14:** **Silent auto-prune** in SPA — no toast or banner when rows are removed; row disappears on next load.
- **D-15:** PRUNE-01 satisfied by **not deleting on first miss** + existing rebuild warnings until 3/3, not by new labels.

### Audit (PRUNE-03)

- **D-16:** **`playlist_prune_events`** table: `playlist_id`, `series_id`, `event_type`, `reason`, `timestamp`, optional metadata (e.g. counter at prune, trigger: `catalog_sync` | `rebuild`).
- **D-17:** Log **material events only:** `auto_pruned`, `manual_removed` (when operator uses existing remove API), optionally `evidence_cleared` on recovery. Do **not** log every +1 tick.
- **D-18:** Retain **last 50 events per playlist**; API embed returns **most recent 10–20** on playlist detail GET as `recent_prune_events[]`.
- **D-19:** No dedicated prune UI in Phase 10; Phase 11 diagnostics modal may consume the same API payload later.

### Claude's Discretion

- Exact column names and migration shape on `playlist_series_rows`.
- Whether `manual_removed` is inferred from existing delete endpoint vs explicit event type in handler.
- Structlog fields mirroring `auto_pruned` for operators tailing Docker logs.
- Ordering of sync-then-rebuild in nightly batch (same connection session vs separate tasks) as long as D-05/D-06 hold.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & backlog

- `.planning/REQUIREMENTS.md` — PRUNE-01 through PRUNE-04
- `.planning/BACKLOG.md` — BL-03 acceptance criteria
- `.planning/ROADMAP.md` — Phase 10 goal and success criteria

### Backend implementation

- `backend/src/wheeloffish/core/catalog_sync.py` — full sync, `CachedSeries` deletion on complete sync, `trigger_sync`
- `backend/src/wheeloffish/core/orchestrator.py` — nightly batch, rebuild warnings, `check_provider_reachable`
- `backend/src/wheeloffish/core/playlist/rebuild_inputs.py` — per-row live fetch, `ProviderNotFound` vs generic failures
- `backend/src/wheeloffish/db/models/playlist_series_row.py` — row schema extension point
- `backend/src/wheeloffish/api/routes/playlists.py` — playlist detail API embed for audit slice

### Frontend (unchanged UX)

- `frontend/src/components/playlists/RebuildBanner.tsx` — copy must stay as-is (D-13)
- `frontend/src/components/playlists/TwoPanePicker.tsx` — existing remove flow only

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `catalog_sync.run_chunked_sync` — post-complete `CachedSeries` purge by `synced_at`; pattern for “confident absence” signal.
- `orchestrator.rebuild_playlist` — per-row `fetch_warnings` with `fetch_failure` / `empty_snapshot`; extend to increment counters when provider reachable.
- `orchestrator.run_nightly_batch` — hook point for sync-before-rebuild ordering.
- `check_provider_reachable` in `rebuild_inputs.py` — gate for counting rebuild evidence.
- `RebuildBanner` / `StatusBadge` — partial rebuild surfacing; do not add prune messaging here.

### Established Patterns

- Rebuild row skip is **warning-only** until builder runs (D-14 in orchestrator comments).
- Catalog sync stale `running` recovery at 180s — counts as failed sync for D-04 reset.
- Playlist row delete already exists in editor API — reuse for `manual_removed` audit, no new UX.

### Integration Points

- **Catalog sync completion** — increment counters, auto-prune at end, reset on failure.
- **Rebuild completion** — increment per-row on confident miss; auto-prune at end of successful rebuild.
- **Nightly scheduler** — sync then rebuild per connection/playlist batch.
- **Playlist detail GET** — embed `recent_prune_events[]` without SPA consumption in Phase 10.

</code_context>

<specifics>
## Specific Ideas

- Operator should **not** manage prune lifecycle; system should reach 3/3 quickly via **nightly sync + rebuild**, not three separate logins.
- User asked whether rebuild “checks the server” — yes live per row, and **confident** misses (`empty_snapshot` / `not_found`) should count toward 3/3 when provider is up.
- Rebuild and catalog sync are **complementary evidence channels**, not duplicates of the same signal.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 11:** “View details” diagnostics modal may later show prune events and per-show rebuild warnings; Phase 10 only embeds API data.
- **Explicit “Sync catalog now”** on playlist surfaces — not requested; cadence relies on nightly sync + existing Library/session triggers.
- **Operator toasts** when auto-prune runs — explicitly rejected (silent removal).

</deferred>

---

*Phase: 10-Safe catalog prune*
*Context gathered: 2026-06-02*
