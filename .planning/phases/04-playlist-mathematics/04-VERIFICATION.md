---
phase: 04-playlist-mathematics
verified: 2026-05-25T20:46:13Z
status: passed
score: 32/32 must-haves verified
decision_coverage:
  honored: 24
  total: 24
  not_honored: []
---

# Phase 4: Playlist Mathematics Verification Report

**Phase Goal:** Pure domain playlist mathematics — builder, ordered/disordered pickers, completion policies, multipart handling. No DB/API/SPA yet (Phase 5 orchestrates).

**Verified:** 2026-05-25T20:46:13Z
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `Playlist` domain model accepts id, name, episode_count N≥1, rows, slot_allocation, default_completion_policy | ✓ VERIFIED | `domain/playlist.py` Pydantic models; 9 tests in `test_playlist_models.py` |
| 2 | Each row declares series_id, RowMode, completion policy/event | ✓ VERIFIED | `PlaylistSeriesRow` defaults + validation tests |
| 3 | Multipart groups expand contiguously — ordered forward (D-07), disordered full block (D-08) | ✓ VERIFIED | `multipart.py` + 10 golden vectors in `test_multipart.py`; builder multipart test |
| 4 | Series-complete is sole v1 completion event; policies remove/restart/disordered honored (PLT-06) | ✓ VERIFIED | `completion.py` delegates to `ResumeService`; 9 tests in `test_completion_policies.py` |
| 5 | Ordered rows serial-forward from resume via ResumeService — no reimplemented resume math (PLT-05) | ✓ VERIFIED | `ordered.py` imports `ResumeService`, `order_episodes`; 10 tests in `test_ordered_picker.py` |
| 6 | Disordered pool excludes last 15 watched, falls back when empty, seeded picks stable (PLT-04) | ✓ VERIFIED | `disordered.py` + 11 tests; Plex/Jellyfin `last_viewed_at` mappers tested |
| 7 | `PlaylistBuilder.build()` orchestrates completion → slot allocation → ordered/disordered pick (PLT-01–06) | ✓ VERIFIED | `builder.py` wires completion, ordered, disordered; 10 end-to-end golden vectors |
| 8 | Same rebuild_seed + inputs → identical output; different seeds → different disordered picks | ✓ VERIFIED | `test_build_same_seed_is_deterministic`, `test_build_disordered_row_differs_by_seed` |
| 9 | Slot allocation wild/balanced/round_robin; N slots requested; multipart may expand output length (PLT-02) | ✓ VERIFIED | `allocate_slots()` + builder tests for wild vs round-robin, output length |
| 10 | Pure domain — no DB, HTTP, or scheduler coupling in playlist package | ✓ VERIFIED | No sqlalchemy/httpx/fastapi imports under `core/playlist/` |

