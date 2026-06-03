# Phase 11: Sync & rebuild diagnostics - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

As an operator, when a rebuild or provider sync is partial/failed, I can open a structured diagnostics modal from the playlist detail page and see exactly what failed at rebuild, show, and episode granularity — with friendly labels, remediation hints, and optional actions — without shell or DB access. Compact status badges on list cards and in the banner stay unchanged; granular detail moves on-demand into the modal. Phase 11 exposes show-level fetch warnings currently stored only in `row_outcomes_json` and consumes `recent_prune_events` already embedded on playlist detail GET.

</domain>

<decisions>
## Implementation Decisions

### Trigger placement (DIAG-01, DIAG-05)

- **D-01:** Single **"View details"** link on **playlist detail only** (`RebuildBanner`); playlist list cards unchanged (compact badges only).
- **D-02:** Show trigger when **rebuild is partial/failed OR writeback is partial/failed** (any warning/error on the latest run).
- **D-03:** **Panel-level** placement — one control at the bottom of `RebuildBanner` when either section has issues (not per-section duplicate buttons).
- **D-04:** Trigger style: **`Button variant="link"`** — secondary detail action, not a primary outline button.

### Banner vs modal detail (DIAG-05)

- **D-05:** **Remove inline granular lists** from `WritebackStatus` on playlist detail — no bulleted episode warnings in the banner.
- **D-06:** Banner keeps **existing one-line summary copy** only (e.g. "Completed with warnings…"); no per-item lists or counts in banner.
- **D-07:** **Failed rebuild `error_message` moves to modal** — banner shows badge + summary line only; full error text appears in modal Rebuild section.
- **D-08:** Playlist **list cards unchanged** — `WritebackStatus compact` (badge only) as today.

### Modal information architecture (DIAG-02, DIAG-04)

- **D-09:** **Single scrollable modal** with stacked sections: **Rebuild** → **Shows skipped** → **Episode sync** → **Prune history** (when events exist).
- **D-10:** **Hide empty sections** — only render sections with rows.
- **D-11:** Row format: **label + reason + muted remediation hint** on the line below.
- **D-12:** If modal opens with no structured rows: show **empty state** ("No detailed diagnostics available for this run") with run timestamp — do not silently close.

### Run history scope

- **D-13:** Modal shows **latest run only** (`last_rebuild`); no run picker in Phase 11.
- **D-14:** Modal header: **title + status badge + relative timestamp** (e.g. "Finished 2h ago").
- **D-15:** **Prune history is playlist-scoped** — render `recent_prune_events[]` from playlist detail GET as its own section (not tied to a specific rebuild run id).
- **D-16:** **No historical run UI** — operator does not need prior-run comparison in the app; Docker/server logs suffice for deeper forensics. Defer run picker entirely.

### Labels, hints, and actions (DIAG-03, DIAG-04)

- **D-17:** **Backend resolves** friendly copy — each diagnostic row includes `label`, `reason_code`, `reason_text`, `remediation_hint` (and identifiers for fallback).
- **D-18:** Map **known codes only**: `fetch_failure`, `empty_snapshot`, `not_found`, writeback warning reasons, prune event reasons; generic fallback for unknown codes acceptable.
- **D-19:** **Hints + structured actions** — rows include `actions: [{ type, ...params }]` (e.g. `remove_row`, `open_provider`, `open_series`); frontend renders inline link/buttons from API metadata (not hardcoded per reason_code).
- **D-20:** ID fallback: primary **friendly label**; when title missing show **"Unknown show/episode"** with `series_id` / `episode_id` in subdued monospace below.

### API shape (DIAG-02)

- **D-21:** **Embed diagnostics on existing `GET /playlists/{id}`** — extend `last_rebuild` with a `diagnostics` object; no new endpoint for Phase 11.
- **D-22:** `diagnostics` structure: **`{ rebuild_error?, show_issues[], episode_issues[] }`** — fully resolved rows; prune events remain at playlist level (`recent_prune_events`) and are merged into modal client-side or referenced as a fourth section source.
- **D-23:** Each issue row carries **`actions[]`** per D-19; backend decides which actions apply per reason.
- **D-24:** **`diagnostics` on `last_rebuild` only** — `recent_runs` stay summary-only (no pre-computed diagnostics for unused history).

