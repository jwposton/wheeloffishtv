# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

