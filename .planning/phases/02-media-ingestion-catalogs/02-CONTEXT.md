# Phase 2: Media ingestion & catalogs - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver live Plex and Jellyfin connectors behind a shared `MediaProvider` protocol, OAuth-based connection setup, normalized catalog DTOs, show-metadata caching for browse/add-to-playlist, and live episode + watch-state fetch with resume-pointer computation — exposed via REST APIs Phase 3 will consume.

**In scope:** INT-01 (connection registration + auth), INT-02 (library/series enumeration), INT-03 (resume pointer computation from live watch metadata).

**Out of scope:** Playlist CRUD and mathematics (Phase 4), scheduled rebuild jobs (Phase 5), SPA UI (Phase 3), multipart adjacency enforcement (Phase 4), long-lived episode/watch-state SQLite cache.

</domain>

<decisions>
## Implementation Decisions

### Provider parity & API surface
- **D-01:** **Full parity day one** — Plex and Jellyfin connectors equally complete before Phase 2 closes.
- **D-02:** **Pragmatic DTO parity** — identical DTO shapes across providers; nullable/optional fields where a backend lacks native data; document which fields each provider populates.
- **D-03:** **Testing strategy** — mocked unit tests + sanitized recorded API fixtures in CI; manual live-server UAT checklist against real Plex/Jellyfin instances.
- **D-04:** **Full catalog REST API in Phase 2** — connections, library/series browse, sync triggers, episode probe, and resume preview endpoints ready for Phase 3 SPA (not internal-only).

### Connection & credential model
- **D-05:** **At most one Plex + one Jellyfin** per install; neither required. **`WOF_ENABLED_PROVIDERS`** env (or admin setting) gates which provider types users may configure (`plex`, `jellyfin`, or both).
- **D-06:** **Split storage** — DB holds non-secret connection config (base URL, provider type, display name, SSL verify, Jellyfin user ID, Plex client identifier); vault stores auth tokens only via existing `media_server/{connection_id}/token` pattern.
- **D-07:** **Test-then-save** — on connection create, ping provider first; persist DB row + vault token in one transaction only on success; structured 422 errors (`unreachable`, `unauthorized`, `ssl_error`, `provider_disabled`, `wrong_type`); separate `POST /connections/{id}/test` for re-validation after token rotation.
- **D-08:** **Full OAuth early** — Plex OAuth and Jellyfin auth flow (username/password or API key generation) implemented in Phase 2; get OAuth working and out of the way before Phase 3 wizard.

### Install-level library scoping
- **D-09:** **Admin scopes available libraries at install/setup** — operator selects which TV libraries are in scope (env or admin config); users browse shows only from scoped libraries.

### Resume pointer semantics
- **D-10:** **Hybrid resume rule** — default to earliest unfinished episode; honor provider "next up" / On Deck when it is ahead of earliest unfinished (user deliberately skipped).
- **D-11:** **Watch-state thresholds** — `< 5%` watched and not provider-marked-played = unwatched; `5–95%` or provider-marked-played = partial; `≥ 95%` = complete. Map Plex `viewCount` / Jellyfin `Played` as provider override.
- **D-12:** **Specials ordering** — main season episodes first; specials for a season inserted after that season's finale in provider order.
- **D-13:** **Per-app-user watch state** — each Wheel of Fish TV user links their own media-server account via OAuth; resume cursor keyed per `(app_user, media_user, series)`; each user has own watch history, settings, and playlists.

### Catalog cache & sync strategy
- **D-14:** **Show metadata cache only** — persist libraries + series metadata in SQLite for browse/add-to-playlist; **do not cache** episode lists or watch state long-term (stale between daily rebuilds as users watch shows).
- **D-15:** **Episode + watch data fetched fresh** at playlist rebuild time (Phase 4/5 consumers); Phase 2 implements live fetch on demand for UAT/resume preview only.
- **D-16:** **Show-metadata sync triggers** — OAuth connect, user login/session start, and manual "Refresh library"; no nightly show-metadata background sync in Phase 2.
- **D-17:** **Lazy chunked sync** — server-side paging + search (`?page=&limit=&q=`); background sync in chunks so login is not blocked on full library pull.
- **D-18:** **Non-blocking login UX** — login returns immediately; show stale cached data with "Updating library…" banner while background sync runs; first OAuth connect shows empty until first chunk completes.

