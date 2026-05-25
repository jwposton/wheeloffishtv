# Phase 2: Media ingestion & catalogs - Research

**Researched:** 2026-05-25
**Domain:** Plex/Jellyfin connectors, OAuth/auth, normalized catalog DTOs, show-metadata cache, live episode/watch fetch, ResumeCursor computation
**Confidence:** HIGH (Plex OAuth + API), MEDIUM-HIGH (Jellyfin auth + TV endpoints), HIGH (internal architecture aligned to CONTEXT)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full Plex + Jellyfin parity day one — both connectors equally complete before Phase 2 closes
- **D-02:** Pragmatic DTO parity — identical shapes; nullable fields where a backend lacks native data; document per-provider population
- **D-03:** Mocked unit tests + sanitized recorded API fixtures in CI; manual live-server UAT checklist
- **D-04:** Full catalog REST API in Phase 2 — connections, browse, sync triggers, episode probe, resume preview (not internal-only)
- **D-05:** At most one Plex + one Jellyfin per install; neither required; `WOF_ENABLED_PROVIDERS` gates which types may be configured
- **D-06:** Split storage — DB holds non-secret connection config; vault stores auth tokens via `media_server/{connection_id}/token` pattern (extend for per-user tokens per D-13)
- **D-07:** Test-then-save on connection create; structured 422 errors (`unreachable`, `unauthorized`, `ssl_error`, `provider_disabled`, `wrong_type`); separate `POST /connections/{id}/test`
- **D-08:** Full OAuth early — Plex PIN OAuth; Jellyfin username/password auth (or API key for admin server setup only — user tokens for watch state)
- **D-09:** Admin scopes available TV libraries at install/setup (env or admin config); users browse only scoped libraries
- **D-10:** Hybrid resume rule — default earliest unfinished; honor provider On Deck / Next Up when ahead of earliest unfinished
- **D-11:** Watch thresholds — `<5%` unwatched; `5–95%` or provider-marked-played = partial; `≥95%` complete; Plex `viewCount>0` / Jellyfin `Played` as override
- **D-12:** Specials ordering — main season episodes first; specials for a season after that season's finale in provider order
- **D-13:** Per-app-user watch state — each WOF user links own media account; resume keyed `(app_user, media_user, series)`; extend vault keys per user link
- **D-14:** Show metadata cache only — libraries + series in SQLite; no long-lived episode/watch cache
- **D-15:** Episode + watch data fetched live on demand (Phase 2: UAT/resume preview; Phase 4/5: rebuild consumers)
- **D-16:** Show-metadata sync triggers — OAuth connect, user login/session start, manual refresh; no nightly background sync in Phase 2
- **D-17:** Lazy chunked sync — server-side paging + search (`?page=&limit=&q=`); background chunks so login is not blocked
- **D-18:** Non-blocking login UX — return immediately; stale cache + "Updating library…" banner; first OAuth connect empty until first chunk
- **D-19:** Composite stable IDs — `{connection_id}:{provider}:{native_id}` using Plex GUID / Jellyfin item ID; resolve ephemeral Plex ratingKeys internally
- **D-20:** Two-layer DTOs — cached browse (`Library`, `Series`); ephemeral rebuild (`Episode` with embedded watch snapshot, not persisted)
- **D-21:** Optional multipart fields on `Episode` only when mapped from native API; no heuristic detection in Phase 2
- **D-22:** Phase 2 API scope — series browse + sync; live episodes endpoint; resume endpoint returning domain `ResumeCursor`; reusable `ResumeService`

### Claude's Discretion
- OAuth redirect/callback URLs, Plex GUID vs ratingKey resolution internals, sync chunk size, paging defaults, structured error payload shape, OpenAPI route naming

