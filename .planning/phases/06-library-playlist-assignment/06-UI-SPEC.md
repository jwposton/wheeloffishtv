---
phase: 6
slug: library-playlist-assignment
status: draft
shadcn_initialized: true
preset: base-nova
created: 2026-05-25
---

# Phase 6 — UI Design Contract

> Visual and interaction contract for Library-centric playlist assignment. Extends Phase 3/5 design system per CONTEXT D-03–D-21.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn (existing) |
| Preset | base-nova |
| Component library | Radix via shadcn/ui |
| Icon library | lucide-react |
| Font | Geist Variable (`@fontsource-variable/geist`) |

**Reuse Phase 3/5 tokens** — extend `AppShell`, `Button`, `Badge`, `Card`, `Dialog`, `DropdownMenu`, `Sheet`, `Tabs`, `Input`, `Sonner`. No new palette or typography scale.

---

## Spacing Scale

Inherited from Phase 3 (Tailwind defaults + shadcn):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, ⋯ button padding |
| sm | 8px | Tile action gaps |
| md | 16px | Grid gutter, pane padding |
| lg | 24px | Section padding |
| xl | 32px | Two-pane column gap (md+) |
| 2xl | 48px | Detail hero spacing |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px (text-sm) | 400 | 1.5 |
| Label | 12px (text-xs) | 500 | 1.4 |
| Heading | 20px (text-xl) | 600 | 1.3 |
| Display | 24px (text-2xl) | 600 | 1.2 |
| Metadata label | 12px (text-xs) | 500 uppercase tracking-wide | 1.4 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` | Page background |
| Secondary (30%) | `--card` | Tile cards, pane surfaces |
| Accent (10%) | `--primary` | "Add to playlist" primary button, add tile action |
| Destructive | `--destructive` | Remove from playlist confirmation |
| Muted | `--muted-foreground` | Metadata labels, empty pane hints |

**Content rating badge:** `outline` variant with `text-xs`; genre chips use `secondary` variant.

Accent reserved for: primary "Add to playlist" on detail, quick-create confirm, add tile in Available pane

---

## Screens & Routes

### Nav rename — Browse → Library

- **AppShell nav label:** "Library" (path stays `/browse` or gains `/library` redirect — planner discretion)
- **Page heading:** "Library"
- **Back link on detail:** "Back to Library"

### `/browse` (Library) — Catalog + assignment hub

- **Layout:** Existing infinite-scroll poster grid (reuse `SeriesGrid` density)
- **Toolbar:** Name search only (debounced 300ms); no filter chips in v1
- **Tile affordances:**
  - Whole tile click → series detail (unchanged)
  - **Visible ⋯ button** top-right on each tile (always visible, not hover-only)
  - **Right-click** and **long-press (touch)** open same menu as ⋯
  - Menu actions stop propagation — do not navigate
- **Context menu items:**
  - "Add to playlist…" → submenu or dialog listing user playlists
  - "Create new playlist…" → inline name prompt (see Quick Create)
- **Empty state heading:** "Your library is empty"
- **Empty state body:** "Sync your media server to browse shows and add them to playlists." + sync CTA if applicable

### `/series` — Series detail (enriched)

- **Hero layout (md+):** Poster left, metadata right; stacked on mobile
- **Metadata block (from cached provider fields):**
  - Title (display), year
  - Content rating badge (when available)
  - Genre chips (when available)
  - Studio/network line (when available)
  - Summary/blurb (2–4 lines, `line-clamp` optional with expand)
- **Primary CTA:** "Add to playlist" button (opens shared menu/dialog)
- **Secondary:** Same menu as Library ⋯ (dropdown from button or split button — planner discretion)
- **Below hero:** existing `ResumePreview` block unchanged
- **Missing metadata:** Omit empty fields gracefully — no "N/A" placeholders

### Quick create playlist (from Library or detail)

- **Trigger:** "Create new playlist…" from context menu
- **UI:** Small dialog with:
  - Name input (required, autofocus)
  - Primary: "Create and add"
  - Text link: **"Advanced…"** → navigates to `/playlists/new?seriesId={id}` (or equivalent state)
- **Success:** Toast "Added to {playlist name}"; invalidate playlist queries

### `/playlists/new` and `/playlists/:id/edit` — Two-pane picker

- **Sections (stacked, unchanged from Phase 5):**
  1. **Basics** — name, episode count, slot allocation, default completion policy
  2. **Schedule** — daily/weekly cadence
  3. **Shows** — **two-pane tile picker** (replaces search-box `SeriesPicker`)

- **Two-pane layout (md+):**
  - Left: **In playlist (N)** — tile grid of member series
  - Right: **Available to add** — tile grid from catalog (infinite scroll or paginated — match Library)
  - Shared search bar above Available pane filters catalog by name
  - In pane: optional search narrows members by name

- **Two-pane layout (<md):**
  - `Tabs`: **In playlist (N)** | **Add shows**
  - Same tile grids inside each tab

- **In playlist pane interactions:**
  - Click tile → **bottom Sheet** with row settings:
    - Ordered / Random toggle
    - Completion policy override select
    - Remove from playlist (destructive, with confirm if needed)
  - Tile shows small badge for Random mode when not ordered

- **Available pane interactions:**
  - Click tile → add to In playlist (toast feedback)
  - Already-in-playlist series: dimmed or hidden (planner picks simplest)
  - Reuse `SeriesCard` poster tile styling

- **Pre-selection:** When arriving from "Advanced…", series appears in In pane on load

### Shared `AddToPlaylistMenu` component

Used from: Library tile ⋯, series detail button, optionally Available pane quick-add.

| State | Behavior |
|-------|----------|
| Loading playlists | Skeleton or disabled menu |
| No playlists | Show "Create new playlist…" only |
| Has playlists | List playlists + "Create new playlist…" separator |

---

## Interaction Patterns

| Pattern | Spec |
|---------|------|
| ⋯ visibility | Always visible on grid tiles; `absolute top-2 right-2` on card |
| Event propagation | All menu/button handlers call `stopPropagation` + `preventDefault` where needed |
| Long-press | ~500ms delay on touch; same menu as ⋯ |
| Right-click | `contextmenu` handler on tile wrapper |
| Append API | Quick-add uses row append endpoint; toast + query invalidation |
| Row settings | Sheet slides from bottom; focus trap; close on save or backdrop |
| Search debounce | 300ms (match Library) |
| Loading | Skeleton tiles in panes; spinner on quick-create submit |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Nav label | "Library" |
| Page heading | "Library" |
| Primary CTA (detail) | "Add to playlist" |
| Context menu — existing | "Add to playlist…" |
| Context menu — create | "Create new playlist…" |
| Quick create primary | "Create and add" |
| Quick create advanced link | "Advanced…" |
| Two-pane — in column | "In playlist" |
| Two-pane — available column | "Available to add" |
| Mobile tab — in | "In playlist ({N})" |
| Mobile tab — add | "Add shows" |
| Empty in pane | "No shows yet — pick from Available to add." |
| Empty available pane | "No matching shows in your library." |
| Add success toast | "Added to {playlist_name}" |
| Remove confirm | "Remove from playlist": "Remove {series_title} from this playlist?" |
| Back link | "Back to Library" |
| Sheet title | "{series_title} — row settings" |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Badge, Button, Card, Dialog, DropdownMenu, Sheet, Tabs, Input, ContextMenu, Sonner | not required |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS (from CONTEXT D-03–D-21)
- [x] Dimension 2 Visuals: PASS (extends Phase 3/5; two-pane + hero defined)
- [x] Dimension 3 Color: PASS (inherits tokens; genre/rating badges defined)
- [x] Dimension 4 Typography: PASS (inherits Phase 3)
- [x] Dimension 5 Spacing: PASS (inherits Phase 3)
- [x] Dimension 6 Registry Safety: PASS (shadcn only)

**Approval:** approved 2026-05-25 (derived from discuss-phase CONTEXT)
