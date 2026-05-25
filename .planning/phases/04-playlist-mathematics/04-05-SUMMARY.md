---
phase: 04-playlist-mathematics
plan: 05
subsystem: core
tags: [playlist, disordered, last-viewed, multipart, pytest, golden-vectors, plex, jellyfin]

requires:
  - phase: 04-playlist-mathematics
    provides: expand_multipart_full_block from 04-02, Episode DTO from 04-01
provides:
  - Episode.last_viewed_at populated by Plex + Jellyfin mappers (D-06)
  - compute_eligible_pool + pick_disordered_block with LAST_VIEWED_EXCLUSION_SIZE=15 (PLT-04)
  - 11 golden-vector tests for D-03..D-09 + seeded determinism
affects:
  - 04-06 builder orchestration (slot allocation, emitted_ids tracking across rows)

tech-stack:
  added: []
  patterns:
    - "Caller-owned random.Random — picker never instantiates RNG (D-24)"
    - "Last-15 exclusion with id-ascending tie-break on equal last_viewed_at"
    - "Pick-time fallback to full episodes_by_id when eligible pool exhausted (D-05)"

key-files:
  created:
    - backend/src/wheeloffish/core/playlist/disordered.py
    - backend/tests/unit/test_disordered_picker.py
    - backend/tests/unit/test_provider_mappers.py
  modified:
    - backend/src/wheeloffish/domain/dto.py
    - backend/src/wheeloffish/integrations/plex/mappers.py
    - backend/src/wheeloffish/integrations/jellyfin/mappers.py
    - backend/tests/unit/fixtures/playlist_vectors.py
    - backend/tests/integrations/test_jellyfin_client.py

key-decisions:
  - "Episode.last_viewed_at defaults None; Plex lastViewedAt=0 maps to None (never-played sentinel)"
  - "Malformed provider timestamps map to None via try/except — no ingestion exceptions (T-04-05-01)"
  - "compute_eligible_pool D-05 fallback returns full episode list when kept set is empty"
  - "pick_disordered_block D-05 deep fallback uses episodes_by_id minus emitted_ids when eligible candidates empty"

patterns-established:
  - "Pattern: Wave 3 builder must add every id in returned block to emitted_ids before next pick (D-04, D-09)"

requirements-completed: [PLT-04, PLT-03]

duration: 8min
completed: 2026-05-25
---

# Phase 4 Plan 05: Disordered Picker Summary

**Last-15 exclusion disordered picker with Episode.last_viewed_at from Plex/Jellyfin mappers, multipart full-block expansion, and seeded random.Random determinism for Wave 3 builder**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-25T20:45:00Z
- **Completed:** 2026-05-25T20:53:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Extended `Episode` DTO with `last_viewed_at: datetime | None = None` (D-06)
- Plex mapper parses `lastViewedAt` unix seconds; Jellyfin parses `UserData.LastPlayedDate` ISO string
- Implemented `compute_eligible_pool` and `pick_disordered_block` with `LAST_VIEWED_EXCLUSION_SIZE = 15`
- D-03 last-15 exclusion, D-05 dual fallback (pool compute + pick-time), D-08/D-09 multipart full-block via `expand_multipart_full_block`
- 9 mapper tests + 11 disordered golden vectors; 95 unit tests green

## Wave 3 Import Contract

```python
from wheeloffish.core.playlist.disordered import (
    LAST_VIEWED_EXCLUSION_SIZE,
    compute_eligible_pool,
    pick_disordered_block,
)

eligible = compute_eligible_pool(episodes)
block = pick_disordered_block(eligible, episodes_by_id, emitted_ids, rng)
if block:
    for ep in block:
        emitted_ids.add(ep.id)
```

**Function signatures (locked):**

- `LAST_VIEWED_EXCLUSION_SIZE: int = 15`
- `compute_eligible_pool(episodes: list[Episode]) -> list[Episode]`
- `pick_disordered_block(eligible_pool, episodes_by_id, emitted_ids, rng) -> list[Episode] | None`

