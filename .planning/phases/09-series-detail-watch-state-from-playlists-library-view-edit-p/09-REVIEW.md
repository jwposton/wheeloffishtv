---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - frontend/src/pages/SeriesDetailPage.tsx
  - frontend/src/pages/SeriesDetailPage.watch-state.test.tsx
  - frontend/src/hooks/useSeriesEpisodes.ts
  - frontend/src/components/ui/watch-state-progress.tsx
  - frontend/src/components/playlists/PlaylistRowMenuItems.tsx
  - frontend/src/components/playlists/TwoPanePicker.tsx
  - frontend/src/components/playlists/PlaylistMemberTile.tsx
  - frontend/src/components/playlists/PlaylistMembersPanel.tsx
  - frontend/src/App.tsx
  - backend/src/wheeloffish/api/routes/catalog.py
  - backend/src/wheeloffish/api/schemas/catalog.py
  - backend/tests/api/test_catalog_watch_mutations.py
  - backend/tests/unit/test_watch_writeback_services.py
  - backend/src/wheeloffish/integrations/plex/client.py
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: clean
fixes_applied: [CR-01, WR-01, WR-02, WR-03, WR-04]
---

# Phase 9: Code Review Report

**Reviewed:** 2026-06-02  
**Depth:** standard  
**Files Reviewed:** 14  
**Status:** clean (fixes applied 2026-06-02)

## Summary

Phase 9 watch-state work reviewed; Critical and Warning findings were remediated. Remaining Info item (IN-01 live-region on progress banner) is optional accessibility polish.

## Critical Issues

### CR-01: Episode list and watch controls hidden when resume does not need a title

**File:** `frontend/src/pages/SeriesDetailPage.tsx:97-104`, `276-359`  
**Issue:** `useSeriesEpisodes` is only enabled when `needsEpisodeTitle` is true (`resumeQuery.data?.episode_id && !resumeQuery.data.series_complete`). When a show has no on-deck episode or is marked series-complete, the episodes query never runs, so `episodesQuery.data` stays empty and the entire “Episodes by season” section (badges, mark watched/unwatched, season/series bulk actions) is not rendered. That contradicts the Phase 9 UI contract, which requires episode grouping and bulk scope controls on the shared detail route for library and playlist entry points.

**Fix:**
```tsx
// Always load episodes on series detail; use resume only to pick matchedEpisode title.
const episodesQuery = useSeriesEpisodes(connectionId, seriesId, authReady)
```

If resume-only fetch is still desired for performance, split concerns: keep a lightweight resume-driven fetch for `matchedEpisode`, but pass `true` (or `authReady`) for the watch-state episode list.

## Warnings

### WR-01: Optimistic episode update not rolled back on API `failed` responses

**File:** `frontend/src/hooks/useSeriesEpisodes.ts:181-208`  
**Issue:** Episode mutations optimistically set `provider_marked_played` / `percent_watched` before `postWatchMutation`. Rollback only runs in the `catch` branch (network/HTTP errors). When the API returns HTTP 200 with `status: "failed"` or `"partial"`, the optimistic cache remains until invalidation/refetch completes, violating the UI spec’s “optimistic updates with rollback on failure” pattern and briefly showing incorrect badges/button labels.

**Fix:**
```tsx
const result = await postWatchMutation(connectionId!, { /* ... */ })
if (result.status !== "succeeded") {
  queryClient.setQueryData(
    seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
    prior,
  )
}
setWatchMutationProgressResult(result, "episode")
await reconcileAfterMutation()
return result
```

### WR-02: Playlist `from` back-link allows protocol-relative open redirect

**File:** `frontend/src/pages/SeriesDetailPage.tsx:89-90`  
**Issue:** `backHref` accepts any `from` value that `startsWith("/")`. Values like `//evil.example/phish` satisfy that check and can be passed to `<Link to={backHref}>`, enabling an off-site navigation if a crafted playlist URL is shared or bookmarked.

**Fix:**
```tsx
function isSafeInternalPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//")
}

const backHref =
  isPlaylistOrigin && from && isSafeInternalPath(from) ? from : "/browse"
```

### WR-03: Provider unsupported-scope caveat copy not implemented

**File:** `frontend/src/pages/SeriesDetailPage.tsx` (episode section)  
**Issue:** `09-UI-SPEC.md` requires copy such as “This provider does not support this bulk update scope” when a bulk scope is unavailable. No such messaging exists in the detail UI or mutation handlers; failures only surface via generic toasts.

**Fix:** Detect unsupported provider/scope (from API `error_code` or a capability flag) and render the spec copy near season/series controls or disable those buttons with an explanatory `aria-describedby` note.

### WR-04: Global watch-mutation banner timer can clear a newer mutation’s state

**File:** `frontend/src/hooks/useSeriesEpisodes.ts:99-101`  
**Issue:** `setWatchMutationProgressResult` schedules `setTimeout(..., 3000)` to reset banner state without tracking mutation generation. A second mutation finishing after the first can have its “succeeded/partial/failed” message cleared early by the first mutation’s timer.

**Fix:** Store a monotonic `progressEpoch` ref; only clear when `epoch === currentEpoch` inside the timeout callback, or `clearTimeout` previous timers when starting a new mutation.

## Info

### IN-01: Progress banner lacks live-region semantics for screen readers

**File:** `frontend/src/components/ui/watch-state-progress.tsx:24-31`  
**Issue:** Running/completed mutation text updates visually but is not announced to assistive technology; the UI spec calls for accessible feedback during long bulk updates.

**Fix:** Add `role="status"` and `aria-live="polite"` on the banner container (and `aria-busy` while `status === "running"`).

---

_Reviewed: 2026-06-02_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
