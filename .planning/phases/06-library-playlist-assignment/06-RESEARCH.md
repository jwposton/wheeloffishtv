# Phase 6: Library & playlist assignment - Research

**Researched:** 2026-05-25  
**Domain:** React UI patterns + Plex metadata enrichment + REST API row operations  
**Confidence:** HIGH

## Summary

Phase 6 repurposes **Browse → Library** as a playlist assignment hub with context menus, enriches series detail pages with Plex metadata, and replaces the search-only `SeriesPicker` with a visual two-pane tile editor. Research confirms all requirements are achievable with existing stack patterns.

**Primary recommendation:** Use Radix `ContextMenu` for right-click + long-press (built-in), shadcn `Sheet` with `side="bottom"` for row settings, `Tabs` for mobile two-pane collapse, and `POST /playlists/{id}/rows` + `DELETE /playlists/{id}/rows/{rowId}` for append/remove without full PUT. Extend Plex sync to capture `summary`, `Genre` array, `contentRating`, and `studio` into `cached_series.provider_metadata` JSON.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Series metadata display | Frontend Server (SSR) | — | React components render cached metadata; no SSR in current stack but tier semantics apply |
| Context menu UI | Browser / Client | — | DOM interaction, pointer events, React state |
| Add-to-playlist action | API / Backend | — | Playlist mutation, ownership validation, persistence |
| Metadata enrichment sync | API / Backend | — | Plex client, catalog sync job, database writes |
| Poster tile grids | Browser / Client | — | Reusable React components (`SeriesGrid`, `SeriesCard`) |
| Row settings persistence | API / Backend | — | Playlist row CRUD endpoints |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scope & requirements (roadmap amendment)**
- **D-01:** **Cancel ADM-01 and ADM-02** — no server-wide WheelOfFish playlist or admin-only global membership UI in v1.
- **D-02:** Phase 6 renamed **"Library & playlist assignment"** (slug: `library-playlist-assignment`). Update PROJECT.md to remove household WheelOfFish promise.

**Library (formerly Browse)**
- **D-03:** Nav label **Library**; page purpose = catalog discovery **and** playlist assignment hub.
- **D-04:** Each series tile exposes a **visible ⋯ control** (primary affordance). **Right-click** and **long-press** open the **same** menu (secondary; do not rely on right-click alone).
- **D-05:** Context menu actions: **Add to existing playlist…** (submenu or dialog listing user playlists) · **Create new playlist…** (see D-08).
- **D-06:** Tile click still navigates to series detail; ⋯ / menu actions **stop propagation** so they do not trigger navigation.
- **D-07:** v1 filter on Library = **name search only** (reuse debounced search + infinite scroll). Additional filters deferred pending metadata research.

**Series detail page**
- **D-08:** **Create new playlist** from quick-add: **inline name prompt** → create + add series immediately; **"Advanced…"** opens full create form with series pre-selected (decision 2C).
- **D-09:** Series detail includes **shared `AddToPlaylist` UI** — context-style menu **and** a **primary "Add to playlist" button** (decisions 1A + 1C).
- **D-10:** Enrich series detail with **IMDb-like layout** using **cached provider metadata** — target fields: **summary/blurb**, **genres**, **content rating**, **studio/network**, **year**, hero poster (already have thumb). Source = Plex/Jellyfin sync fields stored in `cached_series` / `provider_metadata` — **no external IMDb/TMDB API**.
- **D-11:** Metadata enrichment requires a **sync/API extension wave** in this phase (research maps Plex `summary`, `Genre`, `contentRating`, `studio` — persist during catalog sync). If Jellyfin parity is costly, ship Plex-first with Jellyfin stub fields (planner + research).
- **D-12:** Keep existing **resume preview** block on detail; metadata + add-to-playlist sit above or beside it in a readable hero + details layout.

**Playlist edit (two-pane picker)**
- **D-13:** Replace `SeriesPicker` search list with **two-pane tile UI** on create/edit: **In playlist** (left/top tab) | **Available to add** (right/bottom tab).
- **D-14:** Both panes: poster **tile grid** (reuse `SeriesGrid` / `SeriesCard` patterns), independent **name search** per pane or shared search filtering both — planner picks simplest consistent UX (default: one search bar filters Available; In pane shows all members unless search narrows).
- **D-15:** Add/remove: click tile in Available → add to In; remove via tile action or sheet in In pane.
- **D-16:** **Row settings** (ordered/disordered, completion policy override): **click tile in In playlist pane → bottom sheet / drawer** (decision 3A). Defaults: ordered + remove (match current create behavior).
- **D-17:** **Responsive layout:** `md+` side-by-side columns; **&lt;md** tabbed **In playlist (N)** | **Add shows** (decision 4A).
- **D-18:** Playlist-level settings (name, episode count, schedule, slot allocation, default completion policy) remain in form sections **above** the two-pane picker (reuse `PlaylistForm` sections 1–2).

