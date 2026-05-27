# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

