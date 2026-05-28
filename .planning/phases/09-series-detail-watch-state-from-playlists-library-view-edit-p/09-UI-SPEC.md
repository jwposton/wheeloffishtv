---
phase: 9
slug: series-detail-watch-state-from-playlists-library-view-edit-p
status: draft
shadcn_initialized: true
preset: base-nova
created: 2026-05-28
---

# Phase 9 — UI Design Contract

> UI contract for playlist/library parity on series detail and watch-state actions. Derived from `9-CONTEXT.md` and Phase 9 roadmap goals.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn (existing) |
| Preset | base-nova |
| Component library | Radix via shadcn/ui |
| Icon library | lucide-react |
| Font | Geist Variable (`@fontsource-variable/geist`) |

Reuse existing app tokens and components from Phases 3/6/8. Do not introduce a new color palette or typography scale.

---

## Screens and Route Parity

### Series detail route

- Use one shared series detail route/pattern across:
  - Library flow
  - View-playlist flow
  - Edit-playlist flow (`View series` from in-playlist context menu)
- Navigation should preserve origin context with clear back affordance:
  - "Back to Library" when opened from Library
  - "Back to Playlist" when opened from playlist pages

### Edit playlist two-pane behavior

- In-playlist tile context menu includes **View series**
- Available-pane tile click continues to append membership
- Series added in current edit session are surfaced at top of In-playlist pane with a transient "New" affordance

---

## Episode List Contract

- Episodes grouped by season
- Default season order:
  - Seasons `1..N` ascending first
  - Specials (`S0`) rendered last
- Episode state badges:
  - `Watched`
  - `On deck`
  - `Unwatched`

Bulk scope controls in detail UI:
- Episode-level action
- Season-level action
- Series-level action

Provider support caveat text should appear when a requested bulk scope is not available in the active provider context.

---

## Interaction Patterns

| Pattern | Spec |
|---------|------|
| View series from playlist edit | Context menu item navigates to shared detail route with origin metadata |
| Episode action menu | `Mark watched` / `Mark unwatched` on episode row |
| Season action menu | Bulk watch/unwatch for visible season |
| Series action menu | Bulk watch/unwatch for entire series |
| Optimistic updates | Allowed per action with rollback toast on provider/API failure |
| Refetch/reconcile | Invalidate detail + playlist queries after mutation; reconcile badges with provider response |
| Loading | Skeleton rows for episodes; disable action menus while mutation in flight |

---

## Copy Contract

| Element | Copy |
|---------|------|
| In-playlist context menu item | "View series" |
| Episode action | "Mark watched" / "Mark unwatched" |
| Season action | "Mark season watched" / "Mark season unwatched" |
| Series action | "Mark series watched" / "Mark series unwatched" |
| Session-new marker | "New" |
| Provider failure toast | "Could not update watch status. Please try again." |
| Unsupported scope note | "This provider does not support this bulk update scope." |

---

## Accessibility and QA Baseline

- Keyboard accessible menus for episode/season/series actions
- Visible focus rings on all interactive tile and action controls
- Action labels include scope ("episode", "season", "series") for screen reader clarity
- No color-only status signaling; include text labels for watched state

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS (extends existing detail and pane patterns)
- [x] Dimension 3 Color: PASS (reuse existing semantic badges/tokens)
- [x] Dimension 4 Typography: PASS (inherits existing scale)
- [x] Dimension 5 Spacing: PASS (inherits existing layout rhythm)
- [x] Dimension 6 Registry Safety: PASS (shadcn-only primitives)

**Approval:** ready for `/gsd-plan-phase 9`
