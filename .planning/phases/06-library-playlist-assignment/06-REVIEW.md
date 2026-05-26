---
phase: 06-library-playlist-assignment
reviewed: 2026-05-25T12:00:00Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - backend/src/wheeloffish/integrations/plex/mappers.py
  - backend/src/wheeloffish/integrations/jellyfin/mappers.py
  - backend/src/wheeloffish/api/schemas/playlists.py
  - backend/src/wheeloffish/api/routes/playlists.py
  - frontend/src/api/playlists.ts
  - frontend/src/api/types.ts
  - frontend/src/components/playlists/AddToPlaylistMenu.tsx
  - frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx
  - frontend/src/components/ui/context-menu.tsx
  - frontend/src/components/ui/dialog.tsx
  - frontend/src/components/ui/tabs.tsx
  - frontend/src/components/browse/SeriesCard.tsx
  - frontend/src/pages/BrowsePage.tsx
  - frontend/src/components/layout/AppShell.tsx
  - frontend/src/components/playlists/TwoPanePicker.tsx
  - frontend/src/components/playlists/RowSettingsSheet.tsx
  - frontend/src/components/playlists/PlaylistForm.tsx
  - frontend/src/pages/PlaylistFormPage.tsx
  - frontend/src/components/series/SeriesMetadataHero.tsx
  - frontend/src/pages/SeriesDetailPage.tsx
findings:
  critical: 2
  warning: 4
  info: 0
  total: 6
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-05-25T12:00:00Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Phase 6 delivers metadata mapper enrichment, incremental playlist row API endpoints, Library add-to-playlist UX, a two-pane playlist editor, and a series detail metadata hero. Authorization on row mutations correctly reuses the owner-scoped `_get_owned_playlist` gate, and Plex metadata mapping is defensively typed.

Two critical frontend correctness issues were found: row DELETE/PATCH URLs omit `encodeURIComponent` for composite Plex series IDs (a pattern the codebase already documents and applies elsewhere), and optimistic append rollback can desync edit-mode UI when a form save races with an in-flight append. Several warnings cover cache invalidation after quick-create, duplicate-append error handling, and backend race/validation gaps.

## Critical Issues

### CR-01: Row DELETE/PATCH URLs omit series ID encoding

**File:** `frontend/src/api/playlists.ts:144-156`
**Issue:** `removePlaylistRow` and `patchPlaylistRow` interpolate `seriesId` directly into the URL path. Real composite IDs contain percent-encoded Plex guids (e.g. `%3A%2F%2F` from `com.plexapp.agents.*://…`). Unencoded `%2F` sequences in path segments can be decoded as `/` by HTTP stacks, breaking routing. The project already documents this risk in `seriesId.ts` and encodes series IDs via `seriesApiPath()` / `encodeURIComponent()` for catalog API calls.
**Fix:**
```typescript
export async function removePlaylistRow(
  playlistId: string,
  seriesId: string,
): Promise<void> {
  await fetchJson<void>(
    `/playlists/${playlistId}/rows/${encodeURIComponent(seriesId)}`,
    { method: "DELETE" },
  )
}

export async function patchPlaylistRow(
  playlistId: string,
  seriesId: string,
  payload: PatchPlaylistRowPayload,
): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(
    `/playlists/${playlistId}/rows/${encodeURIComponent(seriesId)}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  )
}
```

### CR-02: Optimistic append rollback desyncs edit UI on 409 race

**File:** `frontend/src/components/playlists/TwoPanePicker.tsx:254-266`
**Issue:** In edit mode, `handleAdd` optimistically adds a row, then calls the append API. If the user clicks **Save playlist** before the append completes, `PlaylistForm` issues a PUT that already persists the row. When the append then returns 409 Conflict, the catch block rolls back to `previousRows`, removing the show from UI while it remains in the database. `PlaylistForm` local row state is not refreshed from query invalidation, so the desync persists until a full page reload.
**Fix:** Treat 409 as success (row already present), or disable form save while row mutations are pending, or refetch playlist detail on 409 instead of rolling back:
```typescript
import { ApiError } from "@/api/client"

// inside handleAdd catch block:
} catch (error) {
  if (error instanceof ApiError && error.status === 409) {
    return // row already persisted — keep optimistic state
  }
  onRowsChange(previousRows)
  toast.error("Failed to add show")
}
```

Also consider tracking `appendMutation.isPending || removeMutation.isPending || patchMutation.isPending` in `PlaylistForm` to disable the Save button during in-flight row ops.

## Warnings

### WR-01: Quick-create does not invalidate playlists query cache

**File:** `frontend/src/components/playlists/QuickCreatePlaylistDialog.tsx:42-45`
**Issue:** `QuickCreatePlaylistDialog` calls `createPlaylistWithSeries` directly instead of `useCreatePlaylist()`. Unlike append/remove/patch hooks, it never invalidates `["playlists"]`. After quick-create, the Add-to-playlist dropdown can omit the new playlist for up to the 30s `staleTime` window.
**Fix:** Use `useQueryClient()` and invalidate on success, or route through `useCreatePlaylist()`:
```typescript
const queryClient = useQueryClient()
// after successful create:
void queryClient.invalidateQueries({ queryKey: ["playlists"] })
```

### WR-02: Concurrent duplicate append can surface 500 instead of 409

**File:** `backend/src/wheeloffish/api/routes/playlists.py:328-351`
**Issue:** Duplicate detection is a pre-insert SELECT. Two concurrent POSTs with the same `series_id` can both pass the check; the second hits the `uq_playlist_series_row` unique constraint with no `IntegrityError` handler anywhere in the backend, likely returning an unhandled 500 instead of 409.
**Fix:** Wrap commit in try/except for `sqlalchemy.exc.IntegrityError` and map `(playlist_id, series_id)` violations to HTTP 409, or use database-level upsert/locking.

### WR-03: Add-to-playlist menu treats 409 as generic failure

**File:** `frontend/src/components/playlists/AddToPlaylistMenu.tsx:28-37`
**Issue:** `handleAppend` catches all errors with a generic toast. A duplicate append (409) should inform the user the show is already in the playlist rather than "Failed to add to playlist".
**Fix:**
```typescript
} catch (error) {
  if (error instanceof ApiError && error.status === 409) {
    toast.info(`Already in ${playlistName}`)
    return
  }
  toast.error("Failed to add to playlist")
}
```

### WR-04: Append endpoint does not verify series exists in user catalog

**File:** `backend/src/wheeloffish/api/routes/playlists.py:318-353`
**Issue:** `append_playlist_row` accepts any non-empty `series_id` string without checking `CachedSeries` ownership (unlike catalog routes that validate connection scope). Operators can add invalid or out-of-scope IDs; playlist rebuilds may fail silently or produce empty slots.
**Fix:** Before insert, query `CachedSeries` filtered by `app_user_id` and return 404/422 when the series is not in the user's cached catalog. (Same gap exists on create, but append is the new hot path for Library quick-add.)

---

_Reviewed: 2026-05-25T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