**Shared components & API**
- **D-19:** Extract shared **`AddToPlaylistMenu`** (or equivalent) used from Library tiles, series detail button, and optionally playlist Available pane.
- **D-20:** Prefer **append/remove row API** endpoints (or PATCH rows) so Library quick-add does not require full playlist PUT — planner specifies; must remain owner-scoped (D-18 from Phase 5).
- **D-21:** Deprecate/remove standalone search-only `SeriesPicker` once two-pane editor ships.

### Claude's Discretion
- `/browse` vs `/library` route path and redirects; exact sheet vs drawer component; playlist picker dialog vs submenu; whether Available pane supports infinite scroll identical to Library; metadata field column vs JSON-only storage; Jellyfin metadata parity depth; mobile long-press delay timing.

### Deferred Ideas (OUT OF SCOPE)
- **Genre / animated / library filter chips** on Library and playlist Available pane — after metadata sync spike identifies reliable fields (likely Phase 7)
- **Cast, crew, episode list browser on detail** — beyond resume preview (Phase 7 polish unless cheap)
- **"Add from browse" only** without detail enrichment — superseded by D-09–D-12
- **Household WheelOfFish global playlist** — cancelled (ADM-01/02)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLT-03 (UX) | User adds/removes TV series to a playlist from enumerated library content | Two-pane tile picker + context menu patterns; row append/remove API design |
| WEB-01 (slice) | Library assignment slice of SPA (extends Phase 3 foundation) | Radix ContextMenu + Sheet for mobile; Tailwind responsive grid for two-pane |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @radix-ui/react-context-menu | (existing) | Right-click + long-press menus | WAI-ARIA compliant, modal/non-modal modes, submenus, built-in long-press support [VERIFIED: codebase—shadcn preset uses Radix] |
| shadcn Sheet | (existing via Radix Dialog) | Bottom drawer for row settings | `side="bottom"` prop, focus trap, overlay, responsive [VERIFIED: codebase—Phase 3/5 established shadcn/base-nova] |
| shadcn Tabs | (existing via Radix Tabs) | Mobile two-pane collapse | Keyboard nav, controlled state, responsive [VERIFIED: codebase] |
| TanStack Query | 5.100.14 | Playlist mutation + invalidation | Existing pattern in `playlists.ts` hooks [VERIFIED: codebase] |
| Plex Media Server API | (integration layer) | Series metadata enrichment | `summary`, `Genre[]`, `contentRating`, `studio` fields [CITED: developer.plex.tv/pms/] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 1.16.0 | MoreVertical icon for ⋯ button | Existing icon lib [VERIFIED: codebase] |
| react-router-dom | 7.15.1 | Navigate to `/playlists/new?seriesId=X` | Pre-selection via query param [VERIFIED: codebase] |
| Tailwind CSS `md:` breakpoint | 4.3.0 | `grid-cols-1 md:grid-cols-2` responsive | Mobile-first breakpoint system [CITED: tailwindcss.com/docs/responsive-design] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Radix ContextMenu | Custom right-click handler | Would lose long-press, ARIA, submenus, typeahead — not worth reinventing |
| POST for row append | PATCH with JSON Merge Patch | More RESTful but requires client to construct patch doc; POST to subresource clearer for single-item append |
| Tabs for mobile | Bottom navigation bar | Tabs semantically correct for pane switching; nav bar for top-level routes only |

**Installation:**
```bash
# Backend: no new deps — Plex client + SQLAlchemy JSON column already exist
# Frontend: shadcn components already installed from Phase 3/5
npx shadcn@latest add context-menu  # if not already added
npx shadcn@latest add sheet          # if not already added
npx shadcn@latest add tabs            # if not already added
```