### Deferred Ideas (OUT OF SCOPE)
- Episode SQLite cache, nightly show-metadata sync, multipart adjacency/heuristics (Phase 4), playlist CRUD (Phase 4), SPA (Phase 3)
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Connection CRUD + test-then-save | API routes (`api/routes/connections.py`) | `core/connections.py` service | HTTP validation; business rules in core |
| Plex PIN OAuth | API routes (`api/routes/oauth_plex.py`) | `integrations/plex/auth.py` | Browser redirect + callback; httpx to plex.tv |
| Jellyfin username auth | API routes (`api/routes/oauth_jellyfin.py`) | `integrations/jellyfin/auth.py` | No OAuth spec; credential POST → token |
| Token storage | `core/secrets.py` (existing vault) | DB `user_media_links` row | Fernet encrypt; keys namespaced per connection + app user |
| MediaProvider protocol | `integrations/base.py` | `integrations/plex/`, `integrations/jellyfin/` | Single interface; provider-specific httpx clients |
| Show metadata cache | DB models + `core/catalog_sync.py` | Background task (asyncio) | SQLite upsert; chunked paging from providers |
| Live episode + watch fetch | `integrations/*` providers | `core/catalog.py` | Never persisted; called by resume + episodes routes |
| ResumeCursor computation | `core/resume.py` (`ResumeService`) | Provider on-deck fetch | Pure domain logic; provider-agnostic thresholds D-11 |
| Library scoping | `core/config.py` + `app_metadata` or dedicated table | Admin routes | Install-level filter before browse queries |
| REST catalog surface | `api/routes/catalog.py` | Pydantic schemas in `api/schemas/` | Phase 3 SPA consumer |
| Migrations | Alembic `002_connections_catalog.py` | SQLAlchemy models | Portable types per Phase 1 pattern |
| Integration tests | `tests/` + `tests/fixtures/` | respx httpx mocks | Recorded JSON fixtures; no live Plex/Jellyfin in CI |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 2 replaces the Phase 1 integration stubs with live **async httpx** clients behind a shared **`MediaProvider` protocol**, exposing a **full REST catalog API** for Phase 3. Plex authentication uses the official **PIN OAuth flow** against `plex.tv/api/v2` (not server-local tokens pasted by users). Jellyfin has **no OAuth** — implement an auth wizard flow via `POST /Users/AuthenticateByName` that stores a per-user **AccessToken** in the vault; avoid admin API keys for watch-state reads (admin keys bypass user scoping).

**Plex server access:** After OAuth, discover servers via `GET https://plex.tv/api/v2/resources?includeHttps=1`, match operator-configured base URL (or let operator pick from discovered resources), then call the local PMS with `X-Plex-Token`. Libraries: `GET /library/sections` (filter `type=show`). Series: `GET /library/sections/{sectionKey}/all?type=2`. Episodes + watch: `GET /library/metadata/{showRatingKey}/allLeaves` — each leaf exposes `viewCount`, `viewOffset`, `duration`, `guid`, `parentIndex`, `index`. On Deck: `GET /library/metadata/{showRatingKey}?includeOnDeck=1` (parse `OnDeck` child) or section-level `/library/sections/{id}/onDeck`. **Stable ID:** persist Plex `guid` in composite IDs; resolve to current `ratingKey` via `GET /library/metadata/` search or cached mapping at call time.

**Jellyfin server access:** Authenticate with MediaBrowser Authorization header. Libraries: `GET /Library/MediaFolders` (filter `CollectionType=tvshows`). Series: `GET /Items?ParentId={libraryId}&IncludeItemTypes=Series&Recursive=true&StartIndex=&Limit=&SearchTerm=`. Episodes: `GET /Shows/{seriesId}/Episodes?userId={userId}&EnableUserData=true`. Watch fields on `UserData`: `Played`, `PlayCount`, `PlayedPercentage`, `PlaybackPositionTicks` (10,000 ticks = 1 ms). Next Up: `GET /Shows/NextUp?userId=&seriesId=&Limit=1&EnableUserData=true&EnableResumable=true` — use as Jellyfin's "on deck" signal; do **not** rely on global NextUp limit quirks for resume algorithm (fetch full episode list + compute locally per D-10).

**ResumeCursor (D-10–D-13):** `ResumeService.compute(series_id, episodes[], on_deck_episode?)` → classify watch state (D-11), order episodes with specials rule (D-12), find earliest unfinished, compare ordinal position to on-deck; pick on-deck if strictly ahead in sequence. Key per `(app_user_id, connection_id, series_composite_id)`.

**Caching (D-14–D-18):** Persist `connections`, `cached_libraries`, `cached_series`, `user_media_links`, `catalog_sync_state` in SQLite. Background asyncio task pulls series in pages (default chunk 100) on connect/login/manual refresh. API returns cached data immediately with `sync_status` field.

**Primary recommendation:** Implement vertical slices per provider behind `MediaProvider`, ship migration `002_connections_catalog`, extend vault key helper for per-user tokens, build `ResumeService` with golden-vector unit tests independent of HTTP, and expose REST under `/api/v1/` prefix with OpenAPI tags for Phase 3.
</research_summary>

<standard_stack>
## Standard Stack

