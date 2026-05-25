# Phase 6: Library & playlist assignment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 06-library-playlist-assignment
**Areas discussed:** Scope repurpose, Library assignment, Series detail, Quick-create flow, Row settings UX, Responsive two-pane, Roadmap cleanup

---

## Prior conversation (pre-discuss)

| Topic | User's choice |
|-------|---------------|
| Admin WheelOfFish | Scrapped |
| Nav label | Browse → Library |
| Add affordance | Visible ⋯ + right-click + long-press (same menu) |
| Filters v1 | Name search only |
| Playlist edit | Two-pane: In playlist \| Available to add |

---

## 1. Series detail — add to playlist + metadata

| Option | Description | Selected |
|--------|-------------|----------|
| A | Same menu on detail page | ✓ |
| B | Library only for v1 | |
| C | Primary “Add to playlist” button on detail | ✓ |
| + | IMDb-like metadata on detail (provider-sourced) | ✓ (with bounded scope) |

**User's choice:** 1A + 1C; also enrich detail with IMDb-*like* metadata if not excessive complexity.

**Notes:** Captured as D-09–D-12. No external IMDb API — extend Plex/Jellyfin sync for summary, genres, content rating, studio. Cast/crew deferred. Resume preview retained.

---

## 2. Create new playlist from quick-add

| Option | Description | Selected |
|--------|-------------|----------|
| A | Inline name prompt only | |
| B | Navigate to full form | |
| C | Inline prompt + “Advanced…” link to full form | ✓ |

**User's choice:** 2C

---

## 3. Row settings in In playlist pane

| Option | Description | Selected |
|--------|-------------|----------|
| A | Click tile → bottom sheet / drawer | ✓ |
| B | Hover actions on tile | |
| C | Select tile → side panel | |

**User's choice:** 3A

---

## 4. Two-pane mobile layout

| Option | Description | Selected |
|--------|-------------|----------|
| A | Tabs: In playlist \| Add shows | ✓ |
| B | Stacked vertical panes | |
| C | Single pane + toggle | |

**User's choice:** 4A

---

## 5. ROADMAP & requirements cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| A | Cancel ADM-01/02; rename Phase 6; update PROJECT.md | ✓ |
| B | Cancel ADM only | |
| C | Defer doc updates | |

**User's choice:** 5A

---

## Claude's Discretion

Route path `/browse` vs `/library`; exact metadata storage shape; Jellyfin parity depth; shared vs per-pane search behavior.

## Deferred Ideas

- Genre/animated filter chips (post metadata spike)
- Cast/crew on detail page
- Global WheelOfFish playlist (cancelled)
