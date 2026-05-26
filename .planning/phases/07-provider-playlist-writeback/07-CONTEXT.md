# Phase 7: Provider playlist writeback — Context

**Discussed:** 2026-05-25  
**Planned:** 2026-05-25  
**Status:** Ready for execution  
**Release gate:** v0.1.0

<domain>
## Phase Boundary

Close the MVP delivery loop: WheelOfFish already **authors** and **rebuilds** playlists internally (Phases 4–6). Phase 7 **pushes** each rebuild snapshot to a **native Plex or Jellyfin playlist** so operators consume nightly output in their existing media clients.

**In scope:**
- Extend `MediaProvider` with playlist writeback operations (create if missing, replace items on rebuild, rename, delete)
- Hook writeback into `rebuild_playlist` orchestrator **after** snapshot persist (success + partial paths)
- Persist provider playlist link on WheelOfFish `Playlist` (`provider_playlist_id`, `provider_playlist_provider` — exact columns in planner)
- Record writeback outcome on `RebuildRun` (status, error, warnings, timestamp)
- SPA: writeback status badge + **open in Plex/Jellyfin** link when URL derivable
- **Plex-first** for v0.1.0; **Jellyfin follow-up wave (07-02)** within phase if API straightforward before tag, else v0.1.1 patch
- Rename WheelOfFish playlist → rename linked provider playlist (with `[wof]` suffix)
- Delete WheelOfFish playlist → delete linked provider playlist
- Manual rebuild retries writeback; nightly job uses same path

**Out of scope:**
- Library picker for Plex playlist placement (playlists are server/account scoped — not library scoped)
- M3U/JSON file export fallback (defer unless API research blocks both providers)
- Bi-directional sync (edits in Plex/Jellyfin app do not mutate WheelOfFish membership)
- Multi-server fan-in (one WheelOfFish playlist → one connection’s provider playlist)
- UX polish pass (Phase 8)
- Genre/metadata Jellyfin parity (Phase 8 unless trivial during writeback work)

</domain>

<decisions>
## Implementation Decisions

### Release & sequencing
- **D-01:** **v0.1.0 tags after Phase 7 validation** — functional MVP complete; Phase 8 polish targets v0.2.0.
- **D-02:** Writeback failure **does not roll back** persisted rebuild snapshot (same isolation principle as fetch partials).
- **D-03:** **Plex ships in Wave 1**; Jellyfin in **Wave 2 (07-02)** if quick, else patch release before blocking v0.1.0 only if user-facing Jellyfin install is a launch requirement (default: attempt in-phase).

### Provider linking
- **D-04:** One WheelOfFish playlist maps to **at most one** provider playlist on the connection inferred from its series rows (existing orchestrator connection resolution).
- **D-05:** **Create-on-first-successful-rebuild** if no `provider_playlist_id` stored (not on playlist save).
- **D-06:** Subsequent rebuilds **replace entire item list** with snapshot ordering (full refresh semantics).
- **D-07:** Plex playlists are **server/account scoped** — no target library section field or UI for v0.1.0.

### Naming & lifecycle
- **D-08:** Provider display name = **`{WheelOfFish playlist name} [wof]`** at creation.
- **D-09:** **Rename sync:** PATCH WheelOfFish playlist name → update provider playlist title to `{new_name} [wof]`.
- **D-10:** **Ownership source of truth** = stored `provider_playlist_id` on WheelOfFish `Playlist`, not display name (handles duplicate human-readable names).
- **D-11:** **Delete sync:** DELETE WheelOfFish playlist → delete linked provider playlist (best-effort; log failure if provider delete fails).

### Identity mapping & partial behavior
- **D-12:** Snapshot `episode_id` values are composite IDs; writeback resolves to provider-native keys via existing mappers / rating-key lookup.
- **D-13:** Episodes that fail ID resolution are **skipped with warning**; **partial writeback allowed** if at least one episode maps (align with partial rebuild status).
- **D-14:** If zero episodes map, writeback status = **failed**; prior provider playlist contents unchanged for that run.

### Observability & UI
- **D-15:** `RebuildRun` gains writeback fields (`writeback_status`, `writeback_error`, `writeback_warnings`, `writeback_at`) — exact schema in planner.
- **D-16:** UI shows writeback state **separate from build state** on playlist list + detail.
- **D-17:** When connection base URL + provider playlist ID allow, show **open in Plex/Jellyfin** deep link alongside status.

### API research spikes (planner must verify)
- **D-18:** Plex: server-level playlist create + replace items + rename + delete with user token.
- **D-19:** Jellyfin: playlist CRUD + replace items with user AccessToken.

</decisions>

<architecture>
## Integration points

```
rebuild_playlist()
  → fetch inputs
  → PlaylistBuilder.build()
  → persist snapshot + RebuildRun (existing)
  → provider_writeback.push(...)     ← after snapshot commit
  → update RebuildRun writeback fields

PATCH /playlists/{id} (rename)
  → update provider playlist title if linked

DELETE /playlists/{id}
  → delete provider playlist if linked
```

Existing hook: `backend/src/wheeloffish/core/orchestrator.py` after snapshot commit (~line 184).

`MediaProvider` today (`integrations/base.py`) is read-only — add write methods without breaking Plex/Jellyfin clients.

</architecture>

<planning_hints>
## Suggested plan waves (planner discretion)

**Wave 1 — Plex writeback core**
- Schema: `playlists.provider_playlist_id`, rebuild run writeback columns
- `PlexProvider`: create / replace items / rename / delete playlist
- Orchestrator hook + episode ID resolution
- Integration tests against mocked Plex API

**Wave 2 — Jellyfin parity (if API straightforward)**
- Mirror operations on Jellyfin client
- Provider-agnostic writeback facade

**Wave 3 — Lifecycle + UI**
- Rename/delete hooks in playlist routes
- SPA status badge + open-in-provider link
- UAT checklist + validation doc

</planning_hints>

---

*Discuss complete 2026-05-25. Plans: 07-01, 07-02, 07-03. Next: `/gsd-execute-phase 7`.*
