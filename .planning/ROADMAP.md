# Roadmap — Wheel of Fish TV

**Current milestone:** v0.2.0 Operator reliability & backlog  
**Phase numbering:** Continues from v0.1.0 (starts at Phase 10)

---

## Milestones

- ✅ **v0.1.0 feature-complete MVP (provider writeback)** — Phases 1–9 (shipped 2026-06-02)
- 🚧 **v0.2.0 Operator reliability & backlog** — Phases 10–13 (planning)

---

## v0.1.0 (shipped)

<details>
<summary>Phases 1–9 — shipped 2026-06-02</summary>

| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundations & packaging | Complete |
| 2 | Media ingestion & catalogs | Complete |
| 3 | Minimal operator SPA shell | Complete |
| 4 | Playlist mathematics | Complete |
| 5 | Orchestration & scheduling | Complete |
| 6 | Library & playlist assignment | Complete |
| 7 | Provider playlist writeback | Complete |
| 8 | UX polish & release readiness | Complete |
| 9 | Series detail & watch state from playlists | Complete |

Full details: [`.planning/milestones/v0.1.0-ROADMAP.md`](milestones/v0.1.0-ROADMAP.md)

</details>

---

## v0.2.0 phases

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 10 | 3/6 | In Progress|  |
| 11 | Sync & rebuild diagnostics | Operators inspect partial/failed runs without shell or DB access | DIAG-01–05 |
| 12 | Server-agnostic providers | Plex and Jellyfin work with or without a pinned media server URL in env | CONN-01–06 |
| 13 | Playlist view toggle | Edit flow switches Available vs Output on desktop; three tabs on mobile | EDIT-01–05 |

### Phase 10: Safe catalog prune

**Goal:** As an operator, shows removed from Plex/Jellyfin eventually leave Wheel of Fish playlists without transient sync failures causing data loss.

**Success criteria:**

1. Series confidently gone from the provider are marked stale before any auto-removal
2. Auto-prune runs only after the documented N-sync / no-error policy is satisfied
3. Prune events are auditable (reason + timestamp) and visible to operators
4. Existing rebuild warning paths stay non-destructive until prune confidence is met

**Requirements:** PRUNE-01, PRUNE-02, PRUNE-03, PRUNE-04  
**Backlog:** BL-03

**Plans:** 3/6 plans executed
Plans:
**Wave 1**

- [x] 10-01-PLAN.md — DB schema: prune-state columns + playlist_prune_events table (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 10-02-PLAN.md — catalog_prune service: evidence/reset/recovery/auto-prune/audit + unit tests (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 10-03-PLAN.md — FetchResult typing + reachable-gated rebuild evidence + playlist-scoped auto-prune (wave 3)
- [ ] 10-04-PLAN.md — catalog_sync integration: sync-completion evidence + failure resets (wave 3)
- [ ] 10-06-PLAN.md — API embed recent_prune_events + manual_removed audit (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 10-05-PLAN.md — nightly batch sync-before-rebuild ordering (wave 4)

---

### Phase 11: Sync & rebuild diagnostics

**Goal:** As an operator, I can open a modal from warning/error states and see exactly what failed at rebuild, show, and episode granularity.

**Success criteria:**

1. Partial/failed rebuild states expose a “View details” action that opens structured diagnostics
2. Modal lists rebuild errors, per-show fetch warnings, and per-episode writeback issues from API payloads
3. Rows show friendly labels with fallback identifiers and remediation hints
4. Empty state is clear when no detailed diagnostics exist
5. Existing compact badges are unchanged

**Requirements:** DIAG-01, DIAG-02, DIAG-03, DIAG-04, DIAG-05  
**Backlog:** BL-04

---

### Phase 12: Server-agnostic providers

**Goal:** As an operator, I can deploy without a fixed media server URL and let users pick or supply their server at auth time—for both Plex and Jellyfin—while pinned-URL installs keep working.

**Success criteria:**

1. Unset `WOF_MEDIA_SERVER_URL` enables server selection/supply for Plex OAuth
2. Unset URL enables Jellyfin server selection/supply with persisted connection metadata
3. Set URL preserves backward-compatible Plex and Jellyfin behavior
4. Startup validation rejects invalid env combinations with clear errors
5. README and `.env.example` document both modes for each provider

**Requirements:** CONN-01, CONN-02, CONN-03, CONN-04, CONN-05, CONN-06  
**Backlog:** BL-05 (expanded: both providers)

---

### Phase 13: Playlist view toggle

**Goal:** As an operator editing a playlist, I can inspect “Available to add” or “Current output” beside “In playlist” without leaving the edit workflow.

**Success criteria:**

1. Wide layout shows In playlist + one selectable companion panel (Available or Output)
2. Narrow layout exposes three tabs without horizontal overflow
3. Switching views preserves row edits and predictable selection state
4. Add/remove/edit and output list behavior work in both modes
5. Automated tests cover layout modes and primary interactions

**Requirements:** EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05  
**Backlog:** BL-06

---

## Progress (v0.2.0)

| Metric | Value |
|--------|-------|
| Phases | 0/4 |
| Requirements | 0/20 |
| Status | Planning |

---

*Roadmap created: 2026-06-02 — milestone v0.2.0*
