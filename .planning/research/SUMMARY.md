# Research Summary — Media playlist builder (Plex / Jellyfin)

**Date:** 2026-05-24  
**Scope:** Greenfield self-hosted service

## Stack (directional)

| Layer | Recommendation | Notes |
|-------|----------------|-------|
| API | **FastAPI** + **Pydantic v2** | Async httpx to Plex/Jellyfin; OpenAPI for SPA |
| Job runner | **APScheduler** (in-proc) or **Celery/RQ** + Redis if scale needed | Daily rebuild is single cron-style trigger |
| DB | **PostgreSQL** (docker) or **SQLite** for single-user beta | Playlists + user ↔ server creds + watch-state cache |
| Frontend | **Vite + React** + component lib (**Radix**/shadcn) + **TanStack Query** | “Slick” without bespoke design churn |
| Auth | Session cookies + HTTPS reverse proxy (**Caddy**/Traefik); local login first | SSO later |

### Pitfall: differing “resume point” semantics

Normalize both vendors to internal `ResumeCursor { series_id, season_index?, episode_index, part_index?, percent_watched }`. Poll during refresh OR subscribe to webhooks where available later.

### Pitfall: multipart / multi-episode arcs

Define rule in **Phase algorithm design**: Plex `guid` linkage, Jellyfin parent `IndexNumber`/`Part`, or heuristic `SXXEYY` + specials folder. Requirement: deterministic ordering within the multipart block adjacent in output list.

## Features — table stakes vs differentiators

**Table stakes**

- Secure credential storage per user/server
- Show library enumeration + picker
- CRUD playlists; N-length daily output
- Admin flag for WheelOfFish

**Differentiators**

- Fine-grained **ordered vs disordered** per playlist row
- **Season-complete** policy UX (remove / restart / loosen order)
- Contiguous multipart injection

## Architecture sketch

Browser → HTTPS → Reverse proxy → **backend** (+ static SPA) ↔ **PostgreSQL**. Background job loads watch state → builds playlists → pushes “playlist payloads” readable by Plex/Jellyfin (**playlist/update API**) where supported OR exports M3U/JSON for third-party tooling (fallback risk — confirm in PLAN phase).

## Pitfalls checklist

| Pitfall | Prevention | Phase |
|---------|-------------|-------|
| API rate limiting | Debounce scans; incremental delta | Backend |
| Stale resume after external watch | Nightly reconcile + manual “resync now” optional | Playlist |
| Two-user same Plex home | Separate logical users share server config but distinct cursors keyed by **media username** binding | Multi-user |

---

*Synthetic research (single pass) — run `/gsd-discuss-phase` to deepen any dimension.*
