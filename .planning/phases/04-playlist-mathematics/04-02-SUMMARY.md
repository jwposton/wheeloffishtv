---
phase: 04-playlist-mathematics
plan: 02
subsystem: core
tags: [multipart, playlist, pytest, golden-vectors, sch-02]

requires:
  - phase: 04-playlist-mathematics
    provides: Episode DTO, playlist_vectors factories from 04-01
provides:
  - Pure multipart grouping and expansion helpers (D-07, D-08, D-21)
  - 10 golden-vector tests proving SCH-02 adjacency semantics
affects:
  - 04-04 ordered picker (expand_multipart_forward consumer)
  - 04-05 disordered picker (expand_multipart_full_block consumer)
  - 04-06 builder pipeline

tech-stack:
  added: []
  patterns:
    - "Pure functions over Episode DTO with deterministic sort tiebreakers"
    - "Native multipart_group_id only — no SxxExx heuristic fallback"

key-files:
  created:
    - backend/src/wheeloffish/core/playlist/multipart.py
    - backend/tests/unit/test_multipart.py
  modified: []

key-decisions:
  - "Forward expansion (D-07) slices from anchor part_index; null part_index yields full block"
  - "Full-block expansion (D-08) always returns all group parts sorted ascending"
  - "Ungrouped episodes return singleton [anchor] from both expand_* helpers"

patterns-established:
  - "Pattern: expand_multipart_forward vs expand_multipart_full_block split for ordered/disordered rows"

requirements-completed: [SCH-02]

duration: 8min
completed: 2026-05-25
---

# Phase 4 Plan 02: Multipart Grouping & Expansion Summary

**Pure multipart helpers with D-07 forward-from-anchor and D-08 full-block expansion keyed by native multipart_group_id, proven by 10 golden vectors**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-25T21:00:00Z
- **Completed:** 2026-05-25T21:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Implemented four pure helpers in `core/playlist/multipart.py`: `group_by_multipart`, `sort_multipart_block`, `expand_multipart_forward`, `expand_multipart_full_block`
- Locked D-07 vs D-08 divergence: anchor at part 2 → forward `["p2","p3"]`, full block `["p1","p2","p3"]`
- D-21 honored: grouping uses `multipart_group_id` only; no title/SxxExx heuristic
- 10 golden-vector tests pass; no Hypothesis dependency added

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Multipart expansion golden vectors** - `d58dedd` (test)
2. **Task 1 GREEN: Implement multipart helpers** - `1b8994d` (feat)
3. **Task 2: Finalize golden-vector test module** - `781a44d` (test)

**Plan metadata:** pending (docs commit)

## D-07 vs D-08 Verification Snapshot

| Test | Anchor | Forward (D-07) | Full block (D-08) |
|------|--------|----------------|-------------------|
| `test_expand_forward_from_part_two_returns_p2_p3_d07` | p2 (part_index=2) | `["p2","p3"]` | — |
| `test_expand_full_block_returns_all_parts_d08` | p2 (part_index=2) | — | `["p1","p2","p3"]` |
| `test_expand_forward_from_part_one_returns_full_block_d07` | p1 (part_index=1) | `["p1","p2","p3"]` | — |
| `test_expand_full_block_singleton_when_no_group_id` | no group_id | — | `[anchor]` |
| `test_expand_forward_singleton_when_no_group_id` | no group_id | `[anchor]` | — |

No Hypothesis or heuristic fallback added. Wave 2/3 consumers import the four function names exactly as specified in the plan.

## Files Created/Modified

- `backend/src/wheeloffish/core/playlist/multipart.py` — SCH-02 multipart grouping, sorting, forward and full-block expansion
- `backend/tests/unit/test_multipart.py` — 10 golden vectors for D-07, D-08, D-21 edge cases

## Decisions Made

- Null `part_index` on anchor treated as part 1 for forward expansion (returns full sorted block per D-07)
- Sort key `(part_index is None, part_index or 0, id)` ensures null parts sort last with id tiebreaker
- Anchor beyond max group part_index returns `[anchor]` only (never empty list)

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `d58dedd` test(04-02) before implementation
- GREEN gate: `1b8994d` feat(04-02) after tests failed on missing module
- Gate sequence: PASSED

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Multipart helpers ready for ordered picker (04-04) and disordered picker (04-05)
- Signatures frozen for Wave 3 builder slot replacement

## Verification Results

```
uv run ruff check src/wheeloffish/core/playlist/multipart.py tests/unit/test_multipart.py
→ All checks passed

uv run pytest tests/unit/test_multipart.py tests/unit/test_playlist_models.py -q
→ 14 passed

grep -c '^def test_' backend/tests/unit/test_multipart.py
→ 10
```

## Self-Check: PASSED

- FOUND: backend/src/wheeloffish/core/playlist/multipart.py
- FOUND: backend/tests/unit/test_multipart.py
- FOUND: d58dedd, 1b8994d, 781a44d

---
*Phase: 04-playlist-mathematics*
*Completed: 2026-05-25*
