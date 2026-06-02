---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
plan: 04
subsystem: ui
tags: [react, watch-state, series-detail, vitest]
requires:
  - phase: 09-02
    provides: Catalog watch-state mutation API with reconciliation envelopes
  - phase: 09-03
    provides: Playlist entry parity and origin-aware navigation
provides:
  - Grouped season episode list with S0 specials last
  - Watched / on-deck / unwatched affordances on series detail
  - Episode optimistic and season/series refetch reconcile for watch mutations
affects: [playlist-view, playlist-edit, library]
tech-stack:
  added: []
  patterns:
    - Episode-level optimistic watch updates with rollback on failure
    - Season/series bulk mutations invalidate episode queries without optimistic UI
key-files:
  created:
    - frontend/src/pages/SeriesDetailPage.watch-state.test.tsx
  modified:
    - frontend/src/pages/SeriesDetailPage.tsx
    - frontend/src/hooks/useSeriesEpisodes.ts
key-decisions:
  - "Default season order: numbered seasons ascending, specials (S0) last (D-12)."
  - "Episode actions optimistic; season/series bulk actions refetch-only (locked grey-area B=3)."
patterns-established:
  - "One shared SeriesDetailPage for Library, playlist view, and playlist edit entry."
requirements-completed: [WEB-01, INT-01, INT-02]
duration: 25min
completed: 2026-06-02
---

# Phase 9 Plan 04: Series detail watch-state UI Summary

**Series detail now groups episodes by season with watch-state affordances and provider-backed mutation actions using the catalog API reconcile strategy.**

## Performance

- **Duration:** ~25 min (prior session)
- **Tasks:** 2 automated complete; Task 3 human UAT checkpoint pending operator sign-off on live Plex/Jellyfin
- **Files modified:** 3

## Accomplishments

- Rendered season-grouped episode lists with specials after numbered seasons.
- Added watched / on-deck / unwatched indicators from catalog episode data.
- Wired episode, season, and series watch/unwatch actions with optimistic episode updates and refetch for bulk scopes.
- Added focused Vitest coverage for grouping, affordances, and mutation outcomes.

## Task Commits

1. **Task 1: Render grouped season model** — `8398d5d` (test), `014f572` (feat)
2. **Task 2: Wire watch actions with reconcile** — `93db06b` (test), `314b542` (feat)
3. **Task 3: Human provider UAT** — pending operator approval on Plex/Jellyfin bulk semantics (T-09-01, T-09-03, T-09-04)

## Automated Verification

- `cd frontend && npm test -- SeriesDetailPage.watch-state --run` — 6 passed
- `cd backend && uv run pytest tests/api/test_catalog_watch_mutations.py -q` — green

## Self-Check: PASSED