### Provider interface & DTO shape
- **D-19:** **Composite stable IDs** — `{connection_id}:{provider}:{native_id}` using stable provider GUIDs where available (Plex GUID, Jellyfin item ID); resolve ephemeral ratingKeys at API-call time internally.
- **D-20:** **Two-layer DTOs** — cached browse layer (`Library`, `Series`); ephemeral rebuild layer (`Episode` with embedded watch snapshot fields fetched live, not persisted).
- **D-21:** **Optional multipart fields on Episode** — include `part_index`, `multipart_group_id`, and/or link refs **only when mapped from native provider API fields**; nullable otherwise; no heuristic multipart detection in Phase 2.
- **D-22:** **Phase 2 API scope** — ship series browse + sync; live `GET …/series/{id}/episodes` (not cached); `GET …/series/{id}/resume` returning domain-computed `ResumeCursor` (proves INT-03); `ResumeService` reusable by Phase 4 playlist builder.

### Claude's Discretion
- Exact OAuth redirect/callback URLs, Plex GUID vs ratingKey resolution internals, sync chunk size, paging defaults, structured error payload shape, and OpenAPI route naming — as long as decisions above and Phase 2 ROADMAP success criteria are met.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Product scope, Plex/Jellyfin resume semantics, self-host constraints
- `.planning/REQUIREMENTS.md` — INT-01, INT-02, INT-03 traceability
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria
- `.planning/research/SUMMARY.md` — ResumeCursor normalization, multipart pitfalls, API rate-limit notes

### Prior phase context
- `.planning/phases/01-foundations-packaging/01-CONTEXT.md` — SQLite, secrets vault, integrations stub layout, monorepo structure

### Existing code (Phase 1 foundations)
- `backend/src/wheeloffish/core/secrets.py` — Vault CRUD + `store_media_token` helpers
- `backend/src/wheeloffish/core/namespaces.py` — `MEDIA_SERVER_NS` key scheme
- `backend/src/wheeloffish/integrations/plex.py` — Plex client stub to implement
- `backend/src/wheeloffish/integrations/jellyfin.py` — Jellyfin client stub to implement

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SecretsVault` with Fernet encryption and `store_media_token(connection_id, token)` — extend for OAuth token refresh storage
- `MEDIA_SERVER_NS` / `media_server_token_key()` namespace constants — add connection-scoped secret keys as needed
- `PlexClient` / `JellyfinClient` stubs with `connect`, `list_libraries`, `list_shows` method signatures — expand to full `MediaProvider` protocol
- FastAPI app + health route + Alembic migrations + pytest CI — extend with connections/catalog routes and new migrations

### Established Patterns
- Layered `backend/src/wheeloffish/` package: `api/`, `core/`, `db/`, `integrations/`
- Config via `.env` + `compose.yml` environment defaults; secrets never in images
- Phase 1 CI: Ruff + pytest + docker compose smoke — add fixture-based integration tests

### Integration Points
- New `connections` DB table + Alembic migration alongside existing `secrets` table
- New `cached_series` (or equivalent) table for show metadata; no episode cache table in Phase 2
- `integrations/` implements `MediaProvider` protocol; domain service in `core/` computes `ResumeCursor`
- REST routes under `/api/` for Phase 3 SPA consumption; OAuth callback routes for Plex/Jellyfin

</code_context>

<specifics>
## Specific Ideas

- **OAuth early:** User wants OAuth working in Phase 2 so Phase 3 wizard is credential-paste-free.
- **Fresh on login:** Show list should refresh when user logs in since new shows may be added to Plex/Jellyfin anytime between visits.
- **No episode cache:** User explicitly does not want episode/watch data cached — fetch fresh at scheduled playlist rebuild because watch progress changes between refreshes.
- **Per-user isolation:** Each Plex/Jellyfin user gets their own watch history, settings, and playlists within the app.
- **Install scoping:** Operator configures which libraries are available — not a runtime user pick from all libraries.

</specifics>

<deferred>
## Deferred Ideas

- **Multipart adjacency rules** — Phase 4 playlist mathematics; Phase 2 only maps native multipart fields when providers expose them
- **Heuristic multipart detection** (title patterns, SxxExx inference) — Phase 4 when provider metadata insufficient
- **Nightly show-metadata background sync** — deferred; login + manual refresh sufficient for ≤5 casual users
- **Episode SQLite cache** — explicitly rejected; live fetch at rebuild only
- **Playlist CRUD, rebuild scheduler, SPA** — Phases 3–5 per roadmap

</deferred>

---

*Phase: 2-Media ingestion & catalogs*
*Context gathered: 2026-05-25*
