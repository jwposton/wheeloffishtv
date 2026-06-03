---
phase: 11
slug: sync-rebuild-diagnostics
status: draft
shadcn_initialized: true
preset: existing-wof
created: 2026-06-02
---

# Phase 11 — UI Design Contract

> Diagnostics modal on playlist detail. Derived from `11-CONTEXT.md` locked decisions.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | shadcn-style (existing) |
| Preset | `wof-panel`, existing playlist detail tokens |
| Component library | Base UI (`@base-ui/react/dialog`) via `frontend/src/components/ui/dialog.tsx` |
| Icon library | lucide-react |
| Font | Existing app stack |

---

## Components

| Component | Role |
|-----------|------|
| `Dialog` (`ui/dialog.tsx`) | Diagnostics modal shell (scrollable content, not AlertDialog) |
| `Button variant="link"` | Single "View details" trigger at bottom of `RebuildBanner` |
| `StatusBadge` | Modal header status — unchanged semantics |
| `RemoveFromPlaylistDialog` | Pattern for `remove_row` confirm-before-delete |

---

## Layout — RebuildBanner (unchanged badges)

- Keep two sections: Last rebuild + Provider sync.
- **Remove** inline error paragraph for failed rebuild (D-07) and inline writeback warning lists on detail (D-05, D-06).
- One **View details** link at **panel bottom** when rebuild partial/failed OR writeback partial/failed (D-01–D-04).
- List cards: `WritebackStatus compact` only — no trigger (D-08).

---

## Layout — Diagnostics modal

| Zone | Content |
|------|---------|
| Header | Title "Rebuild diagnostics" + `StatusBadge` + relative finished time (D-14) |
| Body | Single scrollable column; `max-w-lg` or `max-w-xl`, `max-h-[70vh]` overflow-y |
| Sections (order) | Rebuild → Shows skipped → Episode sync → Prune history (D-09, D-10) |
| Row | Primary label; `reason_text` on same block; `remediation_hint` muted line below (D-11) |
| ID fallback | Subdued monospace `series_id` / `episode_id` when label missing (D-20) |
| Actions | Inline link/buttons from `actions[]` API metadata (D-19) |
| Empty | "No detailed diagnostics available for this run" + timestamp (D-12) |

Hide empty sections entirely (D-10). Prune section uses `recent_prune_events` from playlist detail (D-15).

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Trigger | View details |
| Modal title | Rebuild diagnostics |
| Empty state heading | No detailed diagnostics available for this run |
| Empty state body | Finished {relative time} — nothing else was recorded for this run. |
| Section: Rebuild | Rebuild |
| Section: Shows | Shows skipped |
| Section: Episodes | Episode sync |
| Section: Prune | Prune history |
| Unknown label | Unknown show / Unknown episode |

Banner summaries stay as today (partial/failed one-liners only).

---

## Interaction

- Open: click View details; close via dialog close control / overlay (standard Dialog).
- `remove_row`: open existing remove confirm dialog; refresh detail on success.
- `open_provider` / `open_series`: navigate or `window.open` per action params from API.
- No run picker; latest `last_rebuild` only (D-13, D-16).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Dialog, Button, Badge | not required |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
