# Phase 6: Library & playlist assignment - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Repurpose Phase 6 from cancelled **Admin WheelOfFish** to **Library-centric playlist assignment UX**.

**In scope:**
- Rename nav **Browse → Library** (user-facing label; route may stay `/browse` or gain `/library` alias — planner discretion)
- **Library tiles:** visible **⋯** action + shared context menu on **right-click and long-press** → add to existing playlist or create new
- **Series detail page:** same add-to-playlist menu **plus primary “Add to playlist” button**; enrich layout with **provider-sourced metadata** (summary, genres, content rating, studio/network when available) — IMDb-*like* presentation using Plex/Jellyfin data, **not** an external IMDb API
- **Quick create:** inline name prompt with **“Advanced…”** link to full playlist form (`/playlists/new`) with show pre-selected
- **Playlist edit:** replace search-box `SeriesPicker` with **two-pane tile picker** — **In playlist | Available to add**; both panes use poster tile grids + **name search** (shared toolbar pattern with Library)
- **Row settings** (ordered/random, completion policy): click tile in **In playlist** pane → **bottom sheet / drawer**
- **Responsive:** side-by-side panes on `md+`; **tabs** on smaller viewports
- API support for append/add/remove row without full PUT where needed (planner designs)
- Retire **ADM-01 / ADM-02**; update ROADMAP, PROJECT, REQUIREMENTS

**Out of scope:**
- Global admin WheelOfFish playlist (cancelled)
- Genre / animated / advanced filter chips beyond **name search** (deferred until metadata sync spike proves fields — Phase 7 or follow-up)
- Cast/crew credits, external links, trailers (unless trivial from existing provider fields — default defer Phase 7)
- Export playlists to Plex/Jellyfin
- Replacing resume preview on series detail (keep `ResumePreview`; metadata sits alongside it)

</domain>

<decisions>
## Implementation Decisions

### Scope & requirements (roadmap amendment)
- **D-01:** **Cancel ADM-01 and ADM-02** — no server-wide WheelOfFish playlist or admin-only global membership UI in v1.
- **D-02:** Phase 6 renamed **“Library & playlist assignment”** (slug: `library-playlist-assignment`). Update PROJECT.md to remove household WheelOfFish promise.

### Library (formerly Browse)
- **D-03:** Nav label **Library**; page purpose = catalog discovery **and** playlist assignment hub.
- **D-04:** Each series tile exposes a **visible ⋯ control** (primary affordance). **Right-click** and **long-press** open the **same** menu (secondary; do not rely on right-click alone).
- **D-05:** Context menu actions: **Add to existing playlist…** (submenu or dialog listing user playlists) · **Create new playlist…** (see D-08).
- **D-06:** Tile click still navigates to series detail; ⋯ / menu actions **stop propagation** so they do not trigger navigation.
- **D-07:** v1 filter on Library = **name search only** (reuse debounced search + infinite scroll). Additional filters deferred pending metadata research.

### Series detail page
- **D-08:** **Create new playlist** from quick-add: **inline name prompt** → create + add series immediately; **“Advanced…”** opens full create form with series pre-selected (decision 2C).
- **D-09:** Series detail includes **shared `AddToPlaylist` UI** — context-style menu **and** a **primary “Add to playlist” button** (decisions 1A + 1C).
- **D-10:** Enrich series detail with **IMDb-like layout** using **cached provider metadata** — target fields: **summary/blurb**, **genres**, **content rating**, **studio/network**, **year**, hero poster (already have thumb). Source = Plex/Jellyfin sync fields stored in `cached_series` / `provider_metadata` — **no external IMDb/TMDB API**.
- **D-11:** Metadata enrichment requires a **sync/API extension wave** in this phase (research maps Plex `summary`, `Genre`, `contentRating`, `studio` — persist during catalog sync). If Jellyfin parity is costly, ship Plex-first with Jellyfin stub fields (planner + research).
- **D-12:** Keep existing **resume preview** block on detail; metadata + add-to-playlist sit above or beside it in a readable hero + details layout.

