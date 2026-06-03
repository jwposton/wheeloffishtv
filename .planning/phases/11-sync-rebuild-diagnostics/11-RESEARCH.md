# Phase 11: Sync & rebuild diagnostics - Research

**Researched:** 2026-06-02
**Domain:** Operator diagnostics on playlist rebuild/writeback (FastAPI + React SPA)
**Confidence:** HIGH

## Summary

Phase 11 is a **vertical slice on existing infrastructure**: rebuild fetch warnings already persist in `row_outcomes_json.fetch_warnings`, writeback warnings in `writeback_warnings`, and prune audit in `recent_prune_events` on `GET /playlists/{id}` — but only writeback warnings reach the client today, and the UI renders them inline in `WritebackStatus` [VERIFIED: codebase grep]. The phase adds a **backend resolver** that turns raw DB JSON into operator-ready rows (`label`, `reason_code`, `reason_text`, `remediation_hint`, `actions[]`) embedded on `last_rebuild.diagnostics`, plus a **scrollable `Dialog` modal** on playlist detail triggered from `RebuildBanner` when rebuild or writeback is partial/failed.

No new HTTP endpoints or npm/PyPI packages are required. The main engineering risk is **writeback `reason` heterogeneity** (often `str(exc)` from Plex/Jellyfin resolution) — the resolver must normalize known patterns and fall back gracefully per D-18. A dedicated `rebuild_diagnostics.py` module keeps copy mapping out of route handlers and enables focused unit tests.

**Primary recommendation:** Add `wheeloffish/core/rebuild_diagnostics.py` + Pydantic row types; build `diagnostics` only when assembling `last_rebuild` in `_playlist_to_detail`; add `RebuildDiagnosticsDialog.tsx` using existing `Dialog` + `RemoveFromPlaylistDialog` patterns; strip inline lists from `WritebackStatus` on detail (keep `compact` on cards).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Trigger placement (DIAG-01, DIAG-05)

- **D-01:** Single **"View details"** link on **playlist detail only** (`RebuildBanner`); playlist list cards unchanged (compact badges only).
- **D-02:** Show trigger when **rebuild is partial/failed OR writeback is partial/failed** (any warning/error on the latest run).
- **D-03:** **Panel-level** placement — one control at the bottom of `RebuildBanner` when either section has issues (not per-section duplicate buttons).
- **D-04:** Trigger style: **`Button variant="link"`** — secondary detail action, not a primary outline button.

#### Banner vs modal detail (DIAG-05)

- **D-05:** **Remove inline granular lists** from `WritebackStatus` on playlist detail — no bulleted episode warnings in the banner.
- **D-06:** Banner keeps **existing one-line summary copy** only (e.g. "Completed with warnings…"); no per-item lists or counts in banner.
- **D-07:** **Failed rebuild `error_message` moves to modal** — banner shows badge + summary line only; full error text appears in modal Rebuild section.
- **D-08:** Playlist **list cards unchanged** — `WritebackStatus compact` (badge only) as today.

#### Modal information architecture (DIAG-02, DIAG-04)

- **D-09:** **Single scrollable modal** with stacked sections: **Rebuild** → **Shows skipped** → **Episode sync** → **Prune history** (when events exist).
- **D-10:** **Hide empty sections** — only render sections with rows.
- **D-11:** Row format: **label + reason + muted remediation hint** on the line below.
- **D-12:** If modal opens with no structured rows: show **empty state** ("No detailed diagnostics available for this run") with run timestamp — do not silently close.

#### Run history scope

- **D-13:** Modal shows **latest run only** (`last_rebuild`); no run picker in Phase 11.
- **D-14:** Modal header: **title + status badge + relative timestamp** (e.g. "Finished 2h ago").
- **D-15:** **Prune history is playlist-scoped** — render `recent_prune_events[]` from playlist detail GET as its own section (not tied to a specific rebuild run id).
- **D-16:** **No historical run UI** — operator does not need prior-run comparison in the app; Docker/server logs suffice for deeper forensics. Defer run picker entirely.

#### Labels, hints, and actions (DIAG-03, DIAG-04)

