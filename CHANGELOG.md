# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Brand / actions:** refreshed wheel icon and playlist action button artwork (rebuild, settings, delete)
- **Series detail routes:** **View series** and origin-aware back navigation from view-playlist (same pattern as edit-playlist)
- **Safe catalog prune:** series removed from Plex/Jellyfin are marked stale and auto-removed from playlists only after the configured N-sync / no-error policy; prune events are audited (reason + timestamp) and rebuild fetch warnings stay non-destructive until confidence is met
- **Playlist detail:** `recent_prune_events` (newest 20) on owner-gated `GET /playlists/{id}`; row delete records a `manual_removed` prune audit in the same transaction
- **Nightly rebuild:** batch job runs catalog sync before rebuild so prune evidence is current
- **Rebuild diagnostics:** partial/failed rebuild or writeback on playlist detail shows **View details**, opening a modal with rebuild errors, per-show fetch warnings, per-episode writeback issues, and prune history; also when `slots_filled` is less than `slots_requested` or the latest run already has structured diagnostic rows
- **Rebuild diagnostics API:** `last_rebuild.diagnostics` on playlist detail (resolved labels, reason text, remediation hints, and actions such as remove row, open series, open provider); `recent_runs` remain summary-only
- **Rebuild underfill:** unfilled slot assignments emit `slot_unfilled` fetch warnings and appear in the diagnostics modal **Shows skipped** section

### Changed

- **Playlist edit:** add, remove, and reorder membership changes are staged locally until the edit form **Save**; **Cancel** discards staged membership without row-level API calls (settings panel still uses **Save Settings** / **Cancel** for config only)
- **Rebuild panel:** failed rebuild `error_message` and per-episode writeback bullet lists moved into the diagnostics modal; detail **WritebackStatus** keeps badges and one-liners only (compact card badges unchanged)
- **Rebuild status:** runs mark **Partial** when any fetch warnings exist or filled slots are fewer than requested (not only when a show row is skipped)
- **Diagnostics actions:** **Open show** from the modal uses in-app navigation on playlist detail (no full page reload)

### Fixed

- **Rebuild diagnostics:** failed rebuilds without `error_message` still show the catalog rebuild-failed row in the modal
- **Rebuild diagnostics:** writeback-only failures surface a provider sync row when there are no per-episode writeback warnings
- **Rebuild diagnostics:** unknown show fetch warning codes resolve to `fetch_failure` catalog copy instead of a generic writeback warning

- **Series detail:** episodes load for watch-state controls whenever auth is ready (not only when an on-deck resume pointer exists)
- **Series detail:** optimistic episode watch cache rolls back when the mutation envelope is not `succeeded`
- **Series detail:** reject protocol-relative `from` back URLs (`//…`)
- **Series detail:** show per-scope provider-error caveat on failed season/series bulk mutations; progress banner timers no longer clear a newer in-flight mutation
- **Playlist edit:** scroll position preserved when session-added rows reorder to the top of the in-playlist pane
- **Watch-state API:** guardrail coverage for unauthenticated requests (401), provider auth failures, and cross-connection targets

## [1.0.0] - 2026-05-28

Stable release: catalog watch-state mutations, series detail controls, and playlist edit parity shipped since `v0.1.8`.

### Added

- **Watch-state API:** `POST /api/v1/catalog/watch-state` for episode, season, and series targets (watched / unwatched) with normalized response envelopes, bulk partial-failure reporting, and auth guards on connection ownership
- **Provider adapters:** Plex and Jellyfin implementations behind a shared typed mutation contract
- **Series detail:** grouped season watch/unwatch affordances with post-mutation reconciliation
- **Global progress:** watch-state mutation banner persists across route changes until the request finishes
- **Playlist edit:** **View series** from in-playlist row menus; origin-aware back navigation to playlist edit
- **Playlist edit:** session-added shows pinned to the top of the in-playlist pane with a transient **New** badge (no scroll jump on add)
- **Playlist settings:** **Save Settings** / **Cancel** apply only to settings (name, episode count, slot allocation, completion policy, refresh); add/remove shows still save immediately
- **Playlist settings:** contextual field help; refresh hint uses install `WOF_REBUILD_CRON` and `WOF_INSTALL_TIMEZONE` via `install_schedule` on `GET /api/v1/auth/me`; slot allocation **?** popup explains Wild / Balanced / Round-robin

### Fixed

- **Up Next / resume:** Season 0 specials are ordered after normal seasons when choosing the next unwatched episode (was treated like a regular season)
- **Playlist edit:** scroll position no longer jumps to top when adding a show during the same session

## [0.1.8] - 2026-05-27

### Fixed

- **Jellyfin:** library sort by date added (newest/oldest) now works — catalog sync requests `Fields=DateCreated` on series list (Jellyfin omits it by default, so `library_added_at` was always null). Re-run a catalog sync after upgrade to backfill existing shows.

## [0.1.7] - 2026-05-27

### Added