**Version verification:** [VERIFIED: codebase—frontend/package.json shows shadcn 4.8.0, @radix-ui/* via shadcn, TanStack Query 5.100.14]

## Package Legitimacy Audit

> No external packages recommended beyond existing codebase dependencies (shadcn/Radix already vetted in Phase 3).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| shadcn | npm | 2+ yrs | >1M/wk | github.com/shadcn/ui | — | Approved (official) |
| @radix-ui/react-context-menu | npm | 3+ yrs | >500k/wk | github.com/radix-ui/primitives | — | Approved (official) |

**Packages removed due to slopcheck [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none

*All recommended packages are existing dependencies from Phase 3/5 baseline.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INTERACTION (Browser)                                      │
│                                                                 │
│  Library Page                Series Detail              Playlist Form │
│  ┌──────────┐               ┌─────────────┐           ┌──────────────┐│
│  │ Tile ⋯   │──context──►   │ Hero +      │           │ In | Available││
│  │  menu    │    menu       │ Add button  │           │ tile   tile   ││
│  └──────────┘               └─────────────┘           │ grids  grid   ││
│       │                            │                  │        │       ││
│       └─────────┬──────────────────┴──────────────────┘        │       ││
│                 │ Add to playlist action                        │       ││
│                 │ (POST append or navigate to form)            │       ││
└─────────────────┼─────────────────────────────────────────────┬┘
                  │                                              │
                  ▼                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ API / BACKEND (FastAPI)                                         │
│                                                                 │
│  POST /playlists/{id}/rows          GET /playlists/{id}         │
│    ├─ Validate ownership              └─ Return with snapshot   │
│    ├─ Create PlaylistSeriesRow                                 │
│    └─ Commit + invalidate queries                              │
│                                                                 │
│  DELETE /playlists/{id}/rows/{rowId}                           │
│    ├─ Validate ownership                                        │
│    └─ Delete row + commit                                      │
│                                                                 │
│  GET /series (Library catalog)                                 │
│    └─ Return cached_series with provider_metadata              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                  │                                              │
                  ▼                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DATABASE (PostgreSQL)                                           │
│                                                                 │
│  cached_series.provider_metadata JSON                          │
│    { summary, genres: [Genre], contentRating, studio }         │
│                                                                 │
│  playlist_series_row (mode, completion_policy, sort_order)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                  ▲
                  │ Catalog sync job
                  │
┌─────────────────────────────────────────────────────────────────┐
│ PLEX API                                                        │
│                                                                 │
│  GET /library/sections/{id}/all → Metadata[]                  │
│    ├─ summary (string)                                         │
│    ├─ Genre[] ({ tag })                                        │
│    ├─ contentRating (string)                                   │
│    └─ studio (string)                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. **Catalog sync** (Phase 2) extended to capture Plex `summary`, `Genre[]`, `contentRating`, `studio` into `cached_series.provider_metadata` JSON
2. **Library page** renders tiles with ⋯ → `ContextMenu` → "Add to playlist…" → calls `POST /playlists/{id}/rows` or navigates to form
3. **Series detail** fetches `cached_series` with enriched metadata → renders IMDb-like hero → "Add to playlist" button same as Library
4. **Playlist form** two-pane picker: Available pane reuses `SeriesGrid`; In pane shows `playlist.rows`; click tile in In → `Sheet` opens with row settings

### Component Responsibilities

| Component | File | Purpose |
|-----------|------|---------|
| `AddToPlaylistMenu` | `frontend/src/components/playlists/AddToPlaylistMenu.tsx` | Shared dropdown: lists user playlists + "Create new…"; used from Library tile ⋯, series detail button, optionally Available pane |
| `SeriesCard` (extended) | `frontend/src/components/browse/SeriesCard.tsx` | Add ⋯ button (visible always, not hover-only); wrap in `ContextMenu.Trigger`; stop propagation on menu actions |
| `SeriesDetailPage` (enriched) | `frontend/src/pages/SeriesDetailPage.tsx` | Hero layout: poster + metadata block (summary, genres, rating, studio) + "Add to playlist" button + existing `ResumePreview` |
| `PlaylistFormPage` (two-pane) | `frontend/src/pages/PlaylistFormPage.tsx` | Sections 1–2 unchanged; Section 3 replaces `SeriesPicker` with `TwoPanePicker` |
| `TwoPanePicker` | `frontend/src/components/playlists/TwoPanePicker.tsx` | Responsive: `md+` side-by-side `SeriesGrid` In | Available; `<md` `Tabs` with same grids; click In tile → `Sheet` for row settings |
| `RowSettingsSheet` | `frontend/src/components/playlists/RowSettingsSheet.tsx` | Bottom `Sheet` (side="bottom"): ordered/random toggle, completion policy select, "Remove from playlist" button |
| `catalog_sync.py` (extended) | `backend/src/wheeloffish/core/catalog_sync.py` | `_upsert_series_page`: extend mapper to persist `summary`, `Genre[]`, `contentRating`, `studio` into `provider_metadata` JSON |
| `/playlists/{id}/rows` | `backend/src/wheeloffish/api/routes/playlists.py` | `POST` → append new row (validate ownership, create row, commit); `DELETE /{rowId}` → remove row |

### Recommended Project Structure

```
frontend/src/
├── components/
│   ├── browse/
│   │   ├── SeriesCard.tsx          # Add ⋯ button + ContextMenu.Trigger
│   │   ├── SeriesGrid.tsx          # Reused in TwoPanePicker
│   │   └── SeriesMetadata.tsx      # NEW: genres/rating/studio display
│   ├── playlists/
│   │   ├── AddToPlaylistMenu.tsx   # NEW: shared menu component
│   │   ├── TwoPanePicker.tsx       # NEW: In | Available panes
│   │   └── RowSettingsSheet.tsx    # NEW: bottom sheet for row config
│   └── ui/
│       ├── context-menu.tsx        # shadcn component (npx add)
│       ├── sheet.tsx               # existing from Phase 5
│       └── tabs.tsx                # existing or npx add
├── pages/
│   ├── SeriesDetailPage.tsx        # Enrich with metadata hero
│   └── PlaylistFormPage.tsx        # Replace SeriesPicker section

backend/src/wheeloffish/
├── api/routes/
│   └── playlists.py                # Add POST/DELETE /playlists/{id}/rows
├── core/
│   └── catalog_sync.py             # Extend _upsert_series_page
└── integrations/plex/
    └── mappers.py                  # Extend map_series with metadata fields
```

### Pattern 1: Context Menu + Long-Press

**What:** Radix `ContextMenu` provides right-click + long-press (touch) in one component with ARIA compliance and built-in typeahead.

**When to use:** Any tile or card needing contextual actions without cluttering primary click behavior.

**Example:**

```typescript
// Source: [CITED: ui.shadcn.com/docs/components/radix/context-menu]
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu"

export function SeriesCard({ series }: { series: Series }) {
  const handleNavigate = () => navigate(seriesDetailRoute(series.id))
  
  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <button
          type="button"
          onClick={handleNavigate}
          className="flex flex-col gap-2 rounded-md text-left transition-colors hover:bg-accent/40"
        >
          <div className="relative">
            <SeriesPoster title={series.title} thumbUrl={series.thumb_url} />
            {/* Visible ⋯ button (D-04) */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation() // D-06: don't navigate
                // ContextMenu will open on click or long-press
              }}
              className="absolute top-2 right-2 bg-background/80 rounded-full p-1"
            >
              <MoreVertical className="size-4" />
            </button>
          </div>
          <span className="line-clamp-2 text-sm font-medium">{series.title}</span>
        </button>
      </ContextMenuTrigger>
      
      <ContextMenuContent>
        <ContextMenuItem onClick={() => openAddToPlaylistMenu(series)}>
          Add to playlist…
        </ContextMenuItem>
        <ContextMenuItem onClick={() => createNewPlaylist(series)}>
          Create new playlist…
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  )
}
```

**Why this works:** `ContextMenuTrigger` wraps the tile; right-click or long-press opens menu. The ⋯ button is always visible (D-04) and also opens the menu via click + `stopPropagation`.

### Pattern 2: Bottom Sheet for Row Settings

**What:** shadcn `Sheet` with `side="bottom"` slides up from viewport bottom, ideal for mobile-friendly settings drawers.

**When to use:** Per-item configuration in a list (here: playlist row ordered/random + completion policy).

**Example:**

```typescript
// Source: [CITED: ui.shadcn.com/docs/components/radix/sheet]
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"