- **D-17:** **Backend resolves** friendly copy — each diagnostic row includes `label`, `reason_code`, `reason_text`, `remediation_hint` (and identifiers for fallback).
- **D-18:** Map **known codes only**: `fetch_failure`, `empty_snapshot`, `not_found`, writeback warning reasons, prune event reasons; generic fallback for unknown codes acceptable.
- **D-19:** **Hints + structured actions** — rows include `actions: [{ type, ...params }]` (e.g. `remove_row`, `open_provider`, `open_series`); frontend renders inline link/buttons from API metadata (not hardcoded per reason_code).
- **D-20:** ID fallback: primary **friendly label**; when title missing show **"Unknown show/episode"** with `series_id` / `episode_id` in subdued monospace below.

#### API shape (DIAG-02)

- **D-21:** **Embed diagnostics on existing `GET /playlists/{id}`** — extend `last_rebuild` with a `diagnostics` object; no new endpoint for Phase 11.
- **D-22:** `diagnostics` structure: **`{ rebuild_error?, show_issues[], episode_issues[] }`** — fully resolved rows; prune events remain at playlist level (`recent_prune_events`) and are merged into modal client-side or referenced as a fourth section source.
- **D-23:** Each issue row carries **`actions[]`** per D-19; backend decides which actions apply per reason.
- **D-24:** **`diagnostics` on `last_rebuild` only** — `recent_runs` stay summary-only (no pre-computed diagnostics for unused history).

### Claude's Discretion

- Dialog component choice (`Dialog` vs existing `AlertDialog` pattern) and exact modal width/scroll behavior.
- Exact operator-facing hint strings and action button labels.
- Whether prune section reuses `recent_prune_events` as-is or maps through the same hint/action resolver as rebuild issues.
- How `remove_row` action wires to existing delete-row API from inside the modal (confirm dialog reuse).

### Deferred Ideas (OUT OF SCOPE)

- **Run picker / previous runs** in diagnostics modal — explicitly rejected for Phase 11; logs cover historical forensics.
- **Diagnostics on playlist list cards** — deferred; detail page only.
- **Dedicated `GET .../rebuilds/{id}/diagnostics` endpoint** — not needed while latest-run-only and detail GET embed suffices.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DIAG-01 | Operator can open structured diagnostics from partial/failed rebuild or writeback | `shouldShowDiagnostics()` on `last_rebuild`; `Button variant="link"` at `RebuildBanner` bottom; `RebuildDiagnosticsDialog` |
| DIAG-02 | Lists rebuild errors, per-show fetch warnings, per-episode writeback warnings from latest run API | `diagnostics` built from `error_message`, `row_outcomes_json.fetch_warnings`, `writeback_warnings`; prune via `recent_prune_events` |
| DIAG-03 | Friendly label + raw IDs when labels unavailable | Resolver uses `CachedSeries` + snapshot episode titles; D-20 fallback copy |
| DIAG-04 | Remediation hints + optional actions | Central `REASON_CATALOG` in `rebuild_diagnostics.py`; `actions[]` typed per D-19 |
| DIAG-05 | Compact badges unchanged; diagnostics on-demand | Strip `WritebackStatus` lists when `!compact`; cards keep `compact` only |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Resolve labels/hints/actions from raw run JSON | API / Backend | — | D-17/D-18: server owns copy; avoids hardcoded reason maps in SPA |
| Embed `diagnostics` on playlist detail GET | API / Backend | — | D-21: extend existing `_playlist_to_detail` |
| Persist fetch/writeback warning data | API / Backend (orchestrator) | Database | Already written by `rebuild_playlist` / `push_snapshot` — no schema change |
| "View details" trigger + visibility rules | Browser / Client | — | Reads `last_rebuild` status fields only |
| Diagnostics modal UI + action handlers | Browser / Client | — | Renders API rows; calls existing `removePlaylistRow`, routes, `window.open` |
| Prune history section | Browser / Client | API (embed) | `recent_prune_events` already on detail GET; optional client-side row mapping |
| Compact list-card badges | Browser / Client | — | `PlaylistCard` + `WritebackStatus compact` unchanged |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (project pin) | Playlist detail API | Existing route module [VERIFIED: codebase grep] |
| Pydantic v2 | (project pin) | `RebuildRunSummary` + new diagnostic models | Same pattern as `PruneEventResponse` |
| React 19 + Vite | ^19.2.6 | Playlist detail UI | Existing SPA |
| @base-ui/react/dialog | ^1.5.0 | Modal shell | `ui/dialog.tsx` + `QuickCreatePlaylistDialog` precedent [VERIFIED: codebase grep] |
| @tanstack/react-query | ^5.100 | Detail refresh after row remove | `usePlaylist` / `removePlaylistRow` mutations |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| structlog | (backend) | Resolver logging for unknown codes | When mapping falls back to generic copy |
| vitest + Testing Library | (frontend devDeps) | Modal/trigger tests | Component tests alongside `PlaylistDetailPage.test.tsx` |
| pytest + pytest-asyncio | >=8.0 | API + resolver unit tests | `backend/tests/` layout |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Embed on `GET /playlists/{id}` | Dedicated diagnostics endpoint | Rejected in CONTEXT (D-21 deferred alt) |
| `Dialog` | `AlertDialog` for diagnostics | UI-SPEC locks `Dialog` for scrollable content; AlertDialog for destructive confirm only |
| Frontend reason map | Backend resolver | Rejected by D-17 |

