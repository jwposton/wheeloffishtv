# Wheel of Fish TV

## What This Is

Self-hosted Dockerized **plex/jellyfin “random TV roulette”**. Users connect their **Plex** or **Jellyfin** library, configure **multiple playlists**, pick which shows feed each playlist, set **episode count per refresh**, and get a rebuilt list daily. For **ordered** shows, playback respects **(series order)** starting from **up-next / earliest unwatched / in-progress**. For **disordered** show entries, episodes from that show are **feathered in randomly**. Admins maintain a fixed **server-wide** **WheelOfFish** playlist (**all disordered**). **Multipart** arcs keep **continuation parts contiguous** within a refresh.

## Core Value

**Pick N random slots across chosen shows — but binge each ordered show from true “resume” — with a slick web UI.**

## Requirements

### Validated

- ✓ Dockerized deployment (Python FastAPI service, Compose stack, CI) — Phase 1

### Active

- [ ] Connect user-configured Plex and/or Jellyfin; list libraries & shows user can attach to playlists
- [ ] Multiple playlists per user + admin **WheelOfFish** playlist
- [ ] Ordered vs disordered per **playlist × show**
- [ ] Policies when a show’s season (or library rules) completes: remove on next refresh vs restart vs switch to disordered
- [ ] Daily full rebuild scheduler; multipart episodes grouped back-to-back (ordered flows)
- [ ] Modern, polished SPA web UI for all configuration

### Out of Scope

- Replacing Plex/Jellyfin as the playback client (this system **authors playlists** consumed in those apps, not a bespoke video player) — narrow if you intend first-class in-app playback
- Offline downloads / DRM circumvention — legal Plex/Jellyfin API usage only
- Multi-region cloud SaaS tenancy — assumes self-hosted deployment

## Context

Inspired by communal “shuffle TV” (**Wheel Of Fish**) where variety matters but serialization matters for dramas. Plex “On Deck” / Jellyfin “Next Up” semantics differ slightly; unify on **canonical “resume index”**: earliest incomplete episode unless user marked disordered row.

Technical notes for later phases:

- **Plex**: token + server URL; REST where stable
- **Jellyfin**: API key / user pairing; richer metadata for multi-part specials
- **Multipart**: derive from backend metadata (`Part` index, specials grouping, consecutive S##E## or explicit links) — MUST define deterministic rule in planning

## Constraints

- **Tech**: Prefer **Python** backend — fits FastAPI/Starlette ecosystem; pair with SPA (React/Vue/Svelte acceptable)
- **Deploy**: Docker **required** (`compose` expected for DB + app + optional worker)
- **UX**: “Modern slick” — invest in design system (tokens, motion restraint, dark-mode ready)
- **Self-hosted**: Secrets (API keys) must not ship in images; env/volume mounts

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python backend | User preference + strong async HTTP client story | — Pending |
| Daily batch rebuild | Predictable load; simpler than continuous mutation | — Pending |
| WheelOfFish = server-wide disordered pool | Distinct product promise for household random mode | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. “What This Is” still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-25 after Phase 1 UAT*