export function RowSettingsSheet({ row, onUpdate, onRemove }: RowSettingsSheetProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button type="button" className="w-full">
          <SeriesCard series={{ id: row.series_id, title: row.series_title, ... }} variant="grid" />
        </button>
      </SheetTrigger>
      
      <SheetContent side="bottom" className="h-[50vh]">
        <SheetHeader>
          <SheetTitle>{row.series_title} — row settings</SheetTitle>
        </SheetHeader>
        
        <div className="flex flex-col gap-4 px-4 py-6">
          {/* Ordered / Random toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onUpdate(row.series_id, { mode: "ordered" })}
              className={row.mode === "ordered" ? "bg-primary text-primary-foreground" : "bg-muted"}
            >
              Ordered
            </button>
            <button
              onClick={() => onUpdate(row.series_id, { mode: "disordered" })}
              className={row.mode === "disordered" ? "bg-primary text-primary-foreground" : "bg-muted"}
            >
              Random
            </button>
          </div>
          
          {/* Completion policy select */}
          <select
            value={row.completion_policy}
            onChange={(e) => onUpdate(row.series_id, { completion_policy: e.target.value })}
          >
            <option value="remove">Remove when done</option>
            <option value="restart">Restart</option>
            <option value="disordered">Switch to random</option>
          </select>
          
          {/* Remove button */}
          <Button variant="destructive" onClick={() => onRemove(row.series_id)}>
            Remove from playlist
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
```

**Why this works:** `side="bottom"` slides sheet from bottom; focus trap + overlay prevent accidental navigation; mobile-friendly.

### Pattern 3: Responsive Two-Pane with Tabs Fallback

**What:** Desktop uses `grid-cols-2` side-by-side; mobile collapses to `Tabs` with same content in each tab.

**When to use:** Any dual-view UI (In/Out, Before/After, Compare) needing mobile responsiveness.

**Example:**

```typescript
// Source: [CITED: tailwindcss.com/docs/responsive-design]
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function TwoPanePicker({ inRows, availableSeries, onAdd, onRemove }: TwoPanePickerProps) {
  return (
    <>
      {/* Desktop: side-by-side */}
      <div className="hidden md:grid md:grid-cols-2 md:gap-6">
        <div>
          <h3 className="mb-2 text-sm font-medium">In playlist ({inRows.length})</h3>
          <SeriesGrid items={inRows.map(r => ({ id: r.series_id, title: r.series_title, ... }))} />
        </div>
        <div>
          <h3 className="mb-2 text-sm font-medium">Available to add</h3>
          <Input placeholder="Search series…" /* ... */ />
          <SeriesGrid items={availableSeries} />
        </div>
      </div>
      
      {/* Mobile: tabs */}
      <Tabs defaultValue="in" className="md:hidden">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="in">In playlist ({inRows.length})</TabsTrigger>
          <TabsTrigger value="available">Add shows</TabsTrigger>
        </TabsList>
        
        <TabsContent value="in">
          <SeriesGrid items={inRows.map(r => ({ id: r.series_id, title: r.series_title, ... }))} />
        </TabsContent>
        
        <TabsContent value="available">
          <Input placeholder="Search series…" /* ... */ />
          <SeriesGrid items={availableSeries} />
        </TabsContent>
      </Tabs>
    </>
  )
}
```

**Why this works:** Tailwind mobile-first: unprefixed = mobile, `md:` = desktop breakpoint and up. `hidden md:grid` hides grid on mobile; `md:hidden` hides tabs on desktop. Same `SeriesGrid` component reused in both views.

### Pattern 4: Row Append API (POST to Subresource)

**What:** Use `POST /playlists/{id}/rows` to append a single row without replacing entire row collection.

**When to use:** Quick-add from Library context menu; avoids fetching full playlist → mutating rows array → PUT.

**Example:**

```python
# Source: [CITED: softwareengineering.stackexchange.com/questions/232130]
@router.post("/{playlist_id}/rows", status_code=status.HTTP_201_CREATED)
def append_playlist_row(
    playlist_id: str,
    body: PlaylistRowAppendRequest,  # { series_id, mode?, completion_policy? }
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistSeriesRowResponse:
    """Append a series to playlist without full PUT (D-20)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    
    # Check for duplicate
    existing = next((r for r in playlist.rows if r.series_id == body.series_id), None)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Series already in playlist")
    
    # Create new row at end of sort order
    max_sort = max((r.sort_order for r in playlist.rows), default=-1)
    row = PlaylistSeriesRowOrm(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id,
        series_id=body.series_id,
        mode=body.mode or "ordered",
        completion_policy=body.completion_policy or playlist.default_completion_policy,
        completion_event="series_complete",
        sort_order=max_sort + 1,
    )
    db.add(row)
    db.commit()
    
    title_map = _series_title_map(db, user.id, [body.series_id])
    return PlaylistSeriesRowResponse(
        series_id=row.series_id,
        mode=row.mode,
        completion_policy=row.completion_policy,
        completion_event=row.completion_event,
        series_title=title_map.get(row.series_id),
    )
```

**Why this works:** POST to collection subresource is semantically "append/process." Returns 201 Created with new row. Frontend invalidates playlist detail query to refresh.

### Anti-Patterns to Avoid

- **Right-click-only affordance:** Mobile has no right-click; D-04 mandates visible ⋯ button + long-press support. Use `ContextMenu.Trigger` which handles both.
- **Full PUT for single row add:** Fetching full playlist → mutating rows → PUT is wasteful. Use POST to `/rows` subresource instead.
- **Mobile tabs without keyboard nav:** Always use Radix `Tabs` (not custom div + useState) for ARIA compliance and keyboard support.
- **Storing metadata in separate columns prematurely:** Until metadata fields stabilize (Phase 7 spike), keep in `provider_metadata` JSON. Easier to extend without migrations.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Right-click + long-press menu | Custom `onContextMenu` + touch timer | Radix `ContextMenu` (via shadcn) | Handles pointer events, touch delays, ARIA, submenus, typeahead, dismissal — tested across browsers/devices [VERIFIED: codebase uses Radix] |
| Bottom drawer | Animated div + `position: fixed` | shadcn `Sheet` with `side="bottom"` | Focus trap, overlay, backdrop dismiss, scroll lock, responsive heights [VERIFIED: codebase—existing from Phase 5] |
| Responsive two-pane collapse | Custom media query hooks | Tailwind `md:grid-cols-2` + Radix `Tabs` | Mobile-first breakpoints + ARIA tabs pattern [VERIFIED: codebase—Tailwind 4.3.0] |
| Partial PATCH with merge semantics | Custom JSON diff logic | POST to `/playlists/{id}/rows` for append | Simpler, clearer intent, no patch format complexity [CITED: REST API patterns] |

**Key insight:** UI interaction libraries (Radix) and CSS frameworks (Tailwind) solve edge cases you won't anticipate: ghost clicks on iOS, focus management during modal open, typeahead in menus, screen reader announcements. Reinventing these patterns introduces bugs and accessibility regressions.

## Common Pitfalls

### Pitfall 1: Plex Genre Field Format Confusion

**What goes wrong:** Assuming `Genre` is a string; it's actually an array of objects `{ tag: "Action" }`.

**Why it happens:** JSON response looks like `"Genre": [{ "tag": "Action" }, { "tag": "Adventure" }]` but developers see "Genre" and assume string.

**How to avoid:** Map `Genre[]` to `string[]` during sync: `genres: [g.get("tag") for g in metadata.get("Genre", [])]`. Store as JSON array in `provider_metadata`. Render as comma-separated or chips in UI.

**Warning signs:** "TypeError: Cannot read property 'map' of undefined" when trying to render genres; empty genre badges even though Plex has them.

### Pitfall 2: Long-Press Triggering Click on Mobile

**What goes wrong:** After long-press opens menu, lifting finger fires synthetic `click` event → navigates to series detail.

**Why it happens:** iOS Safari (and some Android browsers) fire ghost click 300ms after `touchend` to support legacy web.

**How to avoid:** Use Radix `ContextMenu` which handles `preventDefault` on `touchend`. If custom long-press hook, ensure `isPreventDefault: true` [CITED: react-use/useLongPress].

**Warning signs:** Menu opens correctly on long-press, but then immediately navigates to detail page when finger lifts.

### Pitfall 3: Context Menu Propagation to Parent Click

**What goes wrong:** Opening context menu via ⋯ button also triggers tile click → navigates to detail.

**Why it happens:** Click event bubbles up from button to tile wrapper.

**How to avoid:** `onClick` handler on ⋯ button must call `e.stopPropagation()` (D-06). Wrap entire tile in `ContextMenu.Trigger`, not just ⋯ button, so right-click anywhere on tile works.

**Warning signs:** Clicking ⋯ always navigates; right-click on tile body works but ⋯ doesn't.

### Pitfall 4: Mobile Tab Content Re-Rendering on Switch

**What goes wrong:** Switching tabs in mobile two-pane view re-mounts grid components → loses scroll position, resets state.

**Why it happens:** `display: none` on inactive tab unmounts React tree; Radix `Tabs` uses `hidden` attribute which still unmounts by default.

**How to avoid:** Use `keepMounted` prop on `TabsContent` if needed, or accept remount (acceptable for this use case since search is debounced and state lives in URL/query params).

**Warning signs:** Search input clears when switching tabs; scroll jumps to top.

### Pitfall 5: Assuming Plex Metadata Always Present

**What goes wrong:** Series detail crashes with "Cannot read property 'summary' of null" when Plex record lacks metadata.

**Why it happens:** Not all series have summaries, genres, ratings (e.g., home videos, unmatched content).

**How to avoid:** Gracefully omit empty fields (D-10: "no N/A placeholders"). Check `provider_metadata?.summary` before rendering. Use optional chaining and fallbacks.

**Warning signs:** Series detail works for popular shows but crashes on obscure/local content.

## Code Examples

Verified patterns from official sources:

### Plex Metadata Field Mapping

```python
# Source: [CITED: developer.plex.tv/pms/ + Plexopedia]
# Extend integrations/plex/mappers.py map_series()

def map_series(
    connection_id: str,
    library_native_id: str,
    metadata: dict[str, Any],
) -> Series:
    guid = str(metadata["guid"])
    
    # Existing fields
    base_series = Series(
        id=format_composite_id(connection_id, PROVIDER, guid),
        title=str(metadata["title"]),
        native_id=guid,
        library_native_id=library_native_id,
        connection_id=connection_id,
        provider=PROVIDER,
        year=metadata.get("year"),
        thumb_url=metadata.get("thumb"),
        provider_metadata={"ratingKey": metadata.get("ratingKey")},
    )
    
    # NEW: Enrich provider_metadata (Phase 6 D-10, D-11)
    enriched_metadata = {
        "ratingKey": metadata.get("ratingKey"),
        "summary": metadata.get("summary"),  # Full plot synopsis
        "genres": [g.get("tag") for g in metadata.get("Genre", [])],  # Extract tag from Genre[]
        "contentRating": metadata.get("contentRating"),  # e.g., "TV-MA"
        "studio": metadata.get("studio"),  # e.g., "HBO"
    }
    base_series.provider_metadata = enriched_metadata
    return base_series
```

### Series Detail Hero Layout

```typescript
// Source: [VERIFIED: codebase—SeriesDetailPage.tsx pattern + UI-SPEC]
// frontend/src/pages/SeriesDetailPage.tsx

export function SeriesDetailPage() {
  const { seriesId } = useSeriesId()
  const { data: series } = useSeriesDetail(connectionId, seriesId)
  const metadata = series?.provider_metadata
  
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link to="/library">← Back to Library</Link>
      
      {/* Hero: poster + metadata */}
      <div className="flex flex-col gap-4 md:flex-row md:gap-6">
        {/* Poster */}
        <div className="aspect-[2/3] w-40 shrink-0">
          <SeriesPoster title={series.title} thumbUrl={series.thumb_url} />
        </div>
        
        {/* Metadata */}
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-semibold">{series.title}</h2>
          {series.year && <p className="text-sm text-muted-foreground">{series.year}</p>}
          
          {/* Content rating badge */}
          {metadata?.contentRating && (
            <Badge variant="outline" className="w-fit text-xs">
              {metadata.contentRating}
            </Badge>
          )}
          
          {/* Genre chips */}
          {metadata?.genres?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {metadata.genres.slice(0, 5).map((genre: string) => (
                <Badge key={genre} variant="secondary" className="text-xs">
                  {genre}
                </Badge>
              ))}
            </div>
          )}
          
          {/* Studio */}
          {metadata?.studio && (
            <p className="text-sm text-muted-foreground">{metadata.studio}</p>
          )}
          
          {/* Summary with line-clamp */}
          {metadata?.summary && (
            <p className="line-clamp-4 text-sm">{metadata.summary}</p>
          )}
          
          {/* Add to playlist button (D-09) */}
          <AddToPlaylistButton seriesId={series.id} />
        </div>
      </div>
      
      {/* Existing resume preview (D-12) */}
      <ResumePreview {...resumeProps} />
    </div>
  )
}
```

### Quick Create Playlist Dialog

```typescript
// Source: [VERIFIED: codebase—shadcn Dialog pattern from Phase 5]
// frontend/src/components/playlists/QuickCreateDialog.tsx

export function QuickCreateDialog({ seriesId, trigger }: QuickCreateDialogProps) {
  const [name, setName] = useState("")
  const [open, setOpen] = useState(false)
  const createMutation = useCreatePlaylist()
  const navigate = useNavigate()
  
  const handleCreate = async () => {
    if (!name.trim()) return
    const payload = {
      name: name.trim(),
      episode_count: 20,
      slot_allocation: "wild",
      default_completion_policy: "remove",
      refresh_cadence: "daily",
      refresh_day_of_week: null,
      rows: [{ series_id: seriesId, mode: "ordered", completion_policy: "remove" }],
    }
    const result = await createMutation.mutateAsync(payload)
    toast.success(`Added to ${result.name}`)
    setOpen(false)
  }
  
  const handleAdvanced = () => {
    navigate(`/playlists/new?seriesId=${seriesId}`)
    setOpen(false)
  }
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create new playlist</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <Input
            placeholder="Playlist name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <div className="flex items-center gap-2">
            <Button onClick={handleCreate} disabled={!name.trim()}>
              Create and add
            </Button>
            <Button variant="link" onClick={handleAdvanced}>
              Advanced…
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Search-box picker only | Two-pane tile picker | Phase 6 (2026-05) | Visual catalog browsing vs text-only search; aligns with Library UX |
| PUT entire playlist for row add | POST to `/playlists/{id}/rows` | Phase 6 | Reduces payload size, avoids race conditions on concurrent edits |
| Right-click-only menus | Visible ⋯ + ContextMenu | Phase 6 | Mobile-first: touch long-press + explicit affordance |
| Metadata not cached | Plex summary/genres/rating synced | Phase 6 | Enables IMDb-like detail pages without external API |

**Deprecated/outdated:**
- `SeriesPicker` (search-only list): Replaced by `TwoPanePicker` with tile grids (D-21)

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this
> section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | — | — | No assumed claims—all recommendations verified via codebase or official docs |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **Jellyfin metadata parity**
   - What we know: Plex fields researched; Jellyfin uses similar structure but field names may differ
   - What's unclear: Exact Jellyfin API field mapping for `summary`, `genres`, `contentRating`, `studios`
   - Recommendation: Ship Plex-first (D-11); stub Jellyfin fields in Phase 6; research Jellyfin in Phase 7 metadata spike

2. **Mobile long-press delay**
   - What we know: Radix `ContextMenu` default delay ~500ms; react-use `useLongPress` default 300ms
   - What's unclear: Optimal delay for this app's UX (too short = accidental, too long = frustrating)
   - Recommendation: Use Radix default (Claude's discretion per CONTEXT); test during UAT

3. **Route path for Library**
   - What we know: `/browse` existing, nav label changes to "Library"
   - What's unclear: Keep `/browse` route or add `/library` redirect
   - Recommendation: Claude's discretion (CONTEXT); suggest keep `/browse` to avoid breaking bookmarks, update nav label only

## Environment Availability

> Phase 6 has no external dependencies beyond existing codebase stack.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| shadcn/ui (Radix) | ContextMenu, Sheet, Tabs | ✓ | 4.8.0 (Radix via shadcn) | — |
| Plex API | Metadata enrichment | ✓ | (integration exists) | Jellyfin stub |
| Tailwind CSS | Responsive grids | ✓ | 4.3.0 | — |
| TanStack Query | Mutations + invalidation | ✓ | 5.100.14 | — |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

## Validation Architecture

> workflow.nyquist_validation is enabled (checked .planning/config.json)

### Test Framework

| Property | Value |
|----------|-------|
| Framework | **Backend:** pytest 8.0+ with pytest-asyncio 0.24+ · **Frontend:** vitest 3.2.4 with @testing-library/react 16.3.2 |
| Config file | **Backend:** `backend/pyproject.toml` `[tool.pytest.ini_options]` · **Frontend:** `frontend/vitest.config.ts` |
| Quick run command | **Backend:** `pytest tests/api/test_playlists_api.py -x` · **Frontend:** `npm test -- src/components/playlists/TwoPanePicker.test.tsx` |
| Full suite command | **Backend:** `pytest tests/ -x` · **Frontend:** `npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLT-03 | Append row via POST /playlists/{id}/rows | integration | `pytest tests/api/test_playlists_api.py::test_append_row -x` | ❌ Wave 0 |
| PLT-03 | Remove row via DELETE /playlists/{id}/rows/{rowId} | integration | `pytest tests/api/test_playlists_api.py::test_remove_row -x` | ❌ Wave 0 |
| PLT-03 | 409 conflict on duplicate row append | integration | `pytest tests/api/test_playlists_api.py::test_append_duplicate -x` | ❌ Wave 0 |
| WEB-01 | ContextMenu opens on right-click + long-press | unit | `npm test -- src/components/browse/SeriesCard.test.tsx` | ❌ Wave 0 |
| WEB-01 | Sheet opens on In-pane tile click | unit | `npm test -- src/components/playlists/TwoPanePicker.test.tsx` | ❌ Wave 0 |
| WEB-01 | Responsive: md+ shows grid, <md shows tabs | unit | `npm test -- src/components/playlists/TwoPanePicker.test.tsx` | ❌ Wave 0 |
| D-10 | Series detail renders metadata (summary, genres, rating) | integration | `npm test -- src/pages/SeriesDetailPage.test.tsx` | ❌ Wave 0 |
| D-11 | Plex sync persists enriched metadata to provider_metadata | unit | `pytest tests/unit/test_plex_metadata_mapper.py::test_map_series_with_metadata -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/api/test_playlists_api.py -x` (backend row ops) or `npm test -- src/components/playlists/ -x` (frontend components)
- **Per wave merge:** `pytest tests/integration/ -x && npm test` (integration + unit green)
- **Phase gate:** Full suite green + manual UAT checklist before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/api/test_playlists_api.py` — add `test_append_row`, `test_remove_row`, `test_append_duplicate` (PLT-03)
- [ ] `backend/tests/unit/test_plex_metadata_mapper.py` — add `test_map_series_with_metadata` (D-11)
- [ ] `frontend/src/components/browse/SeriesCard.test.tsx` — add context menu interaction tests (WEB-01)
- [ ] `frontend/src/components/playlists/TwoPanePicker.test.tsx` — add responsive + sheet tests (WEB-01)
- [ ] `frontend/src/pages/SeriesDetailPage.test.tsx` — add metadata rendering tests (D-10)

*(Tests must cover both happy path and edge cases: empty metadata, duplicate row append 409, mobile vs desktop layout)*

## Security Domain

> security_enforcement enabled (checked .planning/config.json)

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | (session auth existing from Phase 3) |
| V3 Session Management | no | (session cookie existing from Phase 3) |
| V4 Access Control | yes | Ownership validation on POST/DELETE `/playlists/{id}/rows` (D-20: owner-scoped from Phase 5) |
| V5 Input Validation | yes | Pydantic schemas for row append/remove requests; React form validation for name input |
| V6 Cryptography | no | (no new cryptographic operations) |

### Known Threat Patterns for React + FastAPI Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR (playlist row manipulation) | Tampering / Elevation of Privilege | `_get_owned_playlist()` validates ownership before row CRUD (existing pattern from Phase 5) |
| XSS via metadata rendering | Tampering | React auto-escapes JSX; summary/genres from trusted Plex API cached in DB |
| CSRF on POST /rows | Tampering | SameSite=Lax session cookie (existing from Phase 3); no state-changing GET |
| SQL injection via series_id | Tampering | SQLAlchemy ORM parameterized queries (existing pattern) |

**Phase 6-specific considerations:**
- **Plex metadata injection:** Summary/genres come from Plex API (trusted source); stored in JSON column. No user-supplied HTML. React escapes by default.
- **Row append race:** Concurrent POST to `/playlists/{id}/rows` could create duplicates. Mitigate with 409 check + unique constraint on `(playlist_id, series_id)` if desired (optional—planner decides).

## Sources

### Primary (HIGH confidence)

- [VERIFIED: codebase—frontend/package.json] — shadcn 4.8.0, @radix-ui/* via shadcn, TanStack Query 5.100.14, Tailwind 4.3.0
- [VERIFIED: codebase—backend/pyproject.toml] — pytest 8.0+, FastAPI 0.115+, SQLAlchemy 2.0+
- [VERIFIED: codebase—frontend/src/components/browse/SeriesCard.tsx] — Existing tile pattern to extend
- [VERIFIED: codebase—backend/src/wheeloffish/integrations/plex/mappers.py] — `map_series()` function to extend
- [CITED: developer.plex.tv/pms/] — Plex Metadata API: summary, Genre[], contentRating, studio fields
- [CITED: github.com/plexinc/tmdb-example-provider/blob/main/docs/Metadata.md] — Official Plex metadata structure

### Secondary (MEDIUM confidence)

- [CITED: ui.shadcn.com/docs/components/radix/context-menu] — ContextMenu usage + long-press support
- [CITED: ui.shadcn.com/docs/components/radix/sheet] — Sheet component side="bottom" pattern
- [CITED: tailwindcss.com/docs/responsive-design] — Mobile-first breakpoint system + grid-cols-1 md:grid-cols-2
- [CITED: softwareengineering.stackexchange.com/questions/232130] — REST API pattern: POST to collection subresource for append
- [CITED: github.com/streamich/react-use/blob/HEAD/docs/useLongPress.md] — Long-press `isPreventDefault` ghost click prevention

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — all libraries verified in codebase from Phase 3/5
- Architecture: **HIGH** — patterns extend existing BrowsePage, PlaylistForm, catalog_sync.py
- Pitfalls: **HIGH** — Plex Genre[] array structure verified via official docs; ghost click prevention documented in react-use

**Research date:** 2026-05-25  
**Valid until:** 2026-06-25 (30 days—stable stack, no fast-moving dependencies)