**Installation:** None — no new packages for this phase.

**Version verification:** N/A (no new dependencies).

## Package Legitimacy Audit

> Phase installs **no new external packages**. Existing dependencies only.

| Package | Registry | slopcheck | Disposition |
|---------|----------|-----------|-------------|
| — | — | — | N/A |

**Packages removed due to slopcheck [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Operator (playlist detail)
    │
    ▼
GET /api/v1/playlists/{id}  ──► _playlist_to_detail()
    │                              ├─ _latest_run → last_rebuild
    │                              ├─ build_rebuild_diagnostics(run, db, ctx)
    │                              │     ├─ row_outcomes_json.fetch_warnings
    │                              │     ├─ error_message / writeback_*
    │                              │     └─ CachedSeries + snapshot titles
    │                              └─ recent_prune_events[] (unchanged)
    ▼
RebuildBanner (summary badges only)
    │  partial/failed rebuild OR writeback?
    └─► "View details" link
            ▼
    RebuildDiagnosticsDialog
        ├─ last_rebuild.diagnostics (Rebuild / Shows / Episodes)
        └─ recent_prune_events (Prune history)
            actions: remove_row → DELETE row API
                     open_series → /series?id=
                     open_provider → provider_playlist_open_url
```

### Recommended Project Structure

```
backend/src/wheeloffish/
├── core/
│   └── rebuild_diagnostics.py    # NEW: reason catalog + build_diagnostics()
├── api/
│   ├── schemas/playlists.py      # DiagnosticIssueRow, RebuildDiagnostics, extend RebuildRunSummary
│   └── routes/playlists.py       # Wire diagnostics into last_rebuild only

frontend/src/
├── components/playlists/
│   ├── RebuildDiagnosticsDialog.tsx   # NEW
│   ├── RebuildBanner.tsx              # trigger + modal state; remove inline error (D-07)
│   └── WritebackStatus.tsx            # strip detail lists (D-05)
├── lib/
│   └── rebuildDiagnostics.ts          # shouldShowDiagnostics, runDiagnosticAction
└── api/playlists.ts                   # TS types for diagnostics + recent_prune_events
```

### Pattern 1: Diagnostics builder (backend)

**What:** Pure function `build_rebuild_diagnostics(run, *, db, app_user_id, series_title_map, episode_title_map, provider_open_url)` returning `RebuildDiagnostics | None`.

**When to use:** Only when constructing `last_rebuild` in `_playlist_to_detail` (D-24). Pass `None` for `diagnostics` when `run` is None.

**Example:**

```python
# Pattern — implement in rebuild_diagnostics.py [VERIFIED: codebase grep on data sources]
def build_rebuild_diagnostics(run: RebuildRun, ctx: DiagnosticsContext) -> RebuildDiagnostics:
    show_issues = []
    for w in (run.row_outcomes_json or {}).get("fetch_warnings", []):
        show_issues.append(_resolve_show_issue(w, ctx))
    episode_issues = []
    for w in run.writeback_warnings or []:
        if w.get("episode_id"):
            episode_issues.append(_resolve_episode_issue(w, ctx))
    rebuild_error = _resolve_rebuild_error(run) if run.status == "failed" and run.error_message else None
    return RebuildDiagnostics(
        rebuild_error=rebuild_error,
        show_issues=show_issues,
        episode_issues=episode_issues,
    )
```

Call site change in `playlists.py` [VERIFIED: codebase grep]:

```108:121:backend/src/wheeloffish/api/routes/playlists.py
def _rebuild_run_to_summary(run: RebuildRun) -> RebuildRunSummary:
    return RebuildRunSummary(
        id=run.id,
        status=run.status,
        ...
        writeback_at=run.writeback_at,
    )
```

Replace **only** the `last_rebuild=` assignment (~line 206) with a variant that attaches `diagnostics=build_rebuild_diagnostics(...)` while `recent_runs` keep using `_rebuild_run_to_summary`.

### Pattern 2: Reason catalog (don't hand-roll in routes)

**What:** Dict keyed by `reason_code` → `reason_text`, `remediation_hint`, default `actions`.

| reason_code | Source | Suggested actions |
|-------------|--------|-------------------|
| `fetch_failure` | `orchestrator.py` fetch_warnings | `open_series`, `remove_row` |
| `empty_snapshot` | same | `open_series`, `remove_row` |
| `not_found` | same | `open_series`, `remove_row` |
| `rebuild_failed` | `run.error_message` | `open_provider` if URL exists |
| `writeback_failed` | `run.writeback_error` | `open_provider` |
| `episode_not_found` | normalized from writeback `reason` containing 404/not_found | `open_series` |
| `missing_episode_id` | `provider_writeback.py` | — |
| `catalog_sync` / `operator` | prune `reason` + `event_type` | `open_series` for series_id |

Writeback stored reasons are often **raw exception strings** (`str(exc)`) [VERIFIED: codebase grep] — normalize with substring/heuristic rules before catalog lookup; unknown → `writeback_warning` generic row (D-18).

### Pattern 3: Frontend modal + actions

**What:** Follow `QuickCreatePlaylistDialog` for `Dialog`/`DialogContent`/`max-h-[70vh] overflow-y-auto` per `11-UI-SPEC.md`. Action renderer switches on `action.type`:

```typescript
// Pattern — frontend/src/lib/rebuildDiagnostics.ts
export function runDiagnosticAction(
  action: DiagnosticAction,
  ctx: { playlistId: string; onRemoveRow: (seriesId: string) => void },
) {
  switch (action.type) {
    case "remove_row":
      if (action.series_id) ctx.onRemoveRow(action.series_id)
      break
    case "open_provider":
      if (action.url) window.open(action.url, "_blank", "noopener,noreferrer")
      break
    case "open_series":
      if (action.series_id) window.location.assign(seriesDetailRoute(action.series_id))
      break
  }
}
```

`seriesDetailRoute` already exists [VERIFIED: codebase grep] in `frontend/src/lib/seriesId.ts`. `removePlaylistRow` in `frontend/src/api/playlists.ts` encodes composite IDs in the path.

### Pattern 4: Trigger visibility

```typescript
export function shouldShowDiagnostics(last: RebuildRunSummary | null): boolean {
  if (!last) return false
  const rebuildWarn = last.status === "partial" || last.status === "failed"
  const wb = last.writeback_status
  const writebackWarn = wb === "partial" || wb === "failed"
  return rebuildWarn || writebackWarn
}
```

Note: `writeback_status === "succeeded"` with only info notices (`episode_id: null`) does **not** show trigger unless rebuild is partial/failed — matches D-02 ("warning/error on the latest run").

### Anti-Patterns to Avoid

- **Exposing raw `row_outcomes_json`:** Violates D-17; bloats payload with builder internals.
- **Adding diagnostics to `recent_runs`:** Violates D-24; wastes CPU on unused history.
- **Hardcoding reason strings in React:** Violates D-17/D-19; use API `reason_text` / `actions[].label`.
- **Using AlertDialog for diagnostics body:** Blocks scroll; UI-SPEC requires `Dialog`.
- **Inline `error_message` in banner after D-07:** Duplicate with modal Rebuild section.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Friendly reason copy per code | Ad-hoc strings in routes/components | `rebuild_diagnostics.py` catalog | Single place for D-18 mapping + tests |
| Episode/show title lookup | Custom cache in frontend | `_series_title_map` + snapshot `current_snapshot` | Already used in `_playlist_to_detail` [VERIFIED: codebase grep] |
| Modal accessibility shell | Custom overlay | `components/ui/dialog.tsx` | Base UI + existing playlist dialogs |
| Row delete confirm | New confirm UX | `RemoveFromPlaylistDialog` | Established pattern [VERIFIED: codebase grep] |
| Provider deep link | New URL builder | `provider_playlist_open_url` / `provider_playlist_open_url` on detail | Already on `PlaylistDetailResponse` |

**Key insight:** The hard part is **normalizing heterogeneous writeback reasons**, not UI — invest tests in the resolver module.

## Common Pitfalls

### Pitfall 1: `_rebuild_run_to_summary` lacks DB context

**What goes wrong:** Diagnostics builder cannot resolve series titles.

**Why it happens:** Current helper only accepts `RebuildRun` [VERIFIED: codebase grep].

**How to avoid:** Build diagnostics in `_playlist_to_detail` where `db`, `app_user_id`, and snapshot titles already exist.

**Warning signs:** `label` always "Unknown show" despite rows having `series_title` on playlist.

### Pitfall 2: Episode titles missing when snapshot stale

**What goes wrong:** Writeback warnings reference episodes not in `current_snapshot` (failed rebuild kept old snapshot per D-17).

**Why it happens:** `current_snapshot` comes from latest **succeeded/partial** run with snapshot, not necessarily `last_rebuild` [VERIFIED: codebase grep] lines 176–186 in `playlists.py`.

**How to avoid:** Resolver should also read titles from `last_rebuild`'s own `snapshot_json` when present on the run ORM row, not only playlist-level `current_snapshot`.

### Pitfall 3: Frontend type drift

**What goes wrong:** TypeScript compile errors or silent omission of prune section.

**Why it happens:** `PlaylistDetailResponse` in `frontend/src/api/playlists.ts` lacks `recent_prune_events` though backend sends it [VERIFIED: codebase grep].

**How to avoid:** Wave 0: align TS types with `PruneEventResponse` + `diagnostics` on `RebuildRunSummary`.

### Pitfall 4: Trigger shown but empty modal

**What goes wrong:** Failed rebuild with only `error_message` and empty `fetch_warnings` / `writeback_warnings`.

**How to avoid:** Populate `diagnostics.rebuild_error` row from `error_message`; still satisfy D-12 empty state only when **all** sections including rebuild_error are absent.

### Pitfall 5: Prune section vs rebuild run coupling

**What goes wrong:** Operators assume prune events belong to the displayed rebuild run.

**Why it happens:** D-15 explicitly playlist-scoped.

**How to avoid:** Section heading "Prune history" without run id; optional subtle copy "Recent playlist changes" (discretion).

## Code Examples

### Fetch warnings shape (persisted today)

```python
# orchestrator.py [VERIFIED: codebase grep]
run.row_outcomes_json = {"outcomes": row_outcomes, "fetch_warnings": fetch_warnings}
# fetch_warnings item: {"series_id": str, "reason": "fetch_failure"|"empty_snapshot"|"not_found"}
```

### Writeback warnings shape

```python
# provider_writeback.py [VERIFIED: codebase grep]
warnings.append({"episode_id": episode_id, "reason": str(exc)})
# Info notice: ORPHAN_RECREATED_WARNING — episode_id None, not episode-level diagnostic
```

### Pydantic models (proposed)

```python
class DiagnosticAction(BaseModel):
    type: Literal["remove_row", "open_provider", "open_series"]
    label: str
    series_id: str | None = None
    episode_id: str | None = None
    url: str | None = None

class DiagnosticIssueRow(BaseModel):
    label: str
    reason_code: str
    reason_text: str
    remediation_hint: str
    series_id: str | None = None
    episode_id: str | None = None
    actions: list[DiagnosticAction] = Field(default_factory=list)

class RebuildDiagnostics(BaseModel):
    rebuild_error: DiagnosticIssueRow | None = None
    show_issues: list[DiagnosticIssueRow] = Field(default_factory=list)
    episode_issues: list[DiagnosticIssueRow] = Field(default_factory=list)

class RebuildRunSummary(BaseModel):
    # ... existing fields ...
    diagnostics: RebuildDiagnostics | None = None
```

### Dialog trigger in RebuildBanner (proposed)

```tsx
// After both sections, panel bottom [VERIFIED: 11-UI-SPEC.md + RebuildBanner.tsx]
{shouldShowDiagnostics(lastRebuild) ? (
  <Button variant="link" className="h-auto px-0 self-start" onClick={() => setDiagnosticsOpen(true)}>
    View details
  </Button>
) : null}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline writeback bullet list on detail | Modal-only granular detail | Phase 11 (planned) | Banner stays compact per DIAG-05 |
| fetch_warnings DB-only | API `diagnostics.show_issues` | Phase 11 (planned) | Enables DIAG-02 show-level UI |
| No prune UI on detail | Prune history modal section | Phase 11 (planned) | Consumes Phase 10 embed |

**Deprecated/outdated:**
- `episodeTitlesById` in `RebuildBanner` for warning labels — superseded by backend-resolved labels (CONTEXT code insights).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Prune rows can use `PruneEventResponse` as-is with light client mapping (discretion) | Architecture | Inconsistent hints vs rebuild rows — acceptable per CONTEXT |
| A2 | `writeback_status === "partial"` is the only writeback state that implies episode-level issues worth a trigger when rebuild succeeded | Trigger visibility | May hide edge case: succeeded writeback with episode warnings only — verify against `_finalize_writeback_result` [VERIFIED: codebase grep] sets partial when episode warnings exist |
| A3 | `remove_row` action always targets a playlist series row that still exists | Actions | Stale run after manual remove — DELETE 404 should toast error |

**Note on A2:** [VERIFIED: codebase grep] `_finalize_writeback_result` returns `partial` when episode warnings exist, so trigger logic is consistent.

## Open Questions

1. **Prune section resolver parity**
   - What we know: Backend already returns structured prune events; D-18 lists prune reasons.
   - What's unclear: Whether to run prune events through `rebuild_diagnostics` for hints/actions or map client-side.
   - Recommendation: **Phase 11 default:** client maps `event_type`/`reason` to UI-SPEC copy for speed; optional follow-up unifies in backend if duplication hurts.

2. **Writeback reason normalization depth**
   - What we know: Many reasons are raw exception text.
   - What's unclear: Full taxonomy of Plex/Jellyfin error strings in production.
   - Recommendation: Ship substring rules (`404`, `not_found`, `ProviderNotFound`) + generic fallback; extend catalog as logs reveal patterns.

## Environment Availability

**Step 2.6: SKIPPED** — no new external tools; phase uses existing Python/Node test runners and SQLite/Postgres already configured for the project.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 (backend), vitest (frontend) |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]`; `frontend/vitest.config.ts` |
| Quick run command | `cd backend && pytest tests/unit/test_rebuild_diagnostics.py -x` (Wave 0) |
| Full suite command | `cd backend && pytest tests/ -q` and `cd frontend && npm test -- --run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIAG-01 | View details when partial/failed | unit (frontend) | `cd frontend && npm test -- --run src/components/playlists/RebuildBanner.test.tsx` | ❌ Wave 0 |
| DIAG-02 | API returns diagnostics sections | integration | `cd backend && pytest tests/integration/test_playlists_api.py::test_playlist_detail_diagnostics -x` | ❌ Wave 0 |
| DIAG-02 | Resolver maps fetch_warning codes | unit | `cd backend && pytest tests/unit/test_rebuild_diagnostics.py -x` | ❌ Wave 0 |
| DIAG-03 | Unknown label + series_id fallback | unit | `cd backend && pytest tests/unit/test_rebuild_diagnostics.py::test_unknown_series_label -x` | ❌ Wave 0 |
| DIAG-04 | actions[] present for show issues | unit | `cd backend && pytest tests/unit/test_rebuild_diagnostics.py::test_show_issue_actions -x` | ❌ Wave 0 |
| DIAG-05 | WritebackStatus hides lists on detail | unit | `cd frontend && npm test -- --run src/components/playlists/WritebackStatus.test.tsx` | ❌ Wave 0 |
| PRUNE-03 (regression) | recent_prune_events still embedded | integration | `cd backend && pytest tests/integration/test_playlists_api.py::test_prune_events_in_detail -x` | ✅ |

