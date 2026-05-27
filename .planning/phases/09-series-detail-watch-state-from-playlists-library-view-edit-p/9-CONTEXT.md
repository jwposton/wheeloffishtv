# Phase 9: Series detail & watch state from playlists — Context

**Discussed:** 2026-05-27  
**Planned:** TBD  
**Status:** Pre-plan — provider watch-write API assumptions **locked** (see below)  
**Depends on:** Phase 8 (per ROADMAP)

<domain>
## Phase boundary (summary)

See `.planning/ROADMAP.md` — Phase 9 for full goals: Library / view-playlist / edit-playlist **parity** for series detail; edit-pane **View series** + session ordering for new adds; episode list by season with **watched / on-deck / unwatched**; **context actions** to change watch state at episode, season, or series scope; **Specials (S0) after seasons 1…N** by default.

This document **locks** cross-provider behavior for **writing** watched/unwatched state so implementation agents do not need to rediscover API support.

</domain>

<decisions>
## Provider API — watched / unplayed (locked for planning)

### Plex

- **D-01:** Plex Media Server supports marking items **watched** and **unwatched** via the established endpoints (GET):
  - Watched: `GET /:/scrobble?identifier=com.plexapp.plugins.library&key={ratingKey}`
  - Unwatched: `GET /:/unscrobble?identifier=com.plexapp.plugins.library&key={ratingKey}`
- **D-02:** These endpoints use the **numeric `ratingKey`** for the target metadata item (episode, and commonly season/show containers). Reference: [Plexopedia — Mark item as watched](https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/).
- **D-03:** Documented behavior includes using a **show**-level key to mark the **entire series**. **Season**-level bulk is **assumed** to work like other Plex clients (same `key` pattern) but MUST be verified once against a real library in UAT (`T-09-01`).
- **D-04:** Plex’s HTTP API here is **not** formally published as a stable public contract; treat as supported-in-practice and add integration tests. Failures → surface to user (401, etc.) without corrupting local DB beyond intentional cache refresh.

### Jellyfin

- **D-05:** Jellyfin supports **played** / **unplayed** per user via Playstate API ([`PlaystateController.cs`](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs)):
  - `POST /UserPlayedItems/{itemId}` — mark played (optional `userId`, `datePlayed` query params)
  - `DELETE /UserPlayedItems/{itemId}` — mark unplayed
- **D-06:** For **folder** items (e.g. **Series**, **Season**), server-side `Folder.MarkPlayed` / `MarkUnplayed` walks **descendants** and updates episodes ([`Folder.cs`](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Controller/Entities/Folder.cs)). Therefore **one request** with the **series or season** `itemId` is sufficient for “mark whole show / whole season” without N episode round-trips, provided the id is the correct library item type.
- **D-07:** Episode writes use the same **native item UUID** already present in WheelOfFish composite Jellyfin episode ids.

### WheelOfFish implementation (both providers)

- **D-08:** **Feature is viable** on both Plex and Jellyfin for episode-level and bulk season/series actions; **no plan change required** solely for “API does not exist.”
- **D-09:** **Plex episode identity:** catalog/episodes often expose **guid** in composites; scrobble requires **ratingKey**. Reuse or extend the same resolution pattern as playlist writeback (`resolve_episode_rating_key` and related helpers in `integrations/plex/`).
- **D-10:** **Jellyfin episode identity:** use item id from composite id directly for `UserPlayedItems` routes.
- **D-11:** After successful provider mutation, **refresh UX state** via existing mechanisms (e.g. trigger catalog sync, targeted refetch, or optimistic update + reconcile — **planner chooses**; must not leave UI permanently stale vs provider).
- **D-12:** **On-deck / next** remains **derived** from provider-reported progress + existing mappers (`viewOffset` / `UserData` / `ResumeService` patterns); there is no separate “set on-deck” write API required for Phase 9.

### Error handling (defaults)

- **D-13:** Partial bulk failure (unlikely on Jellyfin folder path; possible if Plex season key rejected): report error, avoid claiming success for unaffected episodes.
- **D-14:** Respect provider **403/401** — clear copy to re-auth if session invalid (align with existing catalog sync behavior).

</decisions>

<architecture>
## Integration sketch (for planners)

```
SPA series detail / context menus
  → REST routes (new or extended under catalog or connections)
    → MediaProvider abstraction (new methods: mark_watched / mark_unwatched at episode | season | series scope)
      → Plex: scrobble / unscrobble + ratingKey resolution
      → Jellyfin: POST / DELETE UserPlayedItems/{itemId} (itemId = episode | season | series)
  → post-mutation: cache / sync / client invalidation (per D-11)
```

Existing read path reference: `integrations/plex/mappers.py` (`viewCount`, `viewOffset`, …), `integrations/jellyfin/mappers.py` (`UserData.Played`, `PlaybackPositionTicks`, …).

</architecture>

<verification>
## Mandatory verification

| Id | Check |
|----|--------|
| T-09-01 | Confirm `:/scrobble` + `:/unscrobble` with a **season** `ratingKey` updates all episodes under that season on a test server. |
| T-09-02 | Confirm guid-based episode composite → ratingKey → scrobble round-trip matches Plex Web. |
| T-09-03 | Confirm `POST /UserPlayedItems/{seasonId}` marks all episodes in that season; `DELETE` clears played. |
| T-09-04 | Same for series id (Jellyfin). |

</verification>

<references>
## External references (read-only)

- Plex watched/unwatched: [Plexopedia — Mark item as watched](https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/)
- Jellyfin playstate: [PlaystateController.cs](https://github.com/jellyfin/jellyfin/blob/master/Jellyfin.Api/Controllers/PlaystateController.cs)
- Jellyfin folder recursion: [Folder.cs](https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Controller/Entities/Folder.cs)

</references>