### Claude's Discretion

- Dialog component choice (`Dialog` vs existing `AlertDialog` pattern) and exact modal width/scroll behavior.
- Exact operator-facing hint strings and action button labels.
- Whether prune section reuses `recent_prune_events` as-is or maps through the same hint/action resolver as rebuild issues.
- How `remove_row` action wires to existing delete-row API from inside the modal (confirm dialog reuse).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & backlog

- `.planning/REQUIREMENTS.md` — DIAG-01 through DIAG-05
- `.planning/BACKLOG.md` — BL-04 acceptance criteria
- `.planning/ROADMAP.md` — Phase 11 goal and success criteria

### Prior phase context

- `.planning/phases/10-safe-catalog-prune/10-CONTEXT.md` — D-19 prune API embed; rebuild banner copy unchanged; `row_outcomes_json` warning codes

### Backend

- `backend/src/wheeloffish/core/orchestrator.py` — `fetch_warnings`, `row_outcomes_json` shape, rebuild/writeback flow
- `backend/src/wheeloffish/api/routes/playlists.py` — playlist detail GET, `_rebuild_run_to_summary`, `recent_prune_events` embed
- `backend/src/wheeloffish/api/schemas/playlists.py` — `RebuildRunSummary`, `PlaylistDetailResponse`, `PruneEventResponse`
- `backend/src/wheeloffish/db/models/rebuild_run.py` — `row_outcomes_json`, writeback fields

### Frontend

- `frontend/src/components/playlists/RebuildBanner.tsx` — trigger placement, summary-only banner
- `frontend/src/components/playlists/WritebackStatus.tsx` — strip inline lists on detail; keep compact on cards
- `frontend/src/components/playlists/StatusBadge.tsx` — unchanged compact badges
- `frontend/src/components/playlists/RemoveFromPlaylistDialog.tsx` — pattern for modal actions
- `frontend/src/pages/PlaylistDetailPage.tsx` — hosts RebuildBanner and modal state
- `frontend/src/api/playlists.ts` — `RebuildRunSummary`, `PlaylistDetailResponse` types

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `RebuildBanner` + `StatusBadge` + `WritebackStatus` — banner shell; add link trigger and modal host.
- `WritebackStatus.compact` — already correct for playlist cards; detail page stops passing full warning lists inline.
- `RemoveFromPlaylistDialog` / Base UI dialog patterns — modal shell and confirm-before-remove for `remove_row` actions.
- `episodeTitlesById(snapshot)` in `RebuildBanner` — pattern for label resolution; superseded by backend-resolved labels in API.
- `recent_prune_events` on playlist detail GET (Phase 10) — ready for Prune history section.

### Established Patterns

- Rebuild warnings stored in DB as `row_outcomes_json.fetch_warnings` with reasons `fetch_failure`, `empty_snapshot`, `not_found` — **not yet in API response**.
- Writeback warnings already in `RebuildRunSummary.writeback_warnings` with `episode_id` + `reason`.
- Phase 10: generic rebuild banner copy must stay; diagnostics are additive via modal only.

### Integration Points

- Extend `_rebuild_run_to_summary` (or adjacent builder) to assemble `diagnostics` from `row_outcomes_json` + writeback fields + cached series/episode titles.
- `RebuildBanner` → open modal with `last_rebuild.diagnostics` + `recent_prune_events` + playlist rows for actions.
- Action handlers: existing row delete API, provider open URL, optional series detail route.

</code_context>

<specifics>
## Specific Ideas

- Operator initially thought diagnostics might already exist — they do **not** (inline writeback lists only; no show-level fetch UI; no modal).
- Operator **does not want historical run UI** — latest run in modal is sufficient; logs for anything older.
- User prefers **recommendations** on each discuss question going forward.

</specifics>

<deferred>
## Deferred Ideas

- **Run picker / previous runs** in diagnostics modal — explicitly rejected for Phase 11; logs cover historical forensics.
- **Diagnostics on playlist list cards** — deferred; detail page only.
- **Dedicated `GET .../rebuilds/{id}/diagnostics` endpoint** — not needed while latest-run-only and detail GET embed suffices.

</deferred>

---

*Phase: 11-Sync & rebuild diagnostics*
*Context gathered: 2026-06-02*