### Sampling Rate

- **Per task commit:** Backend unit test for touched resolver codes; frontend component test if UI changed.
- **Per wave merge:** `pytest tests/integration/test_playlists_api.py -q` + `npm test -- --run`.
- **Phase gate:** Full backend + frontend test suites green before `/gsd-verify-work`.

### Wave 0 Gaps

- [ ] `backend/tests/unit/test_rebuild_diagnostics.py` — resolver + reason catalog
- [ ] `backend/tests/integration/test_playlists_api.py::test_playlist_detail_diagnostics` — embed on GET detail
- [ ] `frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx` + tests
- [ ] `frontend/src/components/playlists/RebuildBanner.test.tsx` — trigger visibility
- [ ] `frontend/src/components/playlists/WritebackStatus.test.tsx` — compact vs detail
- [ ] `frontend/src/api/playlists.ts` — `RebuildDiagnostics`, `recent_prune_events` types

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Existing `get_current_user` on playlist routes |
| V3 Session Management | no | No session changes |
| V4 Access Control | yes | Diagnostics only via owner-gated `_get_owned_playlist` / detail GET |
| V5 Input Validation | yes | Pydantic response models; no new request body |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR on diagnostics payload | Information Disclosure | Same gate as playlist detail — no new public endpoint [VERIFIED: Phase 10 research pattern] |
| Open redirect via `open_provider` action URL | Tampering | Backend only emits `provider_playlist_open_url` from server-side builder, not user input |
| XSS via `error_message` / exception text in modal | Information Disclosure | React text nodes escape by default; avoid `dangerouslySetInnerHTML` |

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory found in the workspace. Follow existing conventions: FastAPI + Pydantic schemas, React function components, `@/` imports, Base UI dialog primitives, pytest/vitest test layout.

