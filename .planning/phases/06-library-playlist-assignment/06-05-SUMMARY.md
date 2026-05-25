---
phase: 06-library-playlist-assignment
plan: 05
subsystem: ui
tags: [react, series-detail, metadata, playlists, tdd]

# Dependency graph
requires:
  - phase: 06-library-playlist-assignment
    plan: 01
    provides: provider_metadata summary, genres, contentRating, studio from catalog sync
  - phase: 06-library-playlist-assignment
    plan: 03
    provides: AddToPlaylistMenu shared dropdown + quick create
provides:
  - SeriesMetadataHero IMDb-like layout with graceful empty-field omission
  - Series detail primary Add to playlist CTA reusing AddToPlaylistMenu
  - SeriesProviderMetadata typed frontend contract
  - Planning docs aligned with cancelled ADM-01/ADM-02 and PLT-03 UX complete
affects:
  - phase-6-validation
  - phase-7-jellyfin-metadata-parity

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SeriesMetadataHero omits null/empty metadata — no N/A placeholders (D-10)"
    - "Detail page reuses AddToPlaylistMenu with Button trigger (D-09)"
    - "Back link reads Back to Library consistently (D-03)"

key-files:
  created:
    - frontend/src/components/series/SeriesMetadataHero.tsx
    - frontend/src/pages/SeriesDetailPage.test.tsx
  modified:
    - frontend/src/pages/SeriesDetailPage.tsx
    - frontend/src/api/types.ts
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md

key-decisions:
  - "SeriesProviderMetadata interface replaces Record<string, unknown> for typed hero fields"
  - "Hero owns focusable h2; loading skeleton mirrors md+ flex layout"
  - "PLT-03 UX marked Complete in REQUIREMENTS after Phase 6 vertical slice ships"

patterns-established:
  - "Series detail hero: poster left, metadata right on md+; stacked mobile"

requirements-completed: [PLT-03, WEB-01]

# Metrics
duration: 8min
completed: 2026-05-25
---

# Phase 6 Plan 05: Series Detail Hero Summary

**Series detail page renders IMDb-like metadata hero from provider_metadata, primary Add to playlist via shared menu, and planning docs reflect cancelled global WheelOfFish scope.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-26T00:45:00Z
- **Completed:** 2026-05-26T00:53:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `SeriesMetadataHero` displays poster, title, year, content rating badge, genre chips, studio, and summary with empty-field omission
- `SeriesDetailPage` integrates hero, primary Add to playlist button, Back to Library link, and preserved ResumePreview
- `SeriesProviderMetadata` typed in frontend API types; unit tests cover metadata and CTA rendering
- PROJECT/REQUIREMENTS/ROADMAP updated — ADM cancelled, PLT-03 UX complete, Phase 6 5/5

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: SeriesDetailPage metadata tests** - `c5aaab4` (test)
2. **Task 1 GREEN: SeriesMetadataHero + detail enrichment** - `89a37ab` (feat)
3. **Task 2: Planning docs WheelOfFish cleanup** - `0effc4a` (docs)

## Files Created/Modified

- `frontend/src/components/series/SeriesMetadataHero.tsx` - Enriched metadata hero layout
- `frontend/src/pages/SeriesDetailPage.tsx` - Hero integration, AddToPlaylistMenu, Back to Library
- `frontend/src/api/types.ts` - SeriesProviderMetadata interface
- `frontend/src/pages/SeriesDetailPage.test.tsx` - Metadata and CTA rendering tests
- `.planning/PROJECT.md` - Library UX moved to Validated; last updated
- `.planning/REQUIREMENTS.md` - Core value cleaned; PLT-03 UX Complete
- `.planning/ROADMAP.md` - Overview fixed; Phase 6 5/5 complete

## Decisions Made

- Typed `SeriesProviderMetadata` instead of loose Record for hero field access
- Loading skeleton mirrors hero flex layout for consistent layout shift
- PLT-03 UX traceability marked Complete now that Phase 6 vertical slice ships

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- Task 1: RED `c5aaab4` → GREEN `89a37ab` ✓

## Issues Encountered

None

## User Setup Required

None - enriched metadata appears after existing catalog re-sync (Plan 06-01).

## Next Phase Readiness

- Phase 6 vertical slice complete end-to-end — ready for 06-VALIDATION UAT
- Jellyfin users see consistent hero layout with empty metadata until Phase 7 parity

---
*Phase: 06-library-playlist-assignment*
*Completed: 2026-05-25*

## Self-Check: PASSED

- FOUND: frontend/src/components/series/SeriesMetadataHero.tsx
- FOUND: frontend/src/pages/SeriesDetailPage.test.tsx
- FOUND: .planning/phases/06-library-playlist-assignment/06-05-SUMMARY.md
- FOUND: c5aaab4, 89a37ab, 0effc4a
