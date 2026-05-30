# Backlog — Wheel of Fish TV

Deferred work not scheduled in the current phase. Pull items into a phase plan when ready.

**Last updated:** 2026-05-28

---

## Open

### BL-03: Safe two-way catalog prune for removed server shows

**Added:** 2026-05-28  
**Target:** Post-release  
**Component:** `backend/src/wheeloffish/core/catalog_sync.py`, `backend/src/wheeloffish/core/orchestrator.py`, `backend/src/wheeloffish/api/routes/playlists.py`, `frontend/src/components/playlists/*`

**User story:** As an operator, I want shows removed from Plex/Jellyfin to stop appearing in Wheel of Fish playlists, without transient provider/network issues silently deleting valid playlist rows.

**Behavior:** Extend login/session catalog sync to identify series that are confidently gone from the provider and mark corresponding playlist rows as stale candidates. Only prune playlist rows after a safety policy is met (for example: successful full sync, repeated absence across N syncs, and no provider auth/connectivity errors during the decision window). Rebuild warnings for stale rows should be actionable and point operators to cleanup status.

**Acceptance criteria:**  
- Series truly removed from provider are eventually removed from WOF playlists without manual intervention.  
- No playlist rows are auto-removed when sync is partial/failed or provider communication is degraded.  
- Prune decisions are auditable (reason + timestamp recorded), and surfaced in UI/logs.  
- Existing rebuild warning path (`fetch_failure` / `empty_snapshot`) remains non-destructive until prune confidence is satisfied.

### BL-04: Detailed sync diagnostics modal for partial/failed runs

**Added:** 2026-05-28  
**Target:** Post-release  
**Component:** `frontend/src/components/playlists/RebuildBanner.tsx`, `frontend/src/components/playlists/WritebackStatus.tsx`, `frontend/src/pages/PlaylistDetailPage.tsx`, `backend/src/wheeloffish/api/routes/playlists.py`, `backend/src/wheeloffish/api/schemas/playlists.py`

**User story:** As an operator, when a rebuild or provider sync is partial/failed, I want a popup/modal that lists exactly what failed (show/episode) and why, so I can fix issues quickly without shell or DB queries.

**Behavior:** Add a "View details" action on warning/error states that opens a modal with structured diagnostics from the latest run (and optionally recent runs): rebuild-level errors, per-show fetch warnings, and per-episode writeback warnings/errors. Include friendly labels, raw identifiers when labels are unavailable, and remediation hints (e.g., removed from server, out-of-scope library, provider auth issue).

**Acceptance criteria:**  
- Partial/failed rebuild states expose a modal with detailed, operator-readable issue breakdown.  
- Modal covers both rebuild fetch issues (show-level) and provider writeback issues (episode-level).  
- Data comes from API payloads (no direct DB access needed by operators).  
- Empty state is clear when no detailed diagnostics are available.  
- Existing compact status badges remain unchanged; modal is additional detail on demand.

### BL-05: Env-driven Plex mode (server-agnostic or server-specific)

**Added:** 2026-05-28  
**Target:** Post-release  
**Component:** `backend/src/wheeloffish/core/config.py`, `backend/src/wheeloffish/core/boot.py`, `backend/src/wheeloffish/api/routes/oauth_plex.py`, `backend/src/wheeloffish/core/connections.py`, `README.md`, `.env.example`

**User story:** As an operator, I want Plex deployments to support either a fixed server URL (current behavior) or a server-agnostic mode (no URL set) where users select an accessible Plex server during auth, while Jellyfin remains explicitly server-specific.

**Behavior:**  
- Plex supports two env-driven modes:  
  - **Server-specific:** `WOF_PROVIDER=plex` with `WOF_MEDIA_SERVER_URL` set; auth must resolve to that server.  
  - **Server-agnostic:** `WOF_PROVIDER=plex` with URL blank/unset; auth flow lists user-accessible Plex servers and captures a selected server for the connection/user link.  
- Jellyfin remains server-specific and requires `WOF_MEDIA_SERVER_URL` to be set and reachable.  
- Startup/validation and operator docs clearly enforce valid combinations and error messages.

**Acceptance criteria:**  
- Plex works in both modes using env config only (no manual DB edits).  
- In Plex server-agnostic mode, user can select from accessible servers at/after OAuth and complete connection successfully.  
- In Plex server-specific mode, behavior remains backward-compatible with current installs.  
- Jellyfin rejects server-agnostic/blank URL config with clear validation error.  
- `.env.example` and `README.md` document both Plex modes and Jellyfin constraint.

### BL-06: Playlist view toggle (Available vs Output) with responsive tabbed layout

**Added:** 2026-05-28  
**Target:** Post-release  
**Component:** `frontend/src/pages/PlaylistDetailPage.tsx`, `frontend/src/components/playlists/TwoPanePicker.tsx`, `frontend/src/components/playlists/PlaylistMembersPanel.tsx`, related tests

**User story:** As an operator, when editing a playlist I want to choose whether the secondary panel shows "Available to add" or "Current output" beside the "In playlist" column, so I can either curate members or inspect generated output without leaving the workflow.

**Behavior:**  
- **Wide screens:** always show "In playlist" plus one selectable companion panel (`Available to add` or `Current output`) controlled by a segmented toggle/switch in the playlist view.  
- **Narrow screens:** collapse into three tabs (`In playlist`, `Available to add`, `Current output`) and allow quick switching between views.  
- Preserve existing row add/remove/edit actions and output-list behavior while adapting layout.

**Acceptance criteria:**  
- Desktop/wide layout supports toggling companion panel between Available and Output next to In Playlist.  
- Mobile/narrow layout presents all three views as tabs and remains usable without horizontal overflow.  
- State/selection behavior is predictable when switching views (no accidental row loss or stale controls).  
- Accessibility is preserved (keyboard tab order, ARIA labels for toggle/tabs).  
- Tests cover both layout modes and key interactions.

---

## Completed (shipped post–v0.1.0 UAT)

### BL-02: Per-user library settings (removed admin RBAC) — 2026-05-26

Delivered: no `WOF_ADMIN_*`; **Settings → Libraries** for any linked user; `PUT /api/v1/connections/{id}/library-scope`; first-sync default all TV libraries in scope. See [CHANGELOG.md](../CHANGELOG.md) and [README.md](../README.md).

### BL-01: "Don't ask again" on remove-from-playlist confirmation — 2026-05-26

Delivered: session-scoped skip in playlist edit/detail; resets on save or navigation. See CHANGELOG.

---

## Template (for future items)

```markdown
### BL-XX: Title

**Added:** YYYY-MM-DD  
**Target:** Phase N or post-release  
**Component:** paths

**User story:** …

**Behavior:** …

**Acceptance criteria:** …
```
