---
phase: 04-playlist-mathematics
plan: 04
subsystem: core
tags: [playlist, ordered, resume, multipart, pytest, golden-vectors]

requires:
  - phase: 04-playlist-mathematics
    provides: expand_multipart_forward from 04-02, completion RESTART semantics from 04-03
  - phase: 02-media-ingestion-catalogs
    provides: ResumeService hybrid on-deck logic and order_episodes (D-10, D-12)
provides:
  - OrderedCursor, start_index_for_row, next_block, make_cursor for Wave 3 builder (PLT-05)
  - Ten golden-vector tests proving serial-from-resume, D-07 multipart blocks, D-17 RESTART
affects:
  - 04-05 disordered picker (parallel row mode)
  - 04-06 builder orchestration (slot allocation across rows)

tech-stack:
  added: []
  patterns:
    - "ResumeService-only start index — no forked on-deck logic (Pitfall 1)"
    - "Position-based cursor advance past entire emitted block (max member pos + 1)"
    - "Frozen OrderedCursor dataclass — immutable cursor state per row"

key-files:
  created:
    - backend/src/wheeloffish/core/playlist/ordered.py
    - backend/tests/unit/test_ordered_picker.py
  modified: []

key-decisions:
  - "start_index_for_row skips ResumeService when restart=True, always returning 0 (D-17)"
  - "Series complete returns len(order_episodes) as exhausted cursor index (D-21)"
  - "next_block advances via max block member position in ordered list, not index + len(block)"

patterns-established:
  - "Pattern: ordered picker consumes order_episodes list directly — specials-after-finale inherited from Phase 2"

requirements-completed: [PLT-05, PLT-04]

duration: 1min
completed: 2026-05-25
---

# Phase 4 Plan 04: Ordered Serial Picker Summary

**ResumeService-driven ordered picker with multipart-forward blocks per slot, RESTART cursor reset, and position-based index advance for Wave 3 builder**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-25T20:39:43Z
- **Completed:** 2026-05-25T20:40:28Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Implemented `OrderedCursor`, `start_index_for_row`, `next_block`, and `make_cursor` in `core/playlist/ordered.py`
- Locked PLT-05 serial semantics: resume/on-deck via `ResumeService().compute` only; `restart=True` forces index 0 even on complete series
- D-07 multipart adjacency: one ordered slot emits forward block from anchor via `expand_multipart_forward`
- D-21 exhaustion: `next_block` at end of ordered list returns `([], index)` without raising
- Ten golden-vector tests pass; 26 total with multipart + resume regression suite

## Wave 3 Import Contract

```python
from wheeloffish.core.playlist.ordered import (
    OrderedCursor,
    start_index_for_row,
    next_block,
    make_cursor,
)

# Per-row cursor init (honors RESTART from completion policy)
cursor = make_cursor(series_id, episodes, on_deck, restart=(outcome.policy_applied == RESTART))

# One slot allocation
ordered = order_episodes(episodes)
by_id = {ep.id: ep for ep in episodes}
block, cursor = next_block(ordered, by_id, cursor.index)
# cursor.index is now advanced past entire block; empty block when exhausted
```

**Restart flag:** When `RowBuildOutcome.policy_applied == RESTART`, pass `restart=True` to `make_cursor` / `start_index_for_row`. This replays from S1E1 regardless of watch state.

**Empty block:** When `start_index_for_row` returns `len(ordered)` or `next_block` returns `[]`, the row is exhausted — builder (04-06) reports `slots_filled < slots_requested` without backfill.

## Task Commits

Each task was committed atomically:

1. **Task 2 RED: Golden-vector tests for ordered picker** - `521ace7` (test)
2. **Task 1 GREEN: Implement OrderedCursor + start_index_for_row + next_block** - `7aedad9` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `backend/src/wheeloffish/core/playlist/ordered.py` — Ordered serial picker with ResumeService start index and multipart-forward `next_block`
- `backend/tests/unit/test_ordered_picker.py` — 10 golden vectors for PLT-05, D-07, D-17 RESTART, specials traversal, end-of-series exhaustion

## Decisions Made

- `restart=True` bypasses `ResumeService` entirely — forces serial replay from index 0 per D-17
- Cursor advance uses `max(position of block members in ordered) + 1` rather than `index + len(block)` for defensive correctness
- Non-empty block assert guards against multipart helper regressions when index is in range

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `521ace7` test(04-04) before implementation (ModuleNotFoundError confirmed)
- GREEN gate: `7aedad9` feat(04-04) after all 10 tests pass
- Gate sequence: PASSED

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ordered picker ready for Wave 3 builder composition in 04-06
- Disordered picker (04-05) is the parallel Wave 2 deliverable
- Builder must pass `restart=True` when completion policy yields RESTART outcome

## Verification Results

```
uv run ruff check src/wheeloffish/core/playlist/ordered.py tests/unit/test_ordered_picker.py
→ All checks passed

uv run pytest tests/unit/test_ordered_picker.py tests/unit/test_multipart.py tests/unit/test_resume_service.py -q
→ 26 passed

grep -c '^def test_' backend/tests/unit/test_ordered_picker.py
→ 10
```

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/ordered.py
- FOUND: backend/tests/unit/test_ordered_picker.py
- FOUND: 521ace7, 7aedad9

---
*Phase: 04-playlist-mathematics*
*Completed: 2026-05-25*