### Core (existing + Phase 2 additions)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | ≥0.27 | Async provider HTTP | Already in pyproject; native async with FastAPI |
| FastAPI | ≥0.115 | REST + OAuth callbacks | Phase 1 baseline |
| Pydantic v2 | (via FastAPI) | DTOs + settings | Shared schemas for API + domain |
| SQLAlchemy | ≥2.0 | ORM for cache tables | Alembic migrations |
| Alembic | ≥1.13 | Schema migrations | `002_connections_catalog` |
| cryptography | ≥42.0 | Vault Fernet | Existing `SecretsVault` |
| respx | ≥0.21 | httpx mock router | Dev dependency; fixture-based provider tests |
| pytest + pytest-asyncio | ≥8 / ≥0.24 | Unit + async route tests | Phase 1 CI pattern |

### External APIs
| API | Base URL | Auth | Phase 2 Usage |
|-----|----------|------|---------------|
| Plex OAuth | `https://plex.tv/api/v2` | PIN flow → `authToken` | User linking (D-08) |
| Plex Media Server | Operator `base_url` | `X-Plex-Token` header | Libraries, shows, episodes, On Deck |
| Jellyfin Server | Operator `base_url` | `Authorization: MediaBrowser … Token="…"` | Libraries, shows, episodes, NextUp |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw httpx | python-plexapi | Sync-oriented; hides ratingKey resolution but couples to sync model |
| respx | pytest-httpx | Either works; respx has richer route matching for fixtures |
| Background asyncio task | Celery/RQ | Overkill for ≤5 users; deferred to Phase 5 worker profile |
| Admin Jellyfin API key | Per-user AuthenticateByName | API keys are admin-level; breaks per-user watch state (D-13) |

