---
phase: 02-media-ingestion-catalogs
plan: 01
subsystem: api
tags: [respx, pydantic, fastapi, domain, resume, fixtures, pytest]

requires:
  - phase: 01-foundations-packaging
    provides: FastAPI app, SecretsVault, config/settings, pytest CI baseline
provides:
  - respx dev dependency and extended conftest fixtures
  - 10 sanitized Plex/Jellyfin JSON fixtures
  - domain DTOs, composite IDs, MediaProvider protocol, ProviderError taxonomy
  - ResumeService with D-10/D-11/D-12 golden-vector unit tests
  - GET /api/v1/meta/providers config endpoint
affects: [02-02, 02-03, 02-04, 02-05, 02-06, provider integrations, catalog routes]

tech-stack:
  added: [respx>=0.21]
  patterns:
    - Composite stable IDs with URL-encoded native segments (D-19)
    - Two-layer DTOs for browse vs live episode data (D-20)
    - Pure ResumeService domain logic independent of HTTP
    - Sanitized fixture-based provider test scaffold (D-03)

key-files:
  created:
    - backend/src/wheeloffish/domain/ids.py
    - backend/src/wheeloffish/domain/dto.py
    - backend/src/wheeloffish/core/resume.py
    - backend/src/wheeloffish/integrations/base.py
    - backend/src/wheeloffish/integrations/errors.py
    - backend/src/wheeloffish/api/routes/meta.py
    - backend/tests/fixtures/plex/
    - backend/tests/fixtures/jellyfin/
    - backend/tests/unit/test_composite_ids.py
    - backend/tests/unit/test_watch_classification.py
    - backend/tests/unit/test_resume_service.py
    - backend/tests/api/test_meta_routes.py
  modified:
    - backend/pyproject.toml
    - backend/tests/conftest.py
    - backend/src/wheeloffish/core/config.py
    - backend/src/wheeloffish/main.py
    - .env.example

key-decisions:
  - "Episode.is_special + special_for_season fields drive D-12 specials ordering"
  - "StrEnum for WatchState to satisfy Ruff UP042"
  - "Composite ID parse uses split(': ', 2) so native IDs may contain colons"

patterns-established:
  - "Pattern: format_composite_id / parse_composite_id round-trip with URL encoding"
  - "Pattern: classify_watch thresholds at 5% and 95% with provider override"
  - "Pattern: conftest load_fixture('plex/pin_create') for respx integration tests"

requirements-completed: [INT-01, INT-03]

duration: 15min
completed: 2026-05-25
---

# Phase 2 Plan 01 Summary

**Wave 0 domain primitives — composite IDs, ResumeService golden vectors, respx fixtures, and meta providers API**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-25
- **Completed:** 2026-05-25
- **Tasks:** 4
- **Files modified:** 28

## Accomplishments

- Added `respx` dev dependency and extended `conftest.py` with `async_client`, `vault`, `app_user_id`, and `load_fixture` helpers
- Created 10 sanitized Plex/Jellyfin JSON fixtures (no real tokens, IPs, or credentials)
- Implemented domain layer: composite IDs, DTOs, `MediaProvider` protocol, `ProviderError` taxonomy, and `ResumeService`
- Shipped `GET /api/v1/meta/providers` wired to `WOF_ENABLED_PROVIDERS` config

## Task Commits

Single plan commit:

1. **All tasks (1–4)** - `79e5b01` (feat)

**Plan metadata:** pending (this summary)

## Files Created/Modified

- `backend/src/wheeloffish/domain/ids.py` — composite ID format/parse with URL encoding
- `backend/src/wheeloffish/domain/dto.py` — Library, Series, Episode, ResumeCursor DTOs
- `backend/src/wheeloffish/core/resume.py` — watch classification, specials ordering, hybrid resume
- `backend/src/wheeloffish/integrations/base.py` — MediaProvider protocol skeleton
- `backend/src/wheeloffish/integrations/errors.py` — structured provider error codes
- `backend/src/wheeloffish/api/routes/meta.py` — enabled providers endpoint
- `backend/tests/fixtures/` — 10 sanitized Plex/Jellyfin API recordings
- `backend/tests/unit/` — composite ID, watch classification, resume golden vectors
- `backend/tests/api/test_meta_routes.py` — meta route smoke test
- `.env.example` — Phase 2 config vars documented

## Decisions Made

- Used `StrEnum` for `WatchState` instead of `(str, Enum)` to satisfy Ruff lint rules
- Added `is_special` / `special_for_season` on `Episode` to support D-12 ordering in unit tests without provider mappers

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule — Lint] WatchState StrEnum migration**
- **Found during:** Final verification (`ruff check`)
- **Issue:** UP042 flagged `class WatchState(str, Enum)`
- **Fix:** Changed to `StrEnum`
- **Files modified:** `backend/src/wheeloffish/core/resume.py`
- **Verification:** `uv run ruff check .` passes

---

**Total deviations:** 1 auto-fixed (lint)
**Impact on plan:** No scope change; lint compliance only.

## Issues Encountered

None

## User Setup Required

None — no external service configuration required.

## Verification

- `cd backend && uv run ruff check .` — pass
- `cd backend && uv run pytest -q` — 29 passed
- `grep -rE 'X-Plex-Token|192\.168\.|password' backend/tests/fixtures/` — clean

## Next Phase Readiness

- Domain primitives and test infra ready for provider integration plans (02-02+)
- `load_fixture` + respx scaffold available for Plex/Jellyfin client tests
- ResumeService golden vectors locked for catalog/resume route plans

---
*Phase: 02-media-ingestion-catalogs*
*Completed: 2026-05-25*

## Self-Check

PASSED
