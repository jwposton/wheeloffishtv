# Phase 2 — Manual UAT Checklist

Operator verification against live Plex and Jellyfin servers. Run after automated CI is green (`cd backend && uv run ruff check . && uv run pytest`).

**Prerequisites:** `WOF_SECRET_KEY` set, `WOF_OAUTH_CALLBACK_BASE` reachable from browser, at least one TV library with watch history on each provider.

| # | Scenario | Requirement | Steps | Expected | PASS/FAIL | Date | Operator notes |
|---|----------|-------------|-------|----------|-----------|------|----------------|
| 1 | Plex OAuth E2E | INT-01, D-03 | 1. `POST /api/v1/connections/plex/oauth/start` with `base_url` of your PMS<br>2. Open auth URL, complete PIN at plex.tv<br>3. Poll `GET /api/v1/connections/plex/oauth/status/{pin_id}` until authorized<br>4. `GET /api/v1/connections/{id}/libraries` | Connection created; libraries list includes TV sections only | | | |
| 2 | Jellyfin auth E2E | INT-01, D-03 | 1. `POST /api/v1/connections/jellyfin/auth` with `base_url`, `username`, `password`<br>2. `GET /api/v1/connections/{id}/libraries` | Connection created; libraries list includes `tvshows` folders | | | |
| 3 | Catalog sync | INT-02 | 1. `PUT /api/v1/admin/connections/{id}/library-scope` to scope at least one TV library<br>2. `POST /api/v1/connections/{id}/sync` (202)<br>3. Poll `GET /api/v1/connections/{id}/sync/status` until `idle`<br>4. `GET /api/v1/connections/{id}/series?page=1` | Sync completes; series browse shows cached shows from scoped libraries | | | |
| 4a | Resume — ordered progression | INT-03 | Pick a series watched in order with an unfinished episode. `GET /api/v1/connections/{id}/series/{series_id}/resume`. Compare to Plex On Deck or Jellyfin Next Up. | Resume points to earliest unfinished episode in sequence | | | |
| 4b | Resume — skipped ahead | INT-03 | Pick a series where you watched later episodes before earlier ones. Compare resume to provider on-deck. | Resume honors on-deck / next-up (skipped-ahead episode) | | | |
| 4c | Resume — partial episode | INT-03 | Pick a series with a partially watched episode (mid-watch). Compare resume offset/percent to provider. | Resume returns partial progress on the in-progress episode | | | |
| 5 | Library scope | INT-02 | 1. Note series count in scoped library<br>2. `PUT /api/v1/admin/connections/{id}/library-scope` excluding one library<br>3. Re-sync and browse series | Series from out-of-scope libraries excluded from browse | | | |
| 6 | Provider parity | INT-03 | For the same logical data, call `GET …/series/{series_id}/episodes` on Plex and Jellyfin connections. Compare JSON field names. | Identical response field names (`id`, `title`, `season_number`, `episode_number`, `duration_ms`, `view_offset_ms`, `viewed`, etc.) | | | |

## Sign-off

| Field | Value |
|-------|-------|
| Operator | |
| Environment | |
| Plex server version | |
| Jellyfin server version | |
| All scenarios PASS | ☐ Yes ☐ No |
| Blockers | |

---
*Phase: 02-media-ingestion-catalogs · Plan: 02-07*
