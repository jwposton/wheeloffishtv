---
phase: 10-safe-catalog-prune
fixed_at: 2026-06-02T23:59:00Z
review_path: .planning/phases/10-safe-catalog-prune/10-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 10: Code Review Fix Report

**Fixed at:** 2026-06-02T23:59:00Z
**Source review:** `.planning/phases/10-safe-catalog-prune/10-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: Nightly rebuild overwrites sync absence counts (stale session)

**Files modified:** `backend/src/wheeloffish/core/orchestrator.py`, `backend/tests/unit/test_orchestrator.py`
**Commit:** b2b001e
**Applied fix:** Added `db.expire_all()` after `run_chunked_sync` and before the rebuild loop so rebuild reads fresh `absence_count` values written by sync in a separate session. Added `test_nightly_expire_all_prevents_stale_absence_overwrite`.

### CR-02: Nightly batch sync/reset scoped to one user per connection

**Files modified:** `backend/src/wheeloffish/core/orchestrator.py`, `backend/tests/unit/test_orchestrator.py`
**Commit:** b84dd3f
**Applied fix:** Grouped due playlists by `(connection_id, app_user_id)` instead of `connection_id` only; resolve `UserMediaLink` per owner and run sync/reset/rebuild per group. Added `test_nightly_sync_per_app_user`.

### WR-01: Malformed `series_id` crashes entire connection prune block

**Files modified:** `backend/src/wheeloffish/core/catalog_prune.py`, `backend/tests/unit/test_catalog_prune.py`
**Commit:** fd2db2d
**Applied fix:** Added `_connection_id_for_row` helper catching `ValueError` from `parse_composite_id`; used in `_rows_for_connection` and `execute_auto_prune` connection filter. Added `test_malformed_series_id_skipped_in_connection_filter`.

### WR-02: Per-library `ProviderUnauthorized` still completes sync and accumulates absence

**Files modified:** `backend/src/wheeloffish/core/catalog_sync.py`, `backend/tests/unit/test_catalog_sync_prune.py`
**Commit:** 0ac1b61
**Applied fix:** Track `library_auth_failed` during library loop; on mid-sync unauthorized, clear credentials, set sync status failed, reset absence counters, and return early without purge/prune. Added `test_mid_sync_unauthorized_fails_without_purge_or_prune`.

## Skipped Issues

None.

---

_Fixed: 2026-06-02T23:59:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
