---
phase: 06-library-playlist-assignment
plan: 01
subsystem: api
tags: [plex, jellyfin, metadata, catalog-sync, provider_metadata]

# Dependency graph
requires:
  - phase: 02-media-ingestion-catalogs
    provides: cached_series.provider_metadata JSON column and catalog_sync upsert path
provides:
  - Plex map_series enriched with summary, genres, contentRating, studio
  - Jellyfin map_series stub keys for consistent frontend shape
  - Unit + integration tests proving catalog sync round-trip persistence
affects:
  - 06-05 series detail metadata hero
  - 06-03 Library tile UX (indirect — metadata available after re-sync)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Defensive provider_metadata accessors (_str_or_none, _genres_from_metadata)"
    - "Missing Plex fields emit None/[] defaults for stable frontend zero-state"
    - "Jellyfin Phase 6 stubs defer real Overview/Genres mapping to Phase 7"

key-files:
  created:
    - backend/tests/unit/test_plex_metadata_mapper.py
    - backend/tests/unit/test_jellyfin_metadata_mapper.py
  modified:
    - backend/src/wheeloffish/integrations/plex/mappers.py
    - backend/src/wheeloffish/integrations/jellyfin/mappers.py
    - backend/tests/unit/test_catalog_sync_upsert.py

key-decisions:
  - "Missing Plex metadata fields present as None (summary/contentRating/studio) or [] (genres) — not omitted"
  - "Jellyfin ships stub null/empty values; real field mapping deferred to Phase 7 spike"
  - "Malformed Genre arrays filtered to list[str] without TypeError"

patterns-established:
  - "Provider metadata enrichment lives in map_series provider_metadata dict — no schema migration"
  - "Genre extraction uses isinstance guards on dict entries and tag values"

requirements-completed: [WEB-01]

# Metrics
duration: 12min
completed: 2026-05-25
---

# Phase 6 Plan 01: Metadata Mapper Extension Summary

**Plex catalog sync now persists IMDb-like metadata (summary, genres, content rating, studio) into cached_series.provider_metadata; Jellyfin emits matching stub keys for frontend parity.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-25T23:20:00Z
- **Completed:** 2026-05-25T23:31:55Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Extended Plex `map_series` to capture summary, genres, contentRating, and studio alongside ratingKey
- Added Jellyfin stub keys (summary/contentRating/studio=None, genres=[]) for provider-agnostic frontend shape
- Verified catalog_sync `_upsert_series_page` persists and overwrites enriched provider_metadata JSON

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 — failing tests for enriched provider metadata (D-11)** - `58a5df5` (test)
2. **Task 2: Implement enriched mappers — Plex full, Jellyfin stub (D-10, D-11)** - `d1d4475` (feat)
3. **Task 3: Round-trip test through catalog_sync._upsert_series_page (D-10)** - `baf93cb` (test)

## Files Created/Modified

- `backend/src/wheeloffish/integrations/plex/mappers.py` - Enriched provider_metadata with defensive accessors
- `backend/src/wheeloffish/integrations/jellyfin/mappers.py` - Stub metadata keys alongside Type
- `backend/tests/unit/test_plex_metadata_mapper.py` - 4 Plex mapper contract tests
- `backend/tests/unit/test_jellyfin_metadata_mapper.py` - Jellyfin stub shape test
- `backend/tests/unit/test_catalog_sync_upsert.py` - Round-trip persistence + resync overwrite tests

## Decisions Made

- Missing Plex fields emit explicit None/[] defaults (not omitted keys) for predictable frontend zero-state
- Jellyfin real Overview/Genres/OfficialRating/Studios mapping deferred to Phase 7 per research guidance
- Genre extraction filters malformed entries; wrong-type string fields coerced to None via `_str_or_none`

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

| File | Field | Reason |
|------|-------|--------|
| `jellyfin/mappers.py` | summary, genres, contentRating, studio | Phase 6 ship-Plex-first; real Jellyfin mapping deferred to Phase 7 spike |

## Issues Encountered

None

## User Setup Required

None - no external service configuration required. Existing catalog sync will populate enriched metadata on next re-sync.

## Next Phase Readiness

- Plan 06-02 (row append/remove/patch API) can proceed independently
- Plan 06-05 series detail hero can consume provider_metadata once users re-sync catalogs
- Jellyfin users see consistent layout with empty metadata until Phase 7 parity work

---
*Phase: 06-library-playlist-assignment*
*Completed: 2026-05-25*

## Self-Check: PASSED

- All created/modified files exist on disk
- Task commits verified: 58a5df5, d1d4475, baf93cb
