---
phase: 5
slug: orchestration-scheduling
status: draft
shadcn_initialized: true
preset: base-nova
created: 2026-05-25
---

# Phase 5 — UI Design Contract

> Visual and interaction contract for playlist orchestration UI. Derived from Phase 3 design system + Phase 5 CONTEXT decisions D-19–D-26.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn (existing) |
| Preset | base-nova |
| Component library | Radix via shadcn/ui |
| Icon library | lucide-react |
| Font | Geist Variable (`@fontsource-variable/geist`) |

**Reuse Phase 3 tokens** — do not introduce new color palette or typography scale. Extend existing `AppShell`, `Button`, `Badge`, `Card`, `Dialog`, `Select`, `Input`, `Sonner` toast patterns.

---

## Spacing Scale

Inherited from Phase 3 (Tailwind defaults + shadcn):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, inline padding |
| sm | 8px | Compact element spacing |
| md | 16px | Default element spacing |
| lg | 24px | Section padding |
| xl | 32px | Layout gaps |
| 2xl | 48px | Major section breaks |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px (text-sm) | 400 | 1.5 |
| Label | 12px (text-xs) | 500 | 1.4 |
| Heading | 20px (text-xl) | 600 | 1.3 |
| Display | 24px (text-2xl) | 600 | 1.2 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` | Page background |
| Secondary (30%) | `--card` | Playlist cards, output panels |
| Accent (10%) | `--primary` | Primary CTA (Rebuild now, Save) |
| Destructive | `--destructive` | Delete playlist confirmation |

**Status badge colors (semantic, not theme tokens):**

| Status | Badge variant | Meaning |
|--------|---------------|---------|
| Success | `default` + green dot or `outline` with `text-green-600` | Last rebuild succeeded, full output |
| Partial | `secondary` + amber `text-amber-600` | Rebuild completed with row skips / warnings |
| Failed | `destructive` | Rebuild failed; last good snapshot retained |
| Never rebuilt | `outline` + muted | No successful rebuild yet |

Accent reserved for: Rebuild now button, Save playlist, Add series primary actions

---

## Screens & Routes

### `/playlists` — List

- **Layout:** Responsive grid of playlist cards (mirror browse grid density)
- **Card content:** Name, cadence label ("Daily" / "Weekly · Saturday"), status badge, `last_rebuild_at` relative time
- **Actions:** Click card → detail; header "New playlist" button
- **Empty state heading:** "No playlists yet"
- **Empty state body:** "Create a playlist to mix episodes from your favorite shows on a daily or weekly schedule." + CTA "New playlist"

### `/playlists/new` and `/playlists/:id` — Create / Edit

- **Sections (stacked):**
  1. **Basics** — name, episode count N (default 20), slot allocation select (Wild / Balanced / Round-robin), default completion policy
  2. **Schedule** — refresh cadence radio: Daily | Weekly; if Weekly, day-of-week select (Mon–Sun)
  3. **Series rows** — searchable catalog picker (reuse browse search pattern against `cached_series`); each row shows series title/poster thumb, ordered/disordered toggle, per-row completion override select
  4. **Output preview** (detail only) — ordered episode list from last successful snapshot (title, series, slot index)
  5. **Status banner** (detail only) — last rebuild timestamp, error text when failed, row-level warnings when partial

- **Primary CTA:** "Save playlist" (create/edit); "Rebuild now" (detail, owner only)
- **Destructive confirmation:** "Delete playlist": "This removes the playlist and its rebuild history. This cannot be undone."

### Navigation

- Add **Playlists** to `AppShell` nav between Browse and Settings
- Protected route — requires session + media link (same as Browse)

---

## Interaction Patterns

| Pattern | Spec |
|---------|------|
| Rebuild now | Button on detail page; disabled while job `running`; toast on enqueue success |
| Status polling | TanStack Query `refetchInterval: 5000` while status is `running` or `queued` |
| Series picker | Debounced search (300ms), multi-select adds row; duplicate series prevented |
| Form validation | Name required; episode_count ≥ 1; weekly requires DOW; at least one series row to save |
| Loading | Skeleton cards on list; spinner on Rebuild now; output section skeleton while fetching |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA (save) | "Save playlist" |
| Primary CTA (rebuild) | "Rebuild now" |
| Empty state heading | "No playlists yet" |
| Empty state body | "Create a playlist to mix episodes from your favorite shows on a daily or weekly schedule." |
| Error state (failed rebuild) | "Last rebuild failed: {error_message}. Your previous playlist output is still available below." |
| Partial warning | "Last rebuild completed with warnings — some series were skipped." |
| Destructive confirmation | "Delete playlist": "This removes the playlist and its rebuild history. This cannot be undone." |
| Cadence daily | "Daily" |
| Cadence weekly | "Weekly · {DayName}" |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Badge, Button, Card, Dialog, Select, Input, RadioGroup, Skeleton, Sonner | not required |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS (from CONTEXT D-19–D-22)
- [x] Dimension 2 Visuals: PASS (extends Phase 3 shell)
- [x] Dimension 3 Color: PASS (semantic status badges defined)
- [x] Dimension 4 Typography: PASS (inherits Phase 3)
- [x] Dimension 5 Spacing: PASS (inherits Phase 3)
- [x] Dimension 6 Registry Safety: PASS (shadcn only)

**Approval:** approved 2026-05-25 (from discuss-phase CONTEXT)
