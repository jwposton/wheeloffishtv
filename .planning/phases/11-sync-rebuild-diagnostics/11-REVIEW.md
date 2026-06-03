---
phase: 11-sync-rebuild-diagnostics
reviewed: 2026-06-02T12:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - backend/src/wheeloffish/api/schemas/playlists.py
  - backend/src/wheeloffish/core/rebuild_diagnostics.py
  - backend/src/wheeloffish/api/routes/playlists.py
  - frontend/src/api/playlists.ts
  - frontend/src/lib/rebuildDiagnostics.ts
  - frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx
  - frontend/src/components/playlists/RebuildBanner.tsx
  - frontend/src/components/playlists/WritebackStatus.tsx
  - frontend/src/pages/PlaylistDetailPage.tsx
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-06-02T12:00:00Z  
**Depth:** standard  
**Files Reviewed:** 9  
**Status:** issues_found

## Summary

Phase 11 adds a pure `build_rebuild_diagnostics` resolver, embeds diagnostics on `last_rebuild` in playlist detail GET, and surfaces them through a scrollable modal with tested action dispatch. Contracts and XSS posture are sound (React text nodes, server-built provider URLs). Three warnings remain around diagnostic completeness when triggers fire but structured rows are empty, show-level reason fallback copy, and SPA navigation from modal actions.

## Warnings

### WR-01: Failed rebuild with empty `error_message` omits modal rebuild detail

**File:** `backend/src/wheeloffish/core/rebuild_diagnostics.py:274-276`  
**Issue:** `rebuild_error` is only populated when `run.status == "failed" and run.error_message`, but `_resolve_rebuild_error` already supports a catalog fallback when `error_message` is falsy. Phase 11 removed the inline failed `error_message` paragraph from `RebuildBanner` (D-07), so a failed run with a null/empty message shows “View details” via `shouldShowDiagnostics` but the modal’s Rebuild section stays empty.  
**Fix:** Gate on status only and always resolve the row:

```python
rebuild_error: DiagnosticIssueRow | None = None
if run.status == "failed":
    rebuild_error = _resolve_rebuild_error(run, ctx)
```

Add a unit test for `status="failed", error_message=None` asserting `rebuild_error.reason_text` uses the catalog default.

### WR-02: Writeback failed with no per-episode warnings yields empty structured diagnostics

**File:** `backend/src/wheeloffish/core/rebuild_diagnostics.py:264-272`  
**Issue:** Whole-playlist writeback failures set `writeback_status="failed"` and `writeback_error` (orchestrator `WritebackResult(status="failed", error=...)`) but `build_rebuild_diagnostics` only reads `writeback_warnings` with `episode_id`. D-02 still shows “View details” for writeback failed, yet the modal can hit the empty state while the banner one-liner carries the only error text.  
**Fix:** When `run.writeback_status == "failed"` and `run.writeback_error`, append a synthetic `episode_issues` (or dedicated) row using `writeback_failed` from `REASON_CATALOG` with `reason_text` from `run.writeback_error`, or add a `writeback_error` field to `RebuildDiagnostics` and render it in the modal Episode sync / Rebuild section.

### WR-03: Unknown fetch-warning reasons map to writeback copy in show issues

**File:** `backend/src/wheeloffish/core/rebuild_diagnostics.py:179-183`  
**Issue:** `_resolve_show_issue` falls back to `writeback_warning` when `raw_reason` is not in `REASON_CATALOG`, producing episode-sync-oriented copy under the “Shows skipped” section. Orchestrator today only emits known fetch codes, but any future or legacy `fetch_warnings` entry with an unknown reason will mislead operators.  
**Fix:** Use a fetch-specific fallback (e.g. `fetch_failure`) or log and map to a dedicated `unknown_fetch` catalog entry:

```python
reason_code = raw_reason if raw_reason in REASON_CATALOG else "fetch_failure"
```

## Info

### IN-01: Empty placeholder paragraphs in RebuildBanner

**File:** `frontend/src/components/playlists/RebuildBanner.tsx:57-58,85-86`  
**Issue:** Two `<p className="text-sm text-muted-foreground"></p>` elements have no content—likely leftovers from removing inline copy. They add noise in the layout/DOM without purpose.  
**Fix:** Remove the empty `<p>` tags.

### IN-02: Modal `open_series` uses full page navigation on detail page

**File:** `frontend/src/components/playlists/RebuildBanner.tsx:112`  
**Issue:** `actionContext` omits `navigate`, so `runDiagnosticAction` falls back to `window.location.assign` for series links. Other playlist surfaces (`PlaylistMembersPanel`, `TwoPanePicker`) use React Router `navigate`, avoiding a full reload.  
**Fix:** Pass `navigate` from `PlaylistDetailPage` through `RebuildBanner` into `actionContext` (same pattern as `rebuildDiagnostics.test.ts`).

---

_Reviewed: 2026-06-02T12:00:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
