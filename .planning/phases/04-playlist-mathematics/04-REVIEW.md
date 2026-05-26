---
phase: 04-playlist-mathematics
reviewed: 2026-05-25T21:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - backend/src/wheeloffish/domain/playlist.py
  - backend/src/wheeloffish/domain/dto.py
  - backend/src/wheeloffish/core/playlist/__init__.py
  - backend/src/wheeloffish/core/playlist/builder.py
  - backend/src/wheeloffish/core/playlist/completion.py
  - backend/src/wheeloffish/core/playlist/disordered.py
  - backend/src/wheeloffish/core/playlist/multipart.py
  - backend/src/wheeloffish/core/playlist/ordered.py
  - backend/src/wheeloffish/integrations/plex/mappers.py
  - backend/src/wheeloffish/integrations/jellyfin/mappers.py
  - backend/tests/unit/fixtures/playlist_vectors.py
  - backend/src/wheeloffish/core/resume.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-05-25T21:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Phase 4 delivers a coherent pure-function playlist pipeline: domain models, multipart expansion, completion policies, ordered/disordered pickers, and a deterministic `PlaylistBuilder` orchestrator. Golden-vector tests cover the happy paths well and the code correctly delegates resume semantics to `ResumeService`.

One correctness gap stands out: an empty or missing episode snapshot is indistinguishable from a finished series, which can silently drop rows under the default `REMOVE` policy during a rebuild. Several secondary issues affect multipart ordering, duplicate row handling, and disordered anti-repeat when providers omit watch timestamps. No injection, auth-bypass, or secret-handling defects were found in the reviewed scope.

## Critical Issues

### CR-01: Empty episode snapshot triggers series-complete REMOVE exclusion

**File:** `backend/src/wheeloffish/core/playlist/builder.py:78-82`
**Issue:** When a row has no matching `SeriesRebuildInput`, or the input carries an empty `episodes` list, the builder passes `[]` into `evaluate_completion`. `ResumeService.compute()` treats an empty ordered list as `series_complete=True`. With the default `CompletionPolicy.REMOVE`, the row is marked `excluded=True` and omitted from slot allocation — the same outcome as a legitimately finished show. A transient Phase 5 fetch failure, race before first sync, or missing input key therefore silently removes the show from that rebuild with no error surfaced in `PlaylistBuildResult`.

**Fix:** Distinguish “no snapshot” from “series finished”. Skip completion evaluation (or emit a dedicated outcome flag) when `inp is None`, and treat `episodes == []` as inconclusive rather than complete unless the caller explicitly signals completion:

```python
for row in playlist.rows:
    inp = inputs_by_series.get(row.series_id)
    if inp is None:
        row_outcomes.append(
            RowBuildOutcome(
                series_id=row.series_id,
                effective_mode=row.mode,
                excluded=True,  # or a new `skipped_reason="missing_input"`
                policy_applied=None,
            )
        )
        continue
    if not inp.episodes:
        row_outcomes.append(
            RowBuildOutcome(
                series_id=row.series_id,
                effective_mode=row.mode,
                excluded=False,
                policy_applied=None,
            )
        )
        continue
    completion_event = evaluate_completion(row, inp.episodes, inp.on_deck)
    row_outcomes.append(apply_policy(row, completion_event))
```

Alternatively, add an explicit guard inside `evaluate_completion` that returns `None` when `not episodes`.

## Warnings

### WR-01: Multipart parts sharing the same episode_index rely on input list order

**File:** `backend/src/wheeloffish/core/resume.py:44-45` (consumed by `backend/src/wheeloffish/core/playlist/ordered.py:139`)
**Issue:** `order_episodes()` sorts within a season by `episode_index` only. Multipart parts from Plex/Jellyfin often share the same `episode_index` with differing `part_index`. Stable sort preserves provider list order, not `part_index` order. If the live snapshot arrives out of part order, ordered serial picks and cursor advancement in `next_block` can emit parts in the wrong sequence or skip parts that appear earlier in the ordered list but later in the walk.

**Fix:** Secondary-sort by `part_index` inside `order_episodes`:

```python
season_eps.sort(key=lambda e: (e.episode_index, e.part_index is None, e.part_index or 0, e.id))
```

Add a golden-vector test with deliberately shuffled multipart input order to lock the behavior.

### WR-02: Duplicate `series_id` in playlist rows — last row silently wins

**File:** `backend/src/wheeloffish/core/playlist/builder.py:107`
**Issue:** `outcome_by_series = {o.series_id: o for o in row_outcomes}` collapses multiple rows for the same series. If a playlist ever contains the same `series_id` twice (different modes or policies), only the last row's `effective_mode` and exclusion state drive slot filling. The earlier row's configuration is ignored without warning.

**Fix:** Validate uniqueness at the `Playlist` model layer (`@model_validator`) or key outcomes by row index / composite id. At minimum, document and assert single-row-per-series in Phase 5 persistence.

### WR-03: Disordered anti-repeat ignores in-progress episodes without `last_viewed_at`

**File:** `backend/src/wheeloffish/core/playlist/disordered.py:28-30`
**Issue:** D-03 excludes the last 15 episodes ranked by `last_viewed_at`. Episodes with partial progress (`percent_watched >= 5`) but `last_viewed_at is None` are classified as “unwatched” and always remain in the eligible pool. If a provider omits the timestamp for in-progress items, the disordered picker can re-select the same partially watched episode on consecutive rebuilds, undermining the anti-repeat intent.

**Fix:** Treat partial-progress episodes as watched for exclusion purposes when `last_viewed_at` is absent — e.g., fold `classify_watch(ep) != UNWATCHED` into the watched bucket, using `last_viewed_at` when present and falling back to watch-state classification otherwise.

### WR-04: `start_index_for_row` raises unhandled `StopIteration` on stale resume pointer

**File:** `backend/src/wheeloffish/core/playlist/ordered.py:42-43`
**Issue:** `next(i for i, ep in enumerate(ordered) if ep.id == cursor.episode_id)` has no default. If the resume cursor references an episode id absent from the current snapshot (stale on-deck, filtered episode, provider drift), the builder crashes with `StopIteration` instead of degrading gracefully.

**Fix:**

```python
for i, ep in enumerate(ordered):
    if ep.id == cursor.episode_id:
        return i
return 0  # or len(ordered) to skip emission
```

## Info

### IN-01: Production code uses `assert` for invariants

**File:** `backend/src/wheeloffish/core/playlist/ordered.py:42-43,56`, `backend/src/wheeloffish/core/playlist/disordered.py:24-25`
**Issue:** Several invariants are enforced with `assert`, which is stripped when Python runs with `-O`. Failures would surface as opaque errors downstream rather than explicit domain exceptions.

**Fix:** Replace with explicit checks raising `ValueError` or a domain-specific exception where the condition guards externally supplied data.

### IN-02: `resolve_row_policy` is exported but unused in the build pipeline

**File:** `backend/src/wheeloffish/core/playlist/completion.py:75-77`, `backend/src/wheeloffish/core/playlist/builder.py:81-82`
**Issue:** `apply_policy` reads `row.completion_policy` directly; `resolve_row_policy` is never called during `PlaylistBuilder.build()`. This matches the Phase 5 “reference data” plan for `default_completion_policy`, but the unused hook may confuse future contributors who expect centralized policy resolution.

**Fix:** Either call `resolve_row_policy(playlist, row)` inside `apply_policy` / the builder loop, or trim the export until Phase 5 row-creation wiring lands.

---

_Reviewed: 2026-05-25T21:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