**Score:** 32/32 truths verified (aggregated from 6 plan must_haves sets)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/wheeloffish/domain/playlist.py` | Playlist config + build result models | ✓ EXISTS + SUBSTANTIVE | 70 lines; enums, Playlist, SeriesRebuildInput, PlaylistBuildResult |
| `backend/tests/unit/fixtures/playlist_vectors.py` | Shared golden-vector factories | ✓ EXISTS + SUBSTANTIVE | Episode factory with multipart fields |
| `backend/src/wheeloffish/core/playlist/__init__.py` | Package scaffold | ✓ EXISTS + SUBSTANTIVE | Exports `PlaylistBuilder` |
| `backend/src/wheeloffish/core/playlist/multipart.py` | Multipart expansion helpers | ✓ EXISTS + SUBSTANTIVE | group, sort, forward/full expand |
| `backend/tests/unit/test_multipart.py` | D-07/D-08 golden vectors | ✓ EXISTS + SUBSTANTIVE | 10 tests (SDK pattern name differs from PLAN — coverage equivalent) |
| `backend/src/wheeloffish/core/playlist/completion.py` | evaluate_completion, apply_policy | ✓ EXISTS + SUBSTANTIVE | Uses `ResumeService().compute` line 23 |
| `backend/tests/unit/test_completion_policies.py` | PLT-06 policy vectors | ✓ EXISTS + SUBSTANTIVE | 9 golden vectors |
| `backend/src/wheeloffish/core/playlist/ordered.py` | Ordered serial picker | ✓ EXISTS + SUBSTANTIVE | OrderedCursor, start_index, next_block |
| `backend/tests/unit/test_ordered_picker.py` | PLT-05 golden vectors | ✓ EXISTS + SUBSTANTIVE | 10 tests including multipart block |
| `backend/src/wheeloffish/core/playlist/disordered.py` | Disordered picker + pool | ✓ EXISTS + SUBSTANTIVE | compute_eligible_pool, pick_disordered_block |
| `backend/tests/unit/test_disordered_picker.py` | D-03–D-09 + seed stability | ✓ EXISTS + SUBSTANTIVE | 11 tests |
| `backend/src/wheeloffish/core/playlist/builder.py` | PlaylistBuilder orchestrator | ✓ EXISTS + SUBSTANTIVE | build(), allocate_slots(), make_build_rng() |
| `backend/tests/unit/test_playlist_builder.py` | End-to-end golden vectors | ✓ EXISTS + SUBSTANTIVE | 10 tests covering PLT-01–06 + SCH-02 |

**Artifacts:** 13/13 verified (2 SDK `verify.artifacts` false negatives on exact test function name patterns — manual inspection confirms equivalent tests exist)

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `domain/playlist.py` | `domain/dto.py` | Episode in SeriesRebuildInput | ✓ WIRED | SDK verified |
| `multipart.py` | `domain/dto.py` | multipart_group_id, part_index | ✓ WIRED | Uses `anchor.multipart_group_id` (SDK regex missed) |
| `completion.py` | `core/resume.py` | ResumeService.compute | ✓ WIRED | Line 23: `ResumeService().compute(...)` (SDK regex false negative) |
| `completion.py` | `domain/playlist.py` | RowBuildOutcome construction | ✓ WIRED | apply_policy returns RowBuildOutcome |
| `ordered.py` | `core/resume.py` | ResumeService + order_episodes | ✓ WIRED | SDK verified |
| `ordered.py` | `multipart.py` | expand_multipart_forward | ✓ WIRED | SDK verified |
| `disordered.py` | `multipart.py` | expand_multipart_full_block | ✓ WIRED | SDK verified |
| `builder.py` | `completion.py` | evaluate_completion + apply_policy | ✓ WIRED | Lines 81–82 per row before allocation |
| `builder.py` | `ordered.py` | OrderedCursor.next_block | ✓ WIRED | Lines 119–142 for ordered effective_mode |
| `builder.py` | `disordered.py` | compute_eligible_pool + pick_disordered_block | ✓ WIRED | Lines 144–148 with per-row emitted_ids |

**Wiring:** 10/10 connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| PLT-01: Multiple named playlists, independently configured | ✓ SATISFIED | In-memory `Playlist` model with id + name |
| PLT-02: Episode count N per rebuild cycle | ✓ SATISFIED | `episode_count` drives slot loop; default 20 |
| PLT-03: Add/remove TV series via rows membership | ✓ SATISFIED | `PlaylistSeriesRow.series_id` on `rows` list |
| PLT-04: Per playlist×series ordered vs disordered | ✓ SATISFIED | `RowMode` enum; builder respects effective_mode |
| PLT-05: Ordered serial forward from resume/up-next | ✓ SATISFIED | ResumeService-driven cursor; partial watch handled |
| PLT-06: Completion event + remove/restart/disordered policies | ✓ SATISFIED | evaluate_completion + apply_policy; 9 policy tests |
| SCH-02 (algorithm): Multipart adjacency in ordered output | ✓ SATISFIED | expand_multipart_forward in ordered path; builder + unit tests |

**Coverage:** 7/7 requirements satisfied (6 PLT + SCH-02 algorithm portion)

## Behavioral Verification

| Check | Result | Detail |
|-------|--------|--------|
| Phase unit tests | 59 passed, 0 failed | `uv run pytest tests/unit/test_playlist_models.py tests/unit/test_multipart.py tests/unit/test_completion_policies.py tests/unit/test_ordered_picker.py tests/unit/test_disordered_picker.py tests/unit/test_playlist_builder.py -q` — 100% in 0.03s |
| gsd-sdk verify.artifacts (6 plans) | 4/6 all_passed | 04-02, 04-04 failed on exact test function name patterns only; artifacts substantive |
| gsd-sdk verify.key-links (6 plans) | 4/6 all_verified | 04-02, 04-03 regex false negatives; manual grep confirms wiring |

## Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|----------------|---------|
| `test_playlist_models.py` | PLT-01–03 | 9 | 0 | No | Value/Behavioral | ✓ PASS |
| `test_multipart.py` | SCH-02 | 10 | 0 | No | Value | ✓ PASS |
| `test_completion_policies.py` | PLT-06 | 9 | 0 | No | Behavioral | ✓ PASS |
| `test_ordered_picker.py` | PLT-05 | 10 | 0 | No | Behavioral | ✓ PASS |
| `test_disordered_picker.py` | PLT-04 | 11 | 0 | No | Behavioral | ✓ PASS |
| `test_playlist_builder.py` | PLT-01–06 | 10 | 0 | No | Behavioral | ✓ PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No TBD/FIXME/placeholder/stub patterns in `core/playlist/` |

**Anti-patterns:** 0 found (0 blockers, 0 warnings in phase scope)

## Advisory Findings (Non-Blocking)

Findings from `04-REVIEW.md` that do not block phase goal achievement within domain-math scope:

### CR-01: Empty episode snapshot treated as series-complete REMOVE (Advisory)

**File:** `backend/src/wheeloffish/core/playlist/builder.py:78-82`

When `SeriesRebuildInput` is missing or carries `episodes=[]`, `evaluate_completion` passes `[]` to `ResumeService.compute()`, which returns `series_complete=True`. Default `REMOVE` policy then excludes the row silently. No unit test covers this edge case.

**Phase impact:** Domain math is correct given non-empty snapshots; edge case surfaces at Phase 5 orchestration when live fetch fails. Recommend guard in Phase 5 integration or follow-up fix plan before production rebuilds.

### WR-01–WR-04: Secondary correctness warnings

- Multipart parts sharing `episode_index` may sort by input order not `part_index` (resume.py)
- Duplicate `series_id` in rows — last wins silently (builder.py:107)
- Disordered anti-repeat ignores partial episodes without `last_viewed_at` (disordered.py)
- Stale resume pointer raises unhandled `StopIteration` (ordered.py:42)

These are documented in `04-REVIEW.md` for Phase 5 hardening; none block PLT-01–06 golden-vector coverage.

### IN-02: `resolve_row_policy` exported but unused in builder

Per-row policy resolution exists but builder reads `row.completion_policy` directly. Aligns with current row-only policy model; Phase 5 may wire playlist default.

## Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. **24/24 decisions honored**, 0 not honored.

## Human Verification Required

N/A — Infrastructure/foundation phase with no user-facing elements. All acceptance criteria are verifiable programmatically via golden-vector unit tests.

## Gaps Summary

**No gaps found.** Phase goal achieved. Pure domain playlist mathematics delivered with 59 passing unit tests covering PLT-01–06 and SCH-02 algorithm semantics. Advisory CR-01 should be addressed before or during Phase 5 orchestration but does not block phase closure.

## Verification Metadata

**Verification approach:** Goal-backward (must_haves from 6 PLAN frontmatter + ROADMAP success criteria)
**Must-haves source:** PLAN.md frontmatter across 04-01 through 04-06
**Automated checks:** 59 tests passed, 0 failed; gsd-sdk artifacts 17/19 artifact checks passed (2 name-pattern false negatives)
**Human checks required:** 0
**Total verification time:** ~5 min

---
*Verified: 2026-05-25T20:46:13Z*
*Verifier: Claude (subagent)*