**Episode.last_viewed_at parsing:**

| Provider | Source field | Rule |
|----------|-------------|------|
| Plex | `lastViewedAt` (unix seconds) | `None` or `0` → None; else `datetime.fromtimestamp(int, tz=UTC)` |
| Jellyfin | `UserData.LastPlayedDate` (ISO) | missing/empty → None; else `fromisoformat` with `Z` → `+00:00` |

**Wave 3 emitted_ids obligation:** After each `pick_disordered_block` call, builder MUST add all returned block member ids to `emitted_ids` before the next pick. Multipart blocks may include parts excluded from the eligible pool (D-09).

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend Episode DTO + Plex/Jellyfin mappers with last_viewed_at** - `337e05f` (feat)
2. **Task 2: Implement core/playlist/disordered.py picker** - `19ab1de` (feat)
3. **Task 3: Golden-vector tests for disordered picker** - `0cda542` (test)

## Files Created/Modified

- `backend/src/wheeloffish/domain/dto.py` - Added `last_viewed_at: datetime | None = None`
- `backend/src/wheeloffish/integrations/plex/mappers.py` - Parse `lastViewedAt` with malformed-value guard
- `backend/src/wheeloffish/integrations/jellyfin/mappers.py` - Parse `UserData.LastPlayedDate` with malformed-value guard
- `backend/src/wheeloffish/core/playlist/disordered.py` - Eligible pool + disordered block picker
- `backend/tests/unit/test_provider_mappers.py` - 10 D-06 mapper/DTO tests
- `backend/tests/unit/test_disordered_picker.py` - 11 golden-vector tests (D-03..D-09)
- `backend/tests/unit/fixtures/playlist_vectors.py` - `episode()` accepts `last_viewed_at`
- `backend/tests/integrations/test_jellyfin_client.py` - Episode field set includes `last_viewed_at`

## Decisions Made

- Malformed timestamp values map to `None` rather than raising — protects ingestion path (T-04-05-01)
- Ruff UP017 applied `datetime.UTC` alias in mapper/tests (consistent with project Python 3.13)
- Tie-break on equal `last_viewed_at`: sort key `(-timestamp, id)` ascending — lower id excluded first when tied

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated jellyfin integration test Episode field assertion**
- **Found during:** Task 1 verification
- **Issue:** `test_dto_shape_matches_plex` asserted exact Episode field set without `last_viewed_at`
- **Fix:** Added `"last_viewed_at"` to expected field set
- **Files modified:** `backend/tests/integrations/test_jellyfin_client.py`
- **Verification:** 34 tests pass in Task 1 verify command
- **Committed in:** `337e05f`

**2. [Rule 1 - Bug] Corrected D-03 golden vector expected ids**
- **Found during:** Task 3 verification
- **Issue:** Test expected ep-16..ep-20 kept but monotonic hours mean ep-01..ep-05 are oldest (kept after excluding 15 most recent)
- **Fix:** Updated assertion to `{ep-01..ep-05}`
- **Files modified:** `backend/tests/unit/test_disordered_picker.py`
- **Verification:** 11/11 disordered tests pass
- **Committed in:** `0cda542`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Minimal; both required for regression correctness. Plan said not to modify integration tests but field-set assertion update was unavoidable.

## Issues Encountered

None beyond deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Disordered picker contract locked for 04-06 builder orchestration
- Builder must wire `compute_eligible_pool` per disordered row, pass shared `emitted_ids` and seeded `rng`, and expand block ids into `emitted_ids` after each pick
- No blockers for Wave 3 plan 04-06

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/disordered.py
- FOUND: backend/tests/unit/test_disordered_picker.py
- FOUND: backend/tests/unit/test_provider_mappers.py
- FOUND: 337e05f
- FOUND: 19ab1de
- FOUND: 0cda542

---
*Phase: 04-playlist-mathematics*
*Completed: 2026-05-25*