### Playlist edit (two-pane picker)
- **D-13:** Replace `SeriesPicker` search list with **two-pane tile UI** on create/edit: **In playlist** (left/top tab) | **Available to add** (right/bottom tab).
- **D-14:** Both panes: poster **tile grid** (reuse `SeriesGrid` / `SeriesCard` patterns), independent **name search** per pane or shared search filtering both — planner picks simplest consistent UX (default: one search bar filters Available; In pane shows all members unless search narrows).
- **D-15:** Add/remove: click tile in Available → add to In; remove via tile action or sheet in In pane.
- **D-16:** **Row settings** (ordered/disordered, completion policy override): **click tile in In playlist pane → bottom sheet / drawer** (decision 3A). Defaults: ordered + remove (match current create behavior).
- **D-17:** **Responsive layout:** `md+` side-by-side columns; **&lt;md` tabbed **In playlist (N)** | **Add shows** (decision 4A).
- **D-18:** Playlist-level settings (name, episode count, schedule, slot allocation, default completion policy) remain in form sections **above** the two-pane picker (reuse `PlaylistForm` sections 1–2).

### Shared components & API
- **D-19:** Extract shared **`AddToPlaylistMenu`** (or equivalent) used from Library tiles, series detail button, and optionally playlist Available pane.
- **D-20:** Prefer **append/remove row API** endpoints (or PATCH rows) so Library quick-add does not require full playlist PUT — planner specifies; must remain owner-scoped (D-18 from Phase 5).
- **D-21:** Deprecate/remove standalone search-only `SeriesPicker` once two-pane editor ships.

### Claude's Discretion
- `/browse` vs `/library` route path and redirects; exact sheet vs drawer component; playlist picker dialog vs submenu; whether Available pane supports infinite scroll identical to Library; metadata field column vs JSON-only storage; Jellyfin metadata parity depth; mobile long-press delay timing.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Updated product vision (WheelOfFish removed)
- `.planning/REQUIREMENTS.md` — ADM-01/02 cancelled; PLT-03 extended via this phase
- `.planning/ROADMAP.md` — Phase 6 goal (repurposed)
- `.planning/STATE.md` — Phase 5 complete; Phase 6 next

### Prior phase context
- `.planning/phases/05-orchestration-scheduling/05-CONTEXT.md` — D-25 catalog picker intent (superseded by this phase for UX), playlist CRUD, ownership
- `.planning/phases/05-orchestration-scheduling/05-UI-SPEC.md` — shadcn/base-nova design system
- `.planning/phases/03-minimal-operator-spa-shell/03-CONTEXT.md` — Browse SPA patterns, auth, AppShell
- `.planning/phases/02-media-ingestion-catalogs/02-CONTEXT.md` — cached_series, catalog sync, D-14 metadata cache scope

### Implementation anchors (code)
- `frontend/src/pages/BrowsePage.tsx` — Library page baseline
- `frontend/src/components/browse/SeriesGrid.tsx`, `SeriesCard.tsx` — tile grid reuse
- `frontend/src/pages/SeriesDetailPage.tsx` — detail enrichment target
- `frontend/src/components/playlists/PlaylistForm.tsx`, `SeriesPicker.tsx` — replace picker UX
- `backend/src/wheeloffish/api/routes/playlists.py` — row CRUD extension point
- `backend/src/wheeloffish/integrations/plex/mappers.py` — extend `map_series` for metadata fields
- `backend/src/wheeloffish/db/models/cached_series.py` — persistence for enriched metadata

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BrowsePage` + `useSeriesInfiniteQuery` + `BrowseToolbar` — Library infinite scroll and name search
- `SeriesGrid` / `SeriesCard` / `SeriesPoster` — poster tiles for both panes
- `PlaylistForm` — playlist-level settings sections; row state model (`SeriesRow`)
- Playlist CRUD hooks in `frontend/src/api/playlists.ts`
- `cached_series.provider_metadata` JSON — extension point for genres/summary without immediate migration (research may add columns)

### Established Patterns
- TanStack Query for catalog and playlists; debounced search 300ms
- shadcn Sheet/Dialog patterns from delete confirmation on detail page
- Owner-scoped API 404 pattern (Phase 5 D-18)

### Integration Points
- Catalog sync (`catalog_sync.py`) must persist enriched series fields before detail page can render them offline
- Library tile menu → playlist append API → invalidate playlist detail query
- Series detail “Advanced…” → navigate to `PlaylistFormPage` with query param or state for pre-selected series

</code_context>

<specifics>
## Specific Ideas

- User explicitly rejected right-click-only web UX — visible ⋯ is mandatory
- “IMDb-like” means rich **read** page (poster, title, year, blurb, genres, rating badge) — not external integrations
- Two-pane playlist editor: **in** vs **available** — not search box list
- WheelOfFish admin playlist **scrapped** — household random mode is just another user playlist if desired

</specifics>

<deferred>
## Deferred Ideas

- **Genre / animated / library filter chips** on Library and playlist Available pane — after metadata sync spike identifies reliable fields (likely Phase 7)
- **Cast, crew, episode list browser on detail** — beyond resume preview (Phase 7 polish unless cheap)
- **“Add from browse” only** without detail enrichment — superseded by D-09–D-12
- **Household WheelOfFish global playlist** — cancelled (ADM-01/02)

</deferred>

---

*Phase: 06-library-playlist-assignment*
*Context gathered: 2026-05-25*