**Installation (dev test deps):**
```bash
cd backend && uv add --dev respx
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### System Architecture Diagram

```
Phase 3 SPA
    │  REST /api/v1/*
    ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI                                                  │
│  connections │ oauth_plex │ oauth_jellyfin │ catalog    │
└─────────┬───────────────────────────────┬───────────────┘
          │                               │
          ▼                               ▼
┌──────────────────┐            ┌─────────────────────┐
│ core/            │            │ integrations/        │
│ connections.py   │◄──────────►│ MediaProvider proto  │
│ catalog_sync.py  │            │ plex/client.py       │
│ resume.py        │            │ jellyfin/client.py   │
└────────┬─────────┘            └──────────┬──────────┘
         │                                  │ httpx
         ▼                                  ▼
┌──────────────────┐            ┌─────────────────────┐
│ SQLite           │            │ Plex PMS / Jellyfin  │
│ connections      │            │ (operator servers)   │
│ cached_*         │            └─────────────────────┘
│ user_media_links │
│ secrets (vault)  │
└──────────────────┘
```

### Recommended Project Structure (Phase 2 additions)

```
backend/src/wheeloffish/
├── api/
│   ├── deps.py                    # get_db, get_vault, get_current_user (stub until auth phase)
│   ├── schemas/
│   │   ├── connections.py
│   │   ├── catalog.py
│   │   └── resume.py
│   └── routes/
│       ├── connections.py
│       ├── oauth_plex.py
│       ├── oauth_jellyfin.py
│       └── catalog.py
├── core/
│   ├── connections.py             # test-then-save, provider factory
│   ├── catalog_sync.py            # chunked background sync
│   ├── resume.py                  # ResumeService
│   └── namespaces.py              # extend token key helpers
├── db/models/
│   ├── connection.py
│   ├── cached_library.py
│   ├── cached_series.py
│   ├── user_media_link.py
│   └── catalog_sync_state.py
├── domain/
│   ├── dto.py                     # Library, Series, Episode, ResumeCursor, WatchState
│   └── ids.py                     # composite ID parse/format
└── integrations/
    ├── base.py                    # MediaProvider Protocol
    ├── errors.py                  # ProviderError taxonomy → 422 codes
    ├── plex/
    │   ├── auth.py
    │   ├── client.py
    │   └── mappers.py
    └── jellyfin/
        ├── auth.py
        ├── client.py
        └── mappers.py

backend/tests/
├── fixtures/
│   ├── plex/                      # sanitized JSON recordings
│   └── jellyfin/
├── unit/
│   ├── test_resume_service.py
│   ├── test_composite_ids.py
│   └── test_watch_classification.py
├── integrations/
│   ├── test_plex_client.py        # respx + fixtures
│   └── test_jellyfin_client.py
└── api/
    ├── test_connections_routes.py
    └── test_catalog_routes.py
```

### Pattern 1: MediaProvider Protocol

```python
# integrations/base.py
from typing import Protocol
from wheeloffish.domain.dto import Episode, Library, PagedSeries, Series

class MediaProvider(Protocol):
    async def ping(self) -> None: ...
    async def list_libraries(self) -> list[Library]: ...
    async def list_series(
        self, library_native_id: str, *, page: int, limit: int, q: str | None
    ) -> PagedSeries: ...
    async def list_episodes(self, series_composite_id: str) -> list[Episode]: ...
    async def get_on_deck_episode(self, series_composite_id: str) -> Episode | None: ...
```

Factory in `core/connections.py`: load connection row + vault token for `(connection_id, app_user_id)` → instantiate `PlexProvider` or `JellyfinProvider`.

### Pattern 2: Composite stable IDs (D-19)

Format: `{connection_uuid}:plex:{urlencoded_guid}` or `{connection_uuid}:jellyfin:{item_uuid}`

```python
# domain/ids.py
def parse_composite_id(value: str) -> tuple[str, str, str]: ...
def format_composite_id(connection_id: str, provider: str, native_id: str) -> str: ...
```

Plex provider resolves `native_id` (GUID) → current `ratingKey` via `GET /library/all?guid=…` or metadata search before episode fetches.

### Pattern 3: Two-layer DTOs (D-20)

| Layer | Types | Persisted | Fields |
|-------|-------|-----------|--------|
| Browse/cache | `Library`, `Series` | Yes (`cached_*` tables) | id, title, year, thumb_url, library_id, provider_metadata JSON |
| Rebuild/live | `Episode`, `WatchSnapshot` | No | season_index, episode_index, title, duration_ms, percent_watched, is_played, part_index?, multipart_group_id? |

`ResumeCursor`: `{ series_id, season_index, episode_index, episode_id, percent_watched, source: "earliest_unfinished" | "on_deck" }`

### Pattern 4: Test-then-save transaction (D-07)

```python
async def create_connection(...):
    provider = build_ephemeral_provider(config, token)
    try:
        await provider.ping()
    except ProviderUnreachable: raise HTTPException(422, detail={"code": "unreachable"})
    except ProviderUnauthorized: raise HTTPException(422, detail={"code": "unauthorized"})
    # single DB transaction: insert connection + vault.set_secret + commit
```

### Pattern 5: Non-blocking catalog sync (D-17, D-18)

On OAuth success or `POST …/sync`: set `catalog_sync_state.status = "running"`, spawn `asyncio.create_task(run_chunked_sync(connection_id))`. Each chunk: provider.list_series(page=N) → upsert `cached_series` → update cursor. Login route returns `{ series: [...cached...], sync: { status, progress } }` without awaiting completion.

### Anti-Patterns to Avoid
- **Storing Plex ratingKey in composite IDs** — ephemeral across server migrations (D-19)
- **Caching episodes in SQLite** — explicitly rejected (D-14, D-15)
- **Jellyfin admin API key for all users** — breaks per-user watch isolation (D-13)
- **Blocking login on full library pull** — violates D-17, D-18
- **Using Jellyfin global NextUp alone for resume** — insufficient for hybrid rule; always compute from full episode list (D-10)
</architecture_patterns>

<implementation_notes>
## Implementation Notes

### 1. Plex OAuth flow (D-08)

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Generate/store `X-Plex-Client-Identifier` per connection (UUID) | DB column `plex_client_identifier` |
| 2 | Create PIN | `POST https://plex.tv/api/v2/pins?strong=true` + headers `X-Plex-Product`, `X-Plex-Client-Identifier` |
| 3 | Return auth URL to SPA | `https://app.plex.tv/auth#?clientID=…&code=…&forwardUrl=…&context[device][product]=WheelOfFishTV` |
| 4 | Callback/poll PIN | `GET https://plex.tv/api/v2/pins/{pin_id}` until `authToken` present |
| 5 | Validate token | `GET https://plex.tv/api/v2/user` with `X-Plex-Token` → 200/401 |
| 6 | Discover server | `GET https://plex.tv/api/v2/resources?includeHttps=1` → match operator `base_url` |
| 7 | Test-then-save | `GET {base_url}/library/sections` with token → persist connection + vault token |

**WOF routes (suggested):**
- `POST /api/v1/connections/plex/oauth/start` → `{ pin_id, auth_url }`
- `GET /api/v1/connections/plex/oauth/callback?pin_id=…` → completes link, test-then-save
- Optional poll: `GET /api/v1/connections/plex/oauth/status/{pin_id}` for SPA polling flow

**Required Plex headers on all calls:** `X-Plex-Product`, `X-Plex-Client-Identifier`, `X-Plex-Token`, `Accept: application/json`

### 2. Jellyfin auth (D-08) — not OAuth

| Method | When | Endpoint |
|--------|------|----------|
| Username/password | Per-user linking (primary) | `POST {base_url}/Users/AuthenticateByName` |
| Token validation | Test connection | `GET {base_url}/Users/Me` with AccessToken |
| API key | **Avoid for watch state** | Admin-only; document as unsupported for user linking |

**WOF routes:**
- `POST /api/v1/connections/jellyfin/auth` body `{ base_url, username, password, display_name, verify_ssl }` → test-then-save
- Store `jellyfin_user_id` from auth response `User.Id` in connection/link row

**Authorization header format:**
```
Authorization: MediaBrowser Client="WheelOfFishTV", Device="Server", DeviceId="{uuid}", Version="0.1.0", Token="{access_token}"
```

### 3. Provider API endpoint mapping

| Operation | Plex | Jellyfin |
|-----------|------|----------|
| Ping | `GET /identity` or `/library/sections` | `GET /System/Info` or `/Users/Me` |
| Libraries | `GET /library/sections` (type=2) | `GET /Library/MediaFolders` (`CollectionType=tvshows`) |
| Series page | `GET /library/sections/{id}/all?type=2&X-Plex-Container-Start=&Size=` | `GET /Items?ParentId=&IncludeItemTypes=Series&StartIndex=&Limit=&SearchTerm=` |
| Episodes | `GET /library/metadata/{ratingKey}/allLeaves` | `GET /Shows/{id}/Episodes?userId=&EnableUserData=true` |
| On Deck / Next Up | `GET /library/metadata/{ratingKey}?includeOnDeck=1` | `GET /Shows/NextUp?seriesId=&userId=&Limit=1&EnableUserData=true` |
| Watch: played flag | `viewCount > 0` | `UserData.Played == true` |
| Watch: percent | `viewOffset / duration` (ms) | `UserData.PlayedPercentage` or ticks/duration |
| Stable series ID | `guid` attribute | `Id` (UUID) |
| Specials season | `parentIndex == 0` or `Season.type == "season"` index 0 | `IsSpecialSeason` on season items |

### 4. DB schema — migration `002_connections_catalog`

**File:** `backend/alembic/versions/002_connections_catalog.py`

```python
# connections — install-level server config (max one per provider_type)
connections:
  id                  UUID PK
  provider_type       String(16)   # 'plex' | 'jellyfin'
  display_name        String(255)
  base_url            String(512)
  verify_ssl          Boolean default true
  plex_client_identifier  String(64) nullable   # Plex only
  enabled             Boolean default true
  created_at, updated_at

# user_media_links — per WOF user token binding (D-13)
user_media_links:
  id                  UUID PK
  app_user_id         UUID FK (nullable stub UUID until Phase 3 auth)
  connection_id       UUID FK → connections
  provider_user_id    String(128)   # Plex account id / Jellyfin User.Id
  provider_username   String(255) nullable
  linked_at           DateTime

# cached_libraries — scoped browse libraries (D-09)
cached_libraries:
  id                  UUID PK
  connection_id       UUID FK
  native_id           String(128)   # Plex section key / Jellyfin folder Id
  title               String(255)
  in_scope            Boolean       # admin-selected
  synced_at           DateTime

# cached_series — show metadata only (D-14)
cached_series:
  id                  String(512) PK  # composite stable id
  connection_id       UUID FK
  library_native_id   String(128)
  native_id           String(256)     # guid or jellyfin id
  title               String(512)
  title_sort          String(512) nullable
  year                Integer nullable
  thumb_url           String(1024) nullable
  provider_metadata   JSON nullable   # extra provider fields
  synced_at           DateTime
  UNIQUE(connection_id, native_id)

# catalog_sync_state — chunked sync progress (D-17)
catalog_sync_state:
  connection_id       UUID PK FK
  status              String(16)   # idle|running|failed|complete
  library_native_id   String(128) nullable  # current library chunk
  page_cursor         Integer default 0
  total_estimated     Integer nullable
  error_message       Text nullable
  started_at, updated_at
```

**Vault key extension** (`core/namespaces.py`):
```python
def media_user_token_key(connection_id: str, app_user_id: str) -> str:
    return f"media_server/{connection_id}/users/{app_user_id}/token"
```

Deprecate single `media_server/{connection_id}/token` for user-linked flows; keep helper for backward compat during migration.

**Install library scope env:**
```
WOF_ENABLED_PROVIDERS=plex,jellyfin
WOF_SCOPED_LIBRARY_IDS=           # optional comma list; empty = admin picks via API later
```

### 5. ResumeCursor algorithm (D-10–D-13)

**File:** `backend/src/wheeloffish/core/resume.py`

```python
class WatchState(str, Enum):
    UNWATCHED = "unwatched"
    PARTIAL = "partial"
    COMPLETE = "complete"

def classify_watch(ep: Episode) -> WatchState:
    if ep.provider_marked_played: return COMPLETE
    if ep.percent_watched >= 95: return COMPLETE
    if ep.percent_watched >= 5: return PARTIAL
    return UNWATCHED

def order_episodes(episodes: list[Episode]) -> list[Episode]:
    # D-12: group by season; within season sort by index;
    # after each main season's last episode, append specials tagged to that season
    ...

def compute_resume(episodes, on_deck: Episode | None) -> ResumeCursor:
    ordered = order_episodes(episodes)
    earliest = next((e for e in ordered if classify_watch(e) != COMPLETE), None)
    if earliest is None:
        return ResumeCursor(series_complete=True, ...)
    if on_deck and is_ahead_in_sequence(on_deck, earliest, ordered):
        return ResumeCursor(episode=on_deck, source="on_deck", ...)
    return ResumeCursor(episode=earliest, source="earliest_unfinished", ...)
```

`is_ahead_in_sequence(A, B, ordered)`: index(A) > index(B) in ordered list **and** all episodes between B and A are COMPLETE (user deliberately skipped).

**Golden vectors** in `tests/unit/test_resume_service.py`: unwatched series → E1; partial S1E3 → S1E3; skipped ahead with On Deck S2E1 while S1E5 unwatched → On Deck; all complete → series_complete flag.

### 6. REST API surface for Phase 3 (D-04, D-22)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/connections` | List install connections |
| POST | `/api/v1/connections/plex/oauth/start` | Begin Plex PIN OAuth |
| GET | `/api/v1/connections/plex/oauth/callback` | Complete Plex OAuth + save |
| POST | `/api/v1/connections/jellyfin/auth` | Jellyfin username auth + save |
| POST | `/api/v1/connections/{id}/test` | Re-validate token (D-07) |
| DELETE | `/api/v1/connections/{id}` | Remove connection + vault keys |
| GET | `/api/v1/connections/{id}/libraries` | Cached libraries (in_scope filter) |
| PUT | `/api/v1/admin/connections/{id}/library-scope` | Admin set in_scope flags (D-09) |
| GET | `/api/v1/connections/{id}/series?page=&limit=&q=` | Cached series browse (D-17) |
| POST | `/api/v1/connections/{id}/sync` | Trigger show-metadata sync (D-16) |
| GET | `/api/v1/connections/{id}/sync/status` | Chunk progress for banner (D-18) |
| GET | `/api/v1/connections/{id}/series/{series_id}/episodes` | Live episodes + watch (not cached) |
| GET | `/api/v1/connections/{id}/series/{series_id}/resume` | `ResumeCursor` (INT-03 proof) |

**Response envelope for browse routes:**
```json
{
  "items": [...],
  "page": 1,
  "limit": 50,
  "total": 1234,
  "sync": { "status": "running", "progress_pct": 42 }
}
```

Register routers in `main.py`:
```python
app.include_router(connections.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
```

### 7. Config additions (`core/config.py`)

```python
WOF_ENABLED_PROVIDERS: str = "plex,jellyfin"  # parsed to set
WOF_PLEX_PRODUCT_NAME: str = "Wheel of Fish TV"
WOF_OAUTH_CALLBACK_BASE: str = "http://localhost:8000"  # forwardUrl base
WOF_CATALOG_SYNC_CHUNK_SIZE: int = 100
WOF_CATALOG_PAGE_DEFAULT: int = 50
```

Update `.env.example` with new vars (no secrets).
</implementation_notes>

<pitfalls>
## Pitfalls

### Pitfall 1: Plex ratingKey instability
**What goes wrong:** Composite IDs break after Plex library refresh or server move
**How to avoid:** Store Plex `guid` in `cached_series.native_id`; resolve ratingKey at request time (D-19)
**Warning signs:** Resume/episodes 404 on previously working series

### Pitfall 2: Jellyfin API key for all users
**What goes wrong:** All users see same watch state (admin's or aggregated)
**How to avoid:** Per-user `AuthenticateByName` tokens in vault keyed by `app_user_id` (D-13)
**Warning signs:** Resume cursor identical for different household users

### Pitfall 3: Blocking login on full sync
**What goes wrong:** Timeouts on large libraries; bad UX
**How to avoid:** Background chunked sync; return stale cache + status (D-17, D-18)
**Warning signs:** Login >5s; SPA spinner with no data

### Pitfall 4: Caching episodes/watch state
**What goes wrong:** Stale resume between daily rebuilds
**How to avoid:** Live fetch only; no episode table in Phase 2 (D-14, D-15)
**Warning signs:** User watched episode externally; WOF still shows old percent

### Pitfall 5: Plex OAuth token on wrong server
**What goes wrong:** Token valid at plex.tv but server URL unreachable / mismatched
**How to avoid:** Test-then-save pings operator `base_url` with token after resource discovery (D-07)
**Warning signs:** OAuth succeeds but browse fails with connection refused

### Pitfall 6: Jellyfin NextUp limit quirks
**What goes wrong:** Missing on-deck when using low `Limit` on global NextUp
**How to avoid:** Call `Shows/NextUp?seriesId={id}&Limit=1` per series; primary resume from full episode scan (D-10)
**Warning signs:** On Deck null for series with known next episode

### Pitfall 7: Specials ordering breaks resume index
**What goes wrong:** Resume points to special before main season finale
**How to avoid:** Implement D-12 ordering in `ResumeService.order_episodes` before cursor scan
**Warning signs:** Resume lands on S00E01 while main season episodes unwatched

### Pitfall 8: SSL verification disabled silently
**What goes wrong:** MITM on self-signed Jellyfin; or false `ssl_error` on valid certs
**How to avoid:** `verify_ssl` column + httpx `verify=` param; map SSLError → 422 `ssl_error` (D-07)
**Warning signs:** Intermittent connection failures on HTTPS LAN servers

### Pitfall 9: Provider rate limiting during sync
**What goes wrong:** Plex/Jellyfin throttles chunked sync
**How to avoid:** Default chunk 100; small delay between chunks; honor `Retry-After` if present
**Warning signs:** 429 responses during manual refresh

### Pitfall 10: Transaction split on create
**What goes wrong:** DB row without vault token (or inverse) on partial failure
**How to avoid:** Single SQLAlchemy session transaction wrapping DB insert + vault write before commit (D-07)
**Warning signs:** Connection exists but auth always unauthorized
</pitfalls>

## Validation Architecture

| Requirement | Behavior to Verify | Test Type | Command / Assertion |
|-------------|-------------------|-----------|---------------------|
| INT-01 | Plex OAuth PIN start returns auth_url + pin_id | unit (respx) | `pytest tests/integrations/test_plex_client.py -k oauth_start` |
| INT-01 | Plex OAuth callback stores encrypted token in vault | integration | `pytest tests/api/test_connections_routes.py -k plex_oauth` + assert secrets row |
| INT-01 | Jellyfin AuthenticateByName success path stores token | unit (respx) | `pytest tests/integrations/test_jellyfin_client.py -k auth` |
| INT-01 | Test-then-save rejects unreachable server (422 `unreachable`) | unit | mock connection refused → assert detail.code |
| INT-01 | Test-then-save rejects bad credentials (422 `unauthorized`) | unit | mock 401 → assert detail.code |
| INT-01 | `WOF_ENABLED_PROVIDERS=plex` blocks Jellyfin create (422 `provider_disabled`) | unit | `pytest tests/api/test_connections_routes.py -k provider_disabled` |
| INT-01 | At most one connection per provider_type | integration | second POST same type → 409 or 422 |
| INT-01 | `POST /connections/{id}/test` re-validates without persisting bad token | unit | token rotation mock |
| INT-02 | Plex provider lists TV libraries from fixture | unit (fixture) | `tests/fixtures/plex/library_sections.json` |
| INT-02 | Jellyfin provider lists tvshows folders from fixture | unit (fixture) | `tests/fixtures/jellyfin/media_folders.json` |
| INT-02 | Cached series browse returns paged results with `?page=&limit=&q=` | integration | DB seeded → GET series → assert total/page |
| INT-02 | Library scope filter excludes out-of-scope libraries (D-09) | unit | in_scope=false rows omitted |
| INT-02 | Background sync upserts cached_series in chunks | integration | trigger sync → poll status → row count increases |
| INT-02 | Login/browse returns immediately with sync.status=running (D-18) | integration | sync not awaited in request handler |
| INT-03 | Watch classification thresholds (D-11) | unit | `pytest tests/unit/test_watch_classification.py` — 4%, 50%, 96%, viewCount override |
| INT-03 | Specials ordering places specials after season finale (D-12) | unit | `pytest tests/unit/test_resume_service.py -k specials` |
| INT-03 | Hybrid rule: on_deck ahead of earliest unfinished (D-10) | unit | golden vectors in test_resume_service |
| INT-03 | Hybrid rule: earliest unfinished when on_deck behind | unit | golden vector |
| INT-03 | Live episodes endpoint returns watch snapshots, not DB rows | integration | no episode table; GET episodes → fields populated |
| INT-03 | `GET …/resume` returns ResumeCursor matching ResumeService | integration | same fixture episodes → assert cursor episode_id + source |
| INT-03 | Per-user isolation: different tokens → different resume | unit | two app_user fixtures, distinct percent_watched |
| D-03 | Recorded fixtures contain no real tokens/URLs | source | grep fixtures for `X-Plex-Token`, redact in CI |
| D-03 | CI runs without live Plex/Jellyfin | CI | respx-only; live UAT checklist documented separately |

**Wave 0 (test infrastructure):**
- Add `respx` to dev dependencies; extend `conftest.py` with `httpx.AsyncClient`, `vault` fixture, `connection_factory` fixture
- `tests/fixtures/plex/` — `pin_create.json`, `pin_claimed.json`, `library_sections.json`, `show_leaves.json`, `show_ondeck.json` (sanitized)
- `tests/fixtures/jellyfin/` — `authenticate.json`, `media_folders.json`, `series_items.json`, `episodes.json`, `next_up.json`
- `tests/unit/test_resume_service.py` — pure domain golden vectors (no HTTP)
- `tests/unit/test_composite_ids.py` — parse/format round-trip
- `tests/integrations/test_plex_client.py`, `test_jellyfin_client.py` — respx routes → mapper output
- `tests/api/test_connections_routes.py`, `test_catalog_routes.py` — FastAPI TestClient + temp DB migration `002`

**Manual live UAT checklist (not CI):**
1. Plex OAuth end-to-end against real PMS → libraries visible
2. Jellyfin username auth against real server → libraries visible
3. Resume preview matches Plex On Deck / Jellyfin Next Up for 3 test series (ordered, skipped-ahead, partial)
4. Manual refresh updates show list after adding new series externally

**Sampling:**
- After each task: `uv run pytest tests/unit -q`
- After provider slice: `uv run pytest tests/integrations -q`
- Before phase verify: `uv run ruff check . && uv run pytest`

<sources>
## Sources

### Primary (HIGH confidence)
- [Plex authenticating with Plex forum guide](https://forums.plex.tv/t/authenticating-with-plex/609370) — PIN OAuth flow, forwardUrl, token validation
- [Plex API reference (plexapi.dev)](https://plexapi.dev/api-reference/content/set-section-leaves) — viewCount, viewOffset, episode leaf attributes
- [Jellyfin Authentication Overview](https://jellyfin-jellyfin.mintlify.app/api/authentication/overview) — AuthenticateByName, token header format
- [Jellyfin Library API](https://jellyfin-jellyfin.mintlify.app/api/media/library) — MediaFolders
- [Jellyfin Items API](https://jellyfin-jellyfin.mintlify.app/api/media/items) — series paging, IncludeItemTypes
- Phase 1 codebase — `secrets.py`, `namespaces.py`, migration `001_foundation.py`, test patterns

### Secondary (MEDIUM confidence)
- python-plexapi source — On Deck URL patterns (`includeOnDeck=1`, `/library/sections/{id}/onDeck`)
- Jellyfin TypeScript SDK — `TvShowsApi.getNextUp`, `getEpisodes` parameter shapes
- `.planning/research/SUMMARY.md` — ResumeCursor normalization, rate-limit notes

### Tertiary (validate during implementation)
- Plex `guid` → ratingKey resolution exact query — verify against target PMS version
- Jellyfin `PlayedPercentage` availability across server versions — fallback to ticks/duration
</sources>

<metadata>
## Metadata

**Research scope:** Plex OAuth + API, Jellyfin auth + TV endpoints, MediaProvider design, DB schema, ResumeCursor algorithm, REST API for Phase 3, test strategy

**Confidence breakdown:**
- Plex OAuth + PMS read APIs: HIGH — official forum docs + widespread community usage
- Jellyfin auth + Items/Shows APIs: MEDIUM-HIGH — documented; no OAuth; version field variance possible
- ResumeCursor domain logic: HIGH — fully specified in CONTEXT D-10–D-13
- Architecture fit with Phase 1: HIGH — extends existing vault, migrations, httpx dependency

**Research date:** 2026-05-25
**Valid until:** 2026-06-25
</metadata>

---

*Phase: 02-media-ingestion-catalogs*
*Research completed: 2026-05-25*
*Ready for planning: yes*

## RESEARCH COMPLETE
