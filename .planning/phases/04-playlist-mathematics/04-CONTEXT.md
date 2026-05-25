# Phase 4: Playlist mathematics - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a **pure, testable playlist generator** that turns a configured `Playlist` plus live per-series episode snapshots into a fresh ordered output list each rebuild. Implements PLT-01–06 algorithm semantics and SCH-02 multipart rules for **ordered** rows. No DB persistence, REST CRUD, SPA, scheduler, or WheelOfFish admin (Phases 5–6).

**In scope:** In-memory domain models (`Playlist`, rows, build results); `PlaylistBuilder` pipeline (slot allocation, ordered serial picks from resume, disordered random picks, completion policies, multipart expansion); golden-vector unit tests; optional `last_viewed_at` on `Episode` DTO for disordered anti-repeat.

**Out of scope:** Alembic migrations, playlist storage, per-playlist schedule execution, manual-rebuild API/UI, MediaProvider HTTP inside builder, episode SQLite cache, season-complete completion event (v1), WheelOfFish, playlist export to Plex/Jellyfin.

</domain>

<decisions>
## Implementation Decisions

### Slot allocation across shows
- **D-01:** Default slot allocation = **Wild shuffle** (uniform random choice of active row per slot).
- **D-02:** `Playlist` includes optional **`slot_allocation`**: `wild` | `balanced` | `round_robin`. UI labels: Wild shuffle / Balanced mix / Round-robin. UI deferred to Phase 5+; algorithm supports all three in Phase 4.

### Disordered feather picking
- **D-03:** Disordered pool = **all episodes minus last 15 watched** for that user/show, ranked by provider **`last_viewed_at`** descending.
- **D-04:** **No duplicate episode** from the same show within one rebuild.
- **D-05:** If eligible pool is empty (small show / everything recently watched) → **fall back to full episode list**.
- **D-06:** Extend `Episode` DTO + Plex/Jellyfin mappers with optional **`last_viewed_at`** (derived from existing episode list fetch — no separate history API).

### Multipart blocks
- **D-07:** **Ordered rows:** when resume lands on a multipart episode, emit a **contiguous block from that part forward** through the rest of the group (sorted by `part_index`).
- **D-08:** **Disordered rows:** if random pick hits **any part** of a multipart group → emit the **full block** (all parts, sorted by `part_index`).
- **D-09:** Multipart full-block expansion **overrides** last-15 exclusion for those parts (user can skip in Plex).
- **D-10:** SCH-02 adjacency enforcement applies to **ordered** multipart blocks; disordered uses full-block product rule above.

### Completion events & policies
- **D-11:** Completion event = **series complete only** for v1 (`ResumeService` / all episodes complete per Phase 2 thresholds). **No season-complete** event in v1.
- **D-12:** System default completion policy = **`remove`** when series completes.
- **D-13:** Each **playlist** has a configurable **default completion policy** (`remove` | `restart` | `disordered`) applied to new rows.
- **D-14:** **Per-row override** allowed when adding a show; row policy wins over playlist default.
- **D-15:** Completion policies evaluated **at start of build** before slot allocation.

### Rebuild semantics & output length
- **D-16:** Each rebuild (scheduled or manual) produces a **fresh playlist** — prior output is replaced, not appended or refilled as a running queue.
- **D-17:** **Ordered rows:** start at **resume / up-next**, proceed **serially forward** via `ResumeService` + `order_episodes()` (same semantics as `/resume` endpoint).
- **D-18:** **Disordered rows:** new random picks each rebuild from eligible pool (D-03).
- **D-19:** Default **`episode_count` = 20 slots** per playlist; user configurable per playlist.
- **D-20:** **N = slot count** — one slot may expand to multiple episodes via multipart; total output length may exceed N.
- **D-21:** If active rows cannot fill all N slots → **emit fewer**; surface `slots_filled < slots_requested` in build result (Phase 5 UI).
- **D-22:** Per-playlist **schedule** is user-configurable — orchestrated in **Phase 5**; Phase 4 builder accepts inputs only.