- Playlist rebuild logs **`playlist_slot_empty`** at INFO when a slot assignment yields no episode: **`ordered_exhausted`** (ordered cursor at end of the series queue) or **`disordered_fully_emitted`** (every episode in that series was already placed earlier in the same rebuild). Fields include `playlist_id`, `slot_index`, `series_id`, `row_mode`, and counts for debugging.

### Changed

- **Jellyfin parity with Plex:** series posters use the same cached `/series/.../artwork` flow as Plex (including post-sync prefetch). Sync stores Jellyfin primary image as `/Items/{id}/Images/Primary?tag=…` and maps **Overview**, **Genres**, **OfficialRating**, and **Studios** into the same `provider_metadata` fields as Plex. Jellyfin API client uses the same 60s request timeout as Plex. Catalog sync `401` errors now show a Jellyfin-specific message when `WOF_PROVIDER` is Jellyfin.

## [0.1.6] - 2026-05-27

### Fixed

- **PostgreSQL / Docker:** migration `010` could not finish because Alembic’s `alembic_version.version_num` column is `varchar(32)` on Postgres, while the 0.1.5 revision id was longer. Renamed the revision to `010_lib_added_at` so `alembic upgrade head` completes and Postgres compose smoke passes. No change to the applied schema (still adds `cached_series.library_added_at`).

## [0.1.5] - 2026-05-27

### Added

- Sort library and “available shows” lists by **date added** (newest or oldest first), or keep **title (A–Z)**; series API supports `sort=title|added_at` and `order=asc|desc`
- Plex sync stores library add time from `addedAt`; Jellyfin from `DateCreated`

### Migration

- Alembic `010_lib_added_at`: adds nullable `library_added_at` (Unix seconds) on `cached_series`. Run `alembic upgrade head`, then trigger a catalog sync to backfill existing rows.

## [0.1.4] - 2026-05-27

### Added

- CI security workflow: Gitleaks, Semgrep, pip-audit, npm audit, Trivy image scan, and API auth guard regression tests ([SECURITY.md](SECURITY.md))
- **Don’t ask again** on remove-from-playlist confirmation (session-scoped; resets on save or leaving the edit/detail page)

### Changed

- **Per-user library scope:** any signed-in user with a media link can manage **Settings → Libraries**; first sync defaults all TV libraries in scope
- `GET /api/v1/connections/{id}/libraries` returns all libraries with `in_scope` flags; series browse still filters to in-scope only
- Compact header bar (~33% shorter): smaller logo, tighter padding, `xs` action buttons
- Version badge stacked below theme toggle and log out in the header (login page matches)

### Removed

- Admin RBAC: `WOF_ADMIN_PROVIDER_USER_ID`, `WOF_ADMIN_USERNAME`, setup mode, `/setup/admin`, `/api/v1/admin/*`, and `is_admin` / `setup_mode` on `/auth/me`
- Non-admin “wait for admin” holding page (replaced by redirect to **Settings → Libraries** when scope is unset)

### Migration

- Remove unused `WOF_ADMIN_*` entries from `.env` after upgrade
- Replace API calls to `PUT /api/v1/admin/connections/{id}/library-scope` with `PUT /api/v1/connections/{id}/library-scope`

## [0.1.3] - 2026-05-26

### Added

- Header version badge (`v0.1.x`) with GitHub release check and upgrade hint when a newer tag is available

## [0.1.2] - 2026-05-26

### Fixed

- Brand logos blocked by ad/privacy extensions on `/brand/*` URLs — logos now bundled under Vite `/assets/` paths
- Docker entrypoint on slim images (`su` instead of missing `runuser`)
- PostgreSQL migration boolean column defaults in migration 002

## [0.1.1] - 2026-05-26

### Added

- WOF visual theme (dark default, palette, Bungee + Roboto typography)
- Production brand assets: hero logo, header logo, wheel favicon
- SVG `WheelIcon` for rebuild/status spinners
- Vertical rebuild button (wheel + label)
- Home page with hero lockup and quick links
- Mobile nav row (Library / Playlists / Settings)
- LinuxServer-style `PUID` / `PGID` entrypoint for `/data` ownership
- Admin-only Settings route and nav link

### Changed

- Header logo sizing and tight crop of transparent padding
- Playlist detail layout (shows column width, show tile grid)
- Docker entrypoint remaps app user to `PUID`/`PGID` on start (no Compose `user:`)
- Default theme set to dark

### Fixed

- SQLite readonly errors on Docker volumes (permission remapping + `/data` chown)
- TypeScript build: `RebuildRunSummary.status` typed for rebuild helpers
- Mobile nav hiding Library / Playlists on narrow screens

### Removed

- UHF background easter egg silhouettes

## [0.1.0] - 2026-05-25

First feature-complete self-host release.

### Added

- Plex and Jellyfin OAuth / connection flows
- Library browse, series detail, resume preview
- Playlist authoring (ordered / disordered rows, rebuild orchestration)
- Provider playlist writeback — rebuilds push native `{name} [WoF]` playlists
- Writeback status UI and Plex deep links
- Multi-arch Docker images on GHCR (`linux/amd64`, `linux/arm64`)
- `compose.release.yml` for pull-only deployment

### Fixed

