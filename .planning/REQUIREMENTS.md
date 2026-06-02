# Requirements: Wheel of Fish TV

**Defined:** 2026-06-02 (milestone v0.2.0)  
**Core Value:** Pick N random slots across chosen shows — binge each ordered show from true resume — with a slick web UI.

## v0.2.0 Requirements

Backlog BL-03–BL-06. Each maps to one roadmap phase (10–13).

### Catalog prune (BL-03)

- [ ] **PRUNE-01**: Operator sees playlist rows for series that are confidently absent from the provider marked stale (not silently deleted on first failed sync)
- [ ] **PRUNE-02**: System auto-removes stale playlist rows only after a documented safety policy (e.g. successful full sync, repeated absence across N syncs, no auth/connectivity errors in the decision window)
- [ ] **PRUNE-03**: Operator can audit prune decisions (reason + timestamp) via API and operator-facing surfaces
- [ ] **PRUNE-04**: Rebuild warnings for stale or unfetchable rows remain actionable and non-destructive until prune confidence is met

### Sync diagnostics (BL-04)

- [ ] **DIAG-01**: Operator can open a structured diagnostics view from partial/failed rebuild or writeback warning states
- [ ] **DIAG-02**: Diagnostics list rebuild-level errors, per-show fetch warnings, and per-episode writeback warnings/errors from the latest run API payload
- [ ] **DIAG-03**: Each diagnostic row shows a friendly label with raw identifiers when labels are unavailable
- [ ] **DIAG-04**: Diagnostics include remediation hints (removed from server, out-of-scope library, provider auth issue, etc.)
- [ ] **DIAG-05**: Compact status badges on playlist detail remain unchanged; diagnostics are on-demand detail only

### Provider connection modes (BL-05)

- [ ] **CONN-01**: When `WOF_MEDIA_SERVER_URL` is unset, Plex OAuth flow lets the operator select from accessible Plex servers and persists the chosen server on the user connection
- [ ] **CONN-02**: When `WOF_MEDIA_SERVER_URL` is set, Plex behavior remains backward-compatible (auth must resolve to the configured server)
- [ ] **CONN-03**: When `WOF_MEDIA_SERVER_URL` is unset, Jellyfin auth flow lets the operator supply or select a reachable Jellyfin server and persists it on the connection
- [ ] **CONN-04**: When `WOF_MEDIA_SERVER_URL` is set, Jellyfin behavior remains backward-compatible with current server-specific installs
- [ ] **CONN-05**: Startup validation and operator docs describe valid env combinations for both providers (pinned vs server-agnostic)
- [ ] **CONN-06**: `.env.example` and `README.md` document Plex and Jellyfin pinned vs server-agnostic modes

### Playlist editor views (BL-06)

- [ ] **EDIT-01**: On wide screens, operator toggles the companion panel between “Available to add” and “Current output” beside “In playlist”
- [ ] **EDIT-02**: On narrow screens, operator switches among three tabs: In playlist, Available to add, Current output
- [ ] **EDIT-03**: Switching views does not drop unsaved row edits or lose selection state unexpectedly
- [ ] **EDIT-04**: Row add/remove/edit and output-list behavior work in both layout modes
- [ ] **EDIT-05**: Toggle/tabs meet accessibility expectations (keyboard order, ARIA labels)

## Future Requirements

Deferred beyond v0.2.0.

### Operations

- **OPS-01**: Close remaining v0.1.0 human UAT checklists (Phase 05 cron badges, Phase 06 mobile/two-pane) via `/gsd-verify-work` without a dedicated phase

## Out of Scope

| Feature | Reason |
|---------|--------|
| New UX polish milestone | WEB-01 delivered in v0.1.0; operator deemed sufficient for v0.2.0 |
| In-app video playback | Play in Plex/Jellyfin clients |
| Multi-tenant SaaS billing | Self-hosted only |
| Global admin WheelOfFish playlist | Cancelled 2026-05-25 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRUNE-01 | Phase 10 | Pending |
| PRUNE-02 | Phase 10 | Pending |
| PRUNE-03 | Phase 10 | Pending |
| PRUNE-04 | Phase 10 | Pending |
| DIAG-01 | Phase 11 | Pending |
| DIAG-02 | Phase 11 | Pending |
| DIAG-03 | Phase 11 | Pending |
| DIAG-04 | Phase 11 | Pending |
| DIAG-05 | Phase 11 | Pending |
| CONN-01 | Phase 12 | Pending |
| CONN-02 | Phase 12 | Pending |
| CONN-03 | Phase 12 | Pending |
| CONN-04 | Phase 12 | Pending |
| CONN-05 | Phase 12 | Pending |
| CONN-06 | Phase 12 | Pending |
| EDIT-01 | Phase 13 | Pending |
| EDIT-02 | Phase 13 | Pending |
| EDIT-03 | Phase 13 | Pending |
| EDIT-04 | Phase 13 | Pending |
| EDIT-05 | Phase 13 | Pending |

**Coverage:**

- v0.2.0 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-02*  
*Last updated: 2026-06-02 after v0.2.0 roadmap creation*