## Sources

### Primary (HIGH confidence)

- Codebase: `backend/src/wheeloffish/core/orchestrator.py` — fetch_warnings persistence
- Codebase: `backend/src/wheeloffish/core/provider_writeback.py` — writeback warning shape
- Codebase: `backend/src/wheeloffish/api/routes/playlists.py` — `_rebuild_run_to_summary`, `_playlist_to_detail`, prune embed
- Codebase: `frontend/src/components/playlists/RebuildBanner.tsx`, `WritebackStatus.tsx`
- `.planning/phases/11-sync-rebuild-diagnostics/11-CONTEXT.md` — locked decisions
- `.planning/phases/11-sync-rebuild-diagnostics/11-UI-SPEC.md` — modal contract

### Secondary (MEDIUM confidence)

- `.planning/phases/10-safe-catalog-prune/10-RESEARCH.md` — prune embed auth pattern
- `.planning/BACKLOG.md` BL-04 — acceptance criteria alignment

### Tertiary (LOW confidence)

- None required for core architecture; writeback exception string taxonomy is production-dependent (see Open Questions).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; patterns verified in repo
- Architecture: HIGH — clear extension points in `playlists.py` and `RebuildBanner`
- Pitfalls: MEDIUM — writeback reason normalization may need iteration in production

**Research date:** 2026-06-02  
**Valid until:** 2026-07-02 (stable domain; 7 days if writeback catalog expands)

## RESEARCH COMPLETE
