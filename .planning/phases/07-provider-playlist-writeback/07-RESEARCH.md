# Phase 7: Provider playlist writeback — Research

**Date:** 2026-05-25  
**Status:** Ready for execution (spike conclusions locked for planner)

## Goal

Push WheelOfFish rebuild snapshots to native Plex/Jellyfin playlists so operators play nightly output in existing media clients (EXP-01, v0.1.0 gate).

## API findings

### Plex (primary — Wave 1)

| Operation | HTTP | Notes |
|-----------|------|-------|
| Server identity | `GET /identity` | Returns `machineIdentifier` for `library://` URIs when needed |
| Create playlist | `POST /playlists?type=video&title={title}&smart=0&uri={uri}` | Non-smart video playlist; can bootstrap with first item URI |
| List playlist items | `GET /playlists/{ratingKey}/items` | Item `ratingKey` values used for delete |
| Clear items | `DELETE /playlists/{playlistRatingKey}/items/{itemRatingKey}` | Per item; loop until empty |
| Add items | `PUT /playlists/{playlistRatingKey}/items?uri=library%3A%2F%2F{machineId}%2Fcom.plexapp.plugins.library%2Fitem%2F%252Flibrary%252Fmetadata%252F{episodeRatingKey}` | Add in rebuild order (sequential PUTs) |
| Rename | `PUT /playlists/{ratingKey}?title={urlencoded}` | Sync on WheelOfFish rename → `{name} [wof]` |
| Delete playlist | `DELETE /playlists/{ratingKey}` | On WheelOfFish delete |

**Identity mapping:** Snapshot `episode_id` composite native part is Plex **guid**. Resolve guid → **ratingKey** via existing `resolve_guid_to_rating_key()` in `plex/mappers.py` (`GET /library/all?guid=`).

**Replace strategy:** Clear all existing playlist items, then PUT items in snapshot order. Preserves stable `provider_playlist_id` (playlist ratingKey).

**Placement:** Server/account scoped — no library section picker (D-07).

### Jellyfin (Wave 2)

| Operation | HTTP | Notes |
|-----------|------|-------|
| Create | `POST /Playlists?name={name}&ids={id}&userId={userId}` | Can create with initial ids |
| List items | `GET /Playlists/{id}/Items?userId={userId}` | Returns `Id` (item) + entry metadata |
| Remove items | `DELETE /Playlists/{id}/Items?entryIds={playlistItemIds}` | Use **PlaylistItemId** / entry id, not media item id |
| Add items | `POST /Playlists/{id}/Items?ids={mediaItemIds}&userId={userId}` | Media item UUIDs |
| Update metadata | `POST /Playlists/{id}` body `UpdatePlaylistDto` | Rename |
| Delete | `DELETE /Playlists/{id}` | |

**Identity mapping:** Episode composite native part is Jellyfin item **Id** (UUID) — direct use, no guid lookup.

**Replace strategy:** Fetch entry ids → DELETE all → POST ids in order.

## Schema additions (migration 009)

**`playlists`**
- `provider_playlist_id: String(64) nullable` — Plex ratingKey or Jellyfin playlist UUID
- `provider_kind: String(16) nullable` — `plex` | `jellyfin` (denormalized from connection at link time)

**`rebuild_runs`**
- `writeback_status: String(16) nullable` — `succeeded` | `partial` | `failed` | `skipped`
- `writeback_error: Text nullable`
- `writeback_warnings: JSON nullable` — list of `{episode_id, reason}`
- `writeback_at: DateTime(tz) nullable`

## Module layout (recommended)

```
backend/src/wheeloffish/
  integrations/
    base.py              # extend MediaProvider protocol
    plex/playlists.py    # Plex playlist CRUD + item replace
    jellyfin/playlists.py
  core/
    provider_writeback.py   # push_snapshot(), rename_linked(), delete_linked()
    provider_playlist_urls.py  # open-in-client URL builders
```

## Open URL patterns

| Provider | Pattern |
|----------|---------|
| Plex (server web) | `{base_url}/web/index.html#!/playlist?key=/playlists/{ratingKey}` |
| Jellyfin | `{base_url}/web/index.html#!/details?id={playlistId}` |

Expose `provider_playlist_open_url` on list + detail API when linked.

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Guid → ratingKey lookup fails for some episodes | Partial writeback + warnings (D-13); skip episode |
| Plex rate limits on many PUTs | Sequential adds acceptable for N≤20 default; log duration |
| Jellyfin entryIds vs media ids confusion | Unit tests with fixture JSON from SDK docs |
| Writeback fails after good rebuild | Do not roll back snapshot (D-02); surface failed writeback status |
| Delete provider playlist fails | Log + still delete WheelOfFish row (best-effort D-11) |

## Test strategy

- **Unit:** httpx mock transport for Plex/Jellyfin playlist endpoints
- **Unit:** `provider_writeback.push_snapshot` with fake provider
- **Integration:** orchestrator rebuild → writeback fields populated (mock provider injected or respx)
- **Frontend:** vitest for WritebackStatus component

## References

- Plexopedia playlist add-item API
- python-plexapi playlist module (POST/PUT/DELETE paths)
- Jellyfin SDK `PlaylistsApiFp` (createPlaylist, addItemToPlaylist, removeItemFromPlaylist)

---

*Research complete — feeds 07-01 through 07-03 plans.*
