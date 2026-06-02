# Wheel of Fish TV

## What This Is

Self-hosted Dockerized **Plex/Jellyfin “random TV roulette”**. Users connect their media server, configure **multiple playlists**, pick shows from a **Library** browse experience, set **episode count per refresh**, and get a rebuilt list daily. **Ordered** shows respect resume/up-next; **disordered** rows feather episodes randomly. **Multipart** arcs stay contiguous within a refresh. Rebuilt output **writes back** to native Plex/Jellyfin playlists for playback in existing clients.

## Core Value

**Pick N random slots across chosen shows — but binge each ordered show from true “resume” — with a slick web UI.**

## Current State (v0.1.0 — shipped 2026-06-02)

- Dockerized FastAPI + React SPA with Plex/Jellyfin OAuth, catalog sync, and nightly rebuild orchestration
- Deterministic playlist mathematics (ordered/disordered, completion policies, multipart adjacency)
- Library-centric membership UX + two-pane playlist editor
- Provider playlist writeback (`{name} [WoF]`) after each rebuild
- Series detail with season-grouped watch state and provider-backed mutations from Library, view-playlist, and edit-playlist flows

## Next Milestone Goals (v0.2.0 — TBD)

- Visual/UX polish pass (WEB-01 completion beyond functional MVP)
- Backlog items BL-03–BL-06: catalog prune, sync diagnostics modal, Plex server-agnostic mode, playlist view toggle
- Remaining human UAT/verification debt from v0.1.0 (see STATE.md Deferred Items)

## Requirements

### Validated (v0.1.0)

- ✓ Dockerized deployment (Compose, CI, migrations) — Phase 1
- ✓ Plex/Jellyfin integration, catalog sync, resume metadata — Phases 2–3
- ✓ Playlist CRUD, membership, tuning, manual rebuild, job status — Phases 4–6
- ✓ Daily scheduled rebuilds with multipart handling — Phase 5
- ✓ Provider playlist writeback (EXP-01) — Phase 7
- ✓ Series detail + watch-state mutations from playlists — Phase 9
- ✓ Per-user library scope (BL-02) and remove confirmation skip (BL-01)

### Active (v0.2.0+)

- [ ] Modern, polished SPA web UI (motion, dark mode, dashboards, visual QA)
- [ ] BL-03: Safe catalog prune for removed server shows
- [ ] BL-04: Detailed sync/rebuild diagnostics modal
- [ ] BL-05: Env-driven Plex server-agnostic vs server-specific mode
- [ ] BL-06: Playlist view toggle (Available vs Output)

### Out of Scope

- First-class in-app video playback (author in WheelOfFish, play in Plex/Jellyfin)
- Licensed content scraping outside configured servers
- Hosted multi-tenant SaaS billing
- Global admin WheelOfFish playlist (cancelled 2026-05-25)

## Context

Shipped v0.1.0 with 9 phases and 51 plans (2026-05-25 → 2026-06-02). Stack: Python/FastAPI, SQLAlchemy/Alembic, APScheduler, React/Vite, TanStack Query, shadcn/ui. Self-hosted Docker Compose deployment.

## Constraints

- **Tech**: Python backend + SPA frontend
- **Deploy**: Docker Compose required
- **UX**: Modern, accessible, dark-mode ready
- **Self-hosted**: Secrets via env/volume mounts, never baked into images

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python backend | Async HTTP + FastAPI ecosystem | ✓ Good |
| Daily batch rebuild | Predictable load vs continuous mutation | ✓ Good |
| No global WheelOfFish playlist | Users manage own playlists | ✓ Decided |
| v0.1.0 before polish | Writeback gates first release | ✓ Shipped v0.1.0 |
| Plex-first writeback | Jellyfin parity in 07-02 | ✓ Both providers |
| Library UX over search-box picker | Phase 6 two-pane editor | ✓ Shipped |
| Specials (S0) after seasons 1…N | Phase 9 series detail | ✓ Shipped |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-02 after v0.1.0 milestone close*
