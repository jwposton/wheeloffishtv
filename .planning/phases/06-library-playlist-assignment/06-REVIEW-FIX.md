---
phase: 06-library-playlist-assignment
fixed_at: 2026-05-25T20:18:00Z
fix_scope: critical_warning
findings_in_scope: 6
fixed: 6
skipped: 0
already_fixed: 1
iteration: 1
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed:** 2026-05-25T20:18:00Z
**Scope:** critical_warning (Critical + Warning)
**Status:** all_fixed

## Summary

Applied all six findings from `06-REVIEW.md`. CR-01 (series ID URL encoding) was already present in the working tree before this fix pass; the remaining five issues were patched and verified with tests.

## Fixes Applied

### CR-01: Row DELETE/PATCH URLs omit series ID encoding

**Status:** already_fixed
**File:** `frontend/src/api/playlists.ts`
**Action:** `encodeURIComponent(seriesId)` was already applied to `removePlaylistRow` and `patchPlaylistRow` path segments.

### CR-02: Optimistic append rollback desyncs edit UI on 409 race

**Status:** fixed
**Files:** `frontend/src/components/playlists/TwoPanePicker.tsx`, `frontend/src/components/playlists/PlaylistForm.tsx`
**Action:** Treat HTTP 409 on append as success (row already persisted). Disable Save while row mutations are pending via `onRowMutationsPendingChange` callback.

### WR-01: Quick-create does not invalidate playlists query cache

**Status:** fixed
**File:** `frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx`
**Action:** Invalidate `["playlists"]` query key after successful `createPlaylistWithSeries`.

### WR-02: Concurrent duplicate append can surface 500 instead of 409

**Status:** fixed
**File:** `backend/src/wheeloffish/api/routes/playlists.py`
**Action:** Wrap append `db.commit()` in `IntegrityError` handler mapping unique-constraint violations to HTTP 409.

### WR-03: Add-to-playlist menu treats 409 as generic failure

**Status:** fixed
**File:** `frontend/src/components/playlists/AddToPlaylistMenu.tsx`
**Action:** Show informational toast when append returns 409 (`Already in {name}`).

### WR-04: Append endpoint does not verify series exists in user catalog

**Status:** fixed
**Files:** `backend/src/wheeloffish/api/routes/playlists.py`, `backend/tests/integration/test_playlists_api.py`
**Action:** Added `_require_cached_series` guard returning 422 when series is absent from owner-scoped cache. Seeded cached series in row-op integration tests; added `test_append_row_unknown_series_422`.

## Verification

- Backend: `pytest tests/integration/test_playlists_api.py` — 20 passed
- Frontend: `AddToPlaylistMenu.test.tsx`, `TwoPanePicker.test.tsx` — 10 passed

---

_Fixer: gsd-code-fixer (orchestrated)_
_Scope: critical_warning_