### Rebuild identity & determinism
- **D-23:** **Manual “Rebuild now”** and **scheduled rebuild** invoke the **same** `PlaylistBuilder` pipeline with current live episode snapshots.
- **D-24:** Each rebuild invocation produces **fresh stochastic output** (not frozen for calendar day). Seed per run (e.g. rebuild run id / timestamp passed by Phase 5 orchestrator). Tests use explicit fixed seeds.

### Claude's Discretion
- Exact enum names, `core/playlist/` module layout, balanced/round-robin allocation algorithms, re-roll attempt caps on tiny pools, Hypothesis vs golden-vector-only property tests, Jellyfin `last_viewed_at` field mapping — as long as decisions above and Phase 2 resume/multipart contracts are met.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Product vision: mixed random slots, ordered resume binge, disordered feathers, multipart adjacency
- `.planning/REQUIREMENTS.md` — PLT-01…PLT-06, SCH-02 (algorithm portion)
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria
- `.planning/phases/04-playlist-mathematics/04-RESEARCH.md` — Architecture, patterns, test map

### Prior phase context
- `.planning/phases/02-media-ingestion-catalogs/02-CONTEXT.md` — D-10–D-13 resume semantics, D-15 live episode fetch, D-21 multipart fields
- `.planning/phases/03-minimal-operator-spa-shell/03-CONTEXT.md` — Phase boundary (no playlist CRUD in Phase 3)

### Existing code (reuse — do not reimplement)
- `backend/src/wheeloffish/core/resume.py` — `ResumeService`, `order_episodes`, `classify_watch`
- `backend/src/wheeloffish/domain/dto.py` — `Episode`, `ResumeCursor`
- `backend/src/wheeloffish/integrations/plex/mappers.py` — `multipartGroupId`, `partIndex`; add `lastViewedAt`
- `backend/src/wheeloffish/integrations/jellyfin/mappers.py` — Jellyfin play metadata
- `backend/src/wheeloffish/api/routes/catalog.py` — Episode + resume fetch contract for Phase 5 caller
- `backend/tests/unit/test_resume_service.py` — Golden-vector test pattern to mirror

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ResumeService.compute()` — single source of truth for ordered start index; builder must not fork hybrid on-deck logic.
- `order_episodes()` — specials-after-finale ordering for all serial walks.
- `Episode.multipart_group_id` / `part_index` — native multipart grouping from Plex/Jellyfin mappers.
- `list_episodes()` + `get_on_deck_episode()` on `PlexProvider` — Phase 5 fetches inputs; episode list already includes fields needed for `last_viewed_at`.

### Established Patterns
- Pure domain logic in `backend/src/wheeloffish/core/` with Pydantic DTOs in `domain/`.
- Golden-vector pytest fixtures (see `test_resume_service.py`).
- Phase boundary: builder consumes in-memory inputs; no httpx/DB inside `core/playlist/`.

### Integration Points
- Phase 5 orchestrator: fetch episodes + on_deck per series → `SeriesRebuildInput` → `PlaylistBuilder.build(playlist, inputs, rebuild_seed)` → persist output.
- Disordered last-15: computed client-side from episode snapshots after mapper adds `last_viewed_at`.

</code_context>

<specifics>
## Specific Ideas

- Slot allocation UX: expose as **Wild shuffle / Balanced mix / Round-robin** under advanced playlist settings (not internal jargon).
- Disordered anti-repeat: exclude **last 15 watched** from random pool; multipart full block can re-include excluded parts.
- Ordered continuity comes from **Plex watch state**, not carrying over yesterday's list items — fresh menu each rebuild.
- Default playlist size **20 slots**; user sets per playlist.

</specifics>

<deferred>
## Deferred Ideas

- **Season-complete** completion event and per-season policies — v2 if users request pause-between-seasons behavior.
- **Emission history** (track episodes we put on prior playlists) as second anti-repeat layer — optional Phase 5+ if provider watch history insufficient for skipped-list-item case.
- Per-playlist schedule UI + cron/APScheduler — Phase 5.
- WheelOfFish global disordered playlist — Phase 6.

</deferred>

---

*Phase: 4-Playlist mathematics*
*Context gathered: 2026-05-25*
