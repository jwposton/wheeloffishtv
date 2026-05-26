# Phase 7: Provider playlist writeback — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 07-provider-playlist-writeback
**Areas discussed:** Plex playlist placement, naming, lifecycle, Jellyfin timing, partial writeback, create timing, UI surfacing

---

## 1. Plex playlist placement

| Option | Description | Selected |
|--------|-------------|----------|
| First TV library | Default to first scoped TV library | |
| Row library | Infer from first series row | |
| User picker | Settings UI for target library | |
| **Server-level** | **No library — playlists live on Plex account/server** | ✓ |

**User's choice:** Plex playlists are account/server scoped, not library scoped — no library picker needed for v0.1.0.

---

## 2. Rename sync

| Option | Description | Selected |
|--------|-------------|----------|
| Sync rename | Provider playlist renamed to match WheelOfFish | ✓ |
| Keep original | Name frozen at creation | |
| Suffix-only once | Fixed suffix at create; never rename | |

**User's choice:** Keep provider playlist name in sync when WheelOfFish playlist is renamed (with `[wof]` suffix convention — see §3).

---

## 3. Provider playlist naming

| Option | Description | Selected |
|--------|-------------|----------|
| Exact name | Same as WheelOfFish name | |
| **Suffix `[wof]`** | **`{name} [wof]`** at create + on rename | ✓ (custom) |
| Prefix | `WheelOfFish: {name}` | |

**User's choice:** Display name `{WheelOfFish playlist name} [wof]`. **Internal link** via stored `provider_playlist_id` on WheelOfFish `Playlist` is source of truth for ownership — suffix helps operators spot managed playlists when display names collide.

---

## 4. Delete behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Orphan | Leave provider playlist | |
| **Delete provider** | **Remove linked Plex/Jellyfin playlist** | ✓ |
| Confirm prompt | Checkbox at delete time | |

**User's choice:** Delete provider playlist when WheelOfFish playlist is deleted.

---

## 5. Jellyfin timing

| Option | Description | Selected |
|--------|-------------|----------|
| Same phase | Both providers before v0.1.0 | |
| **Plex first** | **Plex for v0.1.0; Jellyfin 07-02 wave if quick else v0.1.1** | ✓ |
| Defer to polish | Jellyfin with Phase 8 | |

**User's choice:** Plex-first; attempt Jellyfin in follow-up wave within Phase 7 before tag if straightforward.

---

## 6. Partial episode mapping during writeback

| Option | Description | Selected |
|--------|-------------|----------|
| **Partial OK** | **Push mappable episodes; record warnings** | ✓ |
| All-or-nothing | Abort entire writeback on any miss | |
| Skip run | Leave previous provider list unchanged | |

**User's choice:** Align with partial rebuild semantics — push what maps, surface warnings.

---

## 7. Create timing

| Option | Description | Selected |
|--------|-------------|----------|
| **First rebuild** | **Create provider playlist on first successful rebuild** | ✓ |
| On save | Create empty playlist when WheelOfFish playlist saved | |

**User's choice:** First successful rebuild creates the link.

---

## 8. UI surfacing (v0.1.0)

| Option | Description | Selected |
|--------|-------------|----------|
| Badge only | Status line on list + detail | |
| **Badge + link** | **Status + open-in-Plex/Jellyfin when URL derivable** | ✓ |
| Minimal | Fold into rebuild badge only | |

**User's choice:** Separate writeback status with deep link to provider client when possible.

---

## Confirmed from prior CONTEXT (unchanged)

- v0.1.0 gate after Phase 7 validation; Phase 8 = polish / v0.2.0
- Writeback failure does not roll back persisted rebuild snapshot
- One WheelOfFish playlist → one provider playlist on inferred connection
- Full replace item list on each rebuild
- No bi-directional sync; no M3U fallback in v0.1.0
