# Phase 09: series-detail-watch-state-from-playlists-library-view-edit-p - Research

**Researched:** 2026-05-27
**Domain:** Series detail parity + provider-backed watch-state mutation (Plex/Jellyfin)
**Confidence:** MEDIUM

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Plex watched/unwatched writes use `GET /:/scrobble` + `GET /:/unscrobble` with `ratingKey` [CITED: https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/]
- Jellyfin watched/unwatched writes use `POST /UserPlayedItems/{itemId}` + `DELETE /UserPlayedItems/{itemId}` [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/Jellyfin.Api/Controllers/PlaystateController.cs]
- Jellyfin folder-level mark played/unplayed recurses descendants via `Folder.MarkPlayed` / `Folder.MarkUnplayed` [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/MediaBrowser.Controller/Entities/Folder.cs]
- Feature is viable on both providers at episode/season/series scope; planner should not block on "API missing" [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
- Plex episode identity may be GUID while scrobble needs `ratingKey`; reuse existing GUID->`ratingKey` resolution patterns [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
- After successful provider mutation, UX state must refresh/reconcile and not remain stale [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
- On-deck remains derived from provider progress + existing mapper/resume logic; no separate on-deck write API [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
- Respect 401/403 and partial-failure semantics in UX and API responses [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

### Claude's Discretion
- Post-mutation refresh strategy (optimistic update vs targeted refetch vs background sync) [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
- Exact API route placement and service decomposition for mark watched/unwatched operations [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)
- None explicitly listed in `9-CONTEXT.md`. [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEB-01 | SPA parity for series detail/watch-state controls in Library/view/edit playlist flows | Reuse `SeriesDetailPage`, `TwoPanePicker`, `PlaylistMemberTile`, and query invalidation patterns already in frontend [CITED: frontend/src/pages/SeriesDetailPage.tsx] |
| INT-01 | Provider integration supports watch-state writeback | Provider-level mutation methods can be added to existing `MediaProvider` integration layer and implemented in Plex/Jellyfin clients [CITED: backend/src/wheeloffish/integrations/base.py] |
| INT-02 | Integration behavior usable with scoped catalogs/series surfaces | Existing scoped catalog routes + per-user auth behavior provide safe base to attach watch write endpoints [CITED: backend/src/wheeloffish/api/routes/catalog.py] |

## Summary

Phase 09 should be planned as a parity extension, not a greenfield feature. The current stack already has (1) series detail routing and data hooks, (2) playlist edit tile/context menu primitives, and (3) provider abstraction and robust error mapping. The missing piece is a write path for watch-state updates (episode/season/series) and rendering richer grouped episode state in series detail. [CITED: frontend/src/pages/SeriesDetailPage.tsx] [CITED: frontend/src/components/playlists/TwoPanePicker.tsx] [CITED: backend/src/wheeloffish/api/routes/catalog.py]

Provider constraints are favorable but asymmetric. Jellyfin has explicit Playstate endpoints and folder-recursive behavior that supports bulk season/series updates in one call when given proper item IDs. Plex uses de-facto `scrobble/unscrobble` behavior keyed by numeric `ratingKey`; this is practical but less formally stable, and season-level bulk remains a required UAT confirmation item. [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/Jellyfin.Api/Controllers/PlaystateController.cs] [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/MediaBrowser.Controller/Entities/Folder.cs] [CITED: https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/] [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

Primary implementation risks are identity translation (Plex GUID to `ratingKey`), stale UI state after writes, and bulk mutation UX semantics when provider permissions/session are invalid. Planning should explicitly split backend mutation API, provider adapter methods, frontend state grouping/actions, and verification (including locked T-09 checks). [CITED: backend/src/wheeloffish/integrations/plex/playlists.py] [CITED: backend/src/wheeloffish/core/provider_writeback.py] [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

**Primary recommendation:** Extend existing catalog/provider architecture with explicit watch-state mutation services and route handlers, then wire UI parity features around current detail and playlist-tile components rather than introducing new page patterns.

## Project Constraints (from .cursor/rules/)

- No `.cursor/rules/` directory exists in this repository at research time. [CITED: repository filesystem scan]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Series detail navigation parity from Library/view/edit playlist | Browser / Client | API / Backend | Route wiring, context-menu actions, and page transitions are client-owned; detail data comes from existing API routes. [CITED: frontend/src/App.tsx] |
| Episode list grouping/state chips (watched/on-deck/unwatched) | Browser / Client | API / Backend | UI computes grouping/presentation from episode payload + resume payload already exposed by backend. [CITED: frontend/src/hooks/useSeriesEpisodes.ts] |
| Watch-state mutation endpoints (episode/season/series) | API / Backend | Database / Storage | Auth, ownership, provider dispatch, and error translation belong in backend route/service layer. [CITED: backend/src/wheeloffish/api/routes/catalog.py] |
| Provider call translation (Plex/Jellyfin) | API / Backend | External provider APIs | Integration clients own endpoint specifics (`ratingKey`, item IDs, request methods). [CITED: backend/src/wheeloffish/integrations/plex/client.py] [CITED: backend/src/wheeloffish/integrations/jellyfin/client.py] |
| Post-write state reconciliation | Browser / Client | API / Backend | Frontend query invalidation/refetch should align with mutation success/failure; backend should return deterministic status/errors. [CITED: frontend/src/api/playlists.ts] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | REST endpoints for catalog/watch mutations | Existing backend API framework and dependency system. [CITED: backend/pyproject.toml] |
| SQLAlchemy | >=2.0 | DB access + owner-scoped data lookups | Existing persistence and ownership enforcement patterns. [CITED: backend/src/wheeloffish/api/routes/playlists.py] |
| React + React Router | 19.2.6 / 7.15.1 | Series detail routing + playlist flow parity | Current SPA and route model already in place. [CITED: frontend/package.json] [CITED: frontend/src/App.tsx] |
| TanStack Query | 5.100.14 | Mutation/refetch orchestration | Existing query invalidation model used across playlist mutations. [CITED: frontend/src/api/playlists.ts] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27 | Provider HTTP calls | For new watch mutation calls in Plex/Jellyfin clients. [CITED: backend/pyproject.toml] |
| Sonner | 2.0.7 | User-facing success/error toasts | For immediate feedback on watch-state actions in UI. [CITED: frontend/package.json] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New standalone watch-state microservice | Existing `catalog` route + integration layer extension | Reuse avoids duplicated auth/ownership/provider plumbing and reduces rollout risk. [CITED: backend/src/wheeloffish/api/routes/catalog.py] |
| New series detail page variant for playlists | Reuse current `SeriesDetailPage` route with contextual return links | Maintains parity and avoids UI divergence. [CITED: frontend/src/pages/SeriesDetailPage.tsx] |

**Installation:** no new external packages required for this phase as scoped. [CITED: backend/pyproject.toml] [CITED: frontend/package.json]

## Package Legitimacy Audit

No new third-party packages are required by this phase scope; package legitimacy gate is not triggered. [CITED: phase scope + existing stack reuse]

## Architecture Patterns

### System Architecture Diagram

```text
Library / playlist tile interactions
  -> Series detail route (/series?id=...)
    -> fetch series + episodes + resume (read path)
      -> render grouped seasons + watch-state affordances
        -> user invokes mark watched/unwatched action
          -> POST/DELETE watch endpoint (episode|season|series)
            -> provider adapter dispatch
              -> Plex scrobble/unscrobble (ratingKey)
              -> Jellyfin UserPlayedItems (itemId)
          -> mutation result
            -> invalidate/refetch detail queries
            -> update UI + toast + error surface
```

### Recommended Project Structure
```text
backend/src/wheeloffish/
├── api/routes/catalog.py                  # add watch mutation routes
├── integrations/base.py                   # extend provider protocol
├── integrations/plex/client.py            # plex watch mutation impl
├── integrations/jellyfin/client.py        # jellyfin watch mutation impl
└── core/                                  # optional thin orchestration helper

frontend/src/
├── pages/SeriesDetailPage.tsx             # grouped episodes + action menus
├── components/playlists/PlaylistRowMenuItems.tsx  # add "View series" action
├── components/playlists/TwoPanePicker.tsx # session-added prioritization in In pane
└── hooks/ / api/                          # mutation hooks + cache invalidation
```

### Pattern 1: Provider Adapter Extension
**What:** Add typed watch mutation capabilities to provider abstraction, then implement per-provider specifics in clients.
**When to use:** Any cross-provider operation with identical product behavior but different APIs.
**Example:**
```python
# Source: backend/src/wheeloffish/integrations/base.py
class MediaProvider(Protocol):
    async def list_episodes(self, series_composite_id: str) -> list[Episode]: ...
    async def get_on_deck_episode(self, series_composite_id: str) -> Episode | None: ...
    # add:
    # async def mark_watched(self, item_composite_id: str) -> None: ...
    # async def mark_unwatched(self, item_composite_id: str) -> None: ...
```

### Pattern 2: Optimistic UI with Reconcile
**What:** Update local UI immediately, then reconcile via server invalidation/refetch.
**When to use:** Tile/menu actions where immediate feedback matters and rollback is feasible.
**Example:**
```typescript
// Source: frontend/src/components/playlists/TwoPanePicker.tsx
const previousRows = rows
onRowsChange([...rows, newRow]) // optimistic
try {
  await appendMutation.mutateAsync({ playlistId, payload: { series_id: series.id } })
} catch {
  onRowsChange(previousRows) // rollback
}
```

### Anti-Patterns to Avoid
- **Forking separate detail UIs by entry point:** breaks parity and multiplies bugs; keep one detail route with contextual navigation. [CITED: frontend/src/App.tsx]
- **Direct provider calls from frontend:** bypasses ownership/auth controls and error normalization. [CITED: backend/src/wheeloffish/api/routes/catalog.py]
- **Assuming Plex season bulk without UAT proof:** must validate T-09-01 before calling behavior complete. [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resume/on-deck classification | Custom ad-hoc cursor logic in UI | Existing backend `ResumeService` and `/resume` endpoint | Already tested and provider-normalized. [CITED: backend/src/wheeloffish/core/resume.py] |
| Plex GUID to rating key translation | New lookup algorithm | Existing `resolve_guid_to_rating_key` + `resolve_episode_rating_key` helpers | Proven in playlist writeback path. [CITED: backend/src/wheeloffish/integrations/plex/mappers.py] [CITED: backend/src/wheeloffish/integrations/plex/playlists.py] |
| Playlist row action primitives | New context/dropdown infra | Existing `PlaylistRowMenuItems` and `PlaylistMemberTile` | Extensible and already tested. [CITED: frontend/src/components/playlists/PlaylistRowMenuItems.tsx] |

**Key insight:** this phase is mostly extension and composition; custom parallel implementations would increase drift and regressions.

## Common Pitfalls

### Pitfall 1: Plex identity mismatch on writes
**What goes wrong:** UI passes GUID-based episode IDs but Plex write endpoint needs numeric `ratingKey`.
**Why it happens:** Plex read models expose GUIDs for stability while write APIs key off metadata rating keys.
**How to avoid:** Route all Plex writes through existing GUID->`ratingKey` resolver path.
**Warning signs:** 404/422 on scrobble despite episode existing in detail list.

### Pitfall 2: Bulk action false-success UX
**What goes wrong:** UI claims whole season/series updated when provider partially failed or refused scope.
**Why it happens:** bulk semantics differ by provider/item type and permission state.
**How to avoid:** return operation summaries and display partial/error outcomes; keep T-09 verification gates.
**Warning signs:** response 200 but subsequent refetch shows unchanged episodes.

### Pitfall 3: Stale watch-state after mutation
**What goes wrong:** badge state remains outdated until manual refresh.
**Why it happens:** mutation path lacks query invalidation and reconcile.
**How to avoid:** invalidate `series-episodes` + `series-resume` queries on success/failure path where appropriate.
**Warning signs:** toast says success but UI state unchanged.

## Code Examples

### Plex episode key resolution reuse
```python
# Source: backend/src/wheeloffish/integrations/plex/playlists.py
async def resolve_episode_rating_key(provider: PlexProvider, episode_composite_id: str) -> str:
    connection_id, provider_kind, native_id = parse_composite_id(episode_composite_id)
    if native_id.isdigit():
        return native_id
    async with provider._client() as client:
        return await resolve_guid_to_rating_key(...)
```

### Existing series episode fetch hook (reuse for refetch keys)
```typescript
// Source: frontend/src/hooks/useSeriesEpisodes.ts
export function seriesEpisodesQueryKey(connectionId: string, seriesId: string) {
  return ["series-episodes", connectionId, seriesId] as const
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate/additive playlist authoring flows | Unified two-pane and shared detail/menu primitives | Phase 06 | Phase 09 can add parity features with minimal UI churn. [CITED: frontend/src/components/playlists/TwoPanePicker.tsx] |
| Provider writeback as future scope | Provider writeback delivered in Phase 07 | 2026-05 | Identity resolution and provider error handling patterns already exist. [CITED: backend/src/wheeloffish/core/provider_writeback.py] |

**Deprecated/outdated:**
- Creating new series detail route variants per page context is outdated for this codebase; parity now expects one detail pattern. [CITED: frontend/src/App.tsx]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Plex season-level `scrobble/unscrobble` works as bulk mark for all child episodes. [ASSUMED] | Summary / Pitfalls | Season bulk action could silently no-op or partially apply; needs T-09-01 UAT. |
| A2 | Existing episode payloads are sufficient to derive "on-deck" visual marker without API schema additions. [ASSUMED] | Architecture Patterns | Might need extra backend field if ambiguous in edge cases. |

## Open Questions

1. **How should backend represent bulk watch mutation results?**
   - What we know: Partial and auth failures must be surfaced clearly. [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]
   - What's unclear: Exact response schema (`updated_count`, `failed_ids`, etc.) for consistent frontend UX.
   - Recommendation: Define explicit response envelope in plan wave 1 before frontend wiring.

2. **Where should "session-added rows first" state live?**
   - What we know: Requirement is specific to edit-session clarity in In pane.
   - What's unclear: whether client-local state is enough or needs backend ordering metadata.
   - Recommendation: Implement client-local session set first; persist-free unless UAT shows confusion.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | backend API/tests | ✓ | 3.13.1 | — |
| Node.js | frontend build/tests | ✓ | v23.10.0 | — |
| npm | frontend scripts | ✓ | 11.2.0 | — |
| Docker | integration/UAT env parity | ✓ | 28.3.3 | — |
| pytest | backend validation | ✓ | 8.4.1 | — |
| vitest | frontend validation | ✓ | 3.2.4 | — |

**Missing dependencies with no fallback:**
- None identified.

**Missing dependencies with fallback:**
- None identified.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 (backend), vitest 3.2.4 (frontend) |
| Config file | `backend/pyproject.toml`, `frontend/vitest.config.ts` |
| Quick run command | `cd backend && python3 -m pytest backend/tests/api/test_catalog_routes.py -q` |
| Full suite command | `cd backend && python3 -m pytest && cd ../frontend && npm test -- --run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Series detail and playlist-edit parity actions | frontend unit/component | `cd frontend && npm test -- SeriesDetailPage TwoPanePicker --run` | ✅ |
| INT-01 | Provider watch mutation dispatch/error handling | backend unit + integration | `cd backend && python3 -m pytest backend/tests/integrations/test_plex_client.py backend/tests/integrations/test_jellyfin_client.py -q` | ✅ (needs expansion) |
| INT-02 | Catalog-scoped series/episodes/resume correctness | backend API | `cd backend && python3 -m pytest backend/tests/api/test_catalog_routes.py -q` | ✅ |

### Sampling Rate
- **Per task commit:** targeted pytest/vitest for touched surfaces.
- **Per wave merge:** backend API+integration set plus frontend component tests.
- **Phase gate:** full backend + frontend suites green plus T-09 provider UAT checks.

### Wave 0 Gaps
- [ ] `backend/tests/api/test_catalog_watch_mutations.py` - endpoint contract for episode/season/series actions.
- [ ] `backend/tests/unit/test_watch_writeback_services.py` - provider adapter behavior and partial failures.
- [ ] `frontend/src/pages/SeriesDetailPage.watch-state.test.tsx` - grouped seasons + status badges + action outcomes.
- [ ] `frontend/src/components/playlists/PlaylistRowMenuItems.view-series.test.tsx` - new View series action.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing session/auth guards on API routes. [CITED: backend/src/wheeloffish/api/routes/playlists.py] |
| V3 Session Management | yes | Existing token-backed provider calls + unauthorized mapping. [CITED: backend/src/wheeloffish/integrations/plex/client.py] |
| V4 Access Control | yes | Owner-scoped playlist and catalog access checks. [CITED: backend/src/wheeloffish/api/routes/playlists.py] |
| V5 Input Validation | yes | FastAPI/Pydantic schema and route validation. [CITED: backend/src/wheeloffish/api/routes/catalog.py] |
| V6 Cryptography | no (phase-local) | No new crypto primitives in this phase. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Cross-user watch mutation attempt | Elevation of Privilege | Keep owner/session-scoped checks before provider dispatch. |
| Invalid composite IDs causing wrong-provider writes | Tampering | Parse/validate composite IDs and connection ownership prior to mutation. |
| Stale/expired provider credentials | Denial of Service | Map 401/403 to actionable UI errors and avoid false success. |

## Concrete Implementation Risks

1. **Plex season/series bulk uncertainty (MEDIUM):** season key behavior is assumed and must be UAT-verified before release signoff. [ASSUMED]
2. **Provider latency and eventual consistency (MEDIUM):** immediate refetch may briefly show old status after mutation; plan for retry/backoff UI state. [ASSUMED]
3. **Menu discoverability overload (LOW-MEDIUM):** adding View series + watch actions can crowd tile menus; keep action hierarchy clear (View first, destructive after separators). [ASSUMED]
4. **Cross-surface parity drift (MEDIUM):** Library/view/edit entry points can diverge unless all funnel to shared route and component composition. [CITED: frontend/src/App.tsx]

## Provider API Constraints for Watch-State Updates

- **Plex**
  - Uses `GET /:/scrobble` and `GET /:/unscrobble` with `identifier=com.plexapp.plugins.library` + `key=<ratingKey>`. [CITED: https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/]
  - Requires `ratingKey` (numeric/string metadata key), not GUID-based composite ID directly. [CITED: https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/]
  - Endpoint is practical/de-facto and tied to Plex ecosystem behavior rather than a strict stable public API contract. [CITED: .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/9-CONTEXT.md]

- **Jellyfin**
  - `POST /UserPlayedItems/{itemId}` marks played; optional `userId`/`datePlayed`. [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/Jellyfin.Api/Controllers/PlaystateController.cs]
  - `DELETE /UserPlayedItems/{itemId}` marks unplayed. [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/Jellyfin.Api/Controllers/PlaystateController.cs]
  - Folder recursion for series/season bulk writes is implemented in `Folder.MarkPlayed/MarkUnplayed`. [CITED: https://raw.githubusercontent.com/jellyfin/jellyfin/master/MediaBrowser.Controller/Entities/Folder.cs]

## Existing Code Patterns to Reuse

- `backend/src/wheeloffish/integrations/plex/playlists.py`: `resolve_episode_rating_key()` already handles Plex GUID-vs-ratingKey split.
- `backend/src/wheeloffish/api/routes/catalog.py`: existing scoped series/episodes/resume routes and provider error translation.
- `backend/src/wheeloffish/core/provider_writeback.py`: provider dispatch + partial/failure result handling conventions.
- `frontend/src/pages/SeriesDetailPage.tsx`: canonical series route and query orchestration.
- `frontend/src/components/playlists/PlaylistRowMenuItems.tsx`: existing row action menu extension point for adding "View series".
- `frontend/src/components/playlists/TwoPanePicker.tsx`: optimistic mutation + rollback and In/Available pane behavior for session-priority enhancement.

## Sources

### Primary (HIGH confidence)
- `https://raw.githubusercontent.com/jellyfin/jellyfin/master/Jellyfin.Api/Controllers/PlaystateController.cs` - playstate watched/unwatched endpoints.
- `https://raw.githubusercontent.com/jellyfin/jellyfin/master/MediaBrowser.Controller/Entities/Folder.cs` - recursive folder mark played/unplayed behavior.
- Repository source files in `backend/src/wheeloffish/...` and `frontend/src/...` listed above - current implementation constraints and reuse paths.

### Secondary (MEDIUM confidence)
- `https://www.plexopedia.com/plex-media-server/api/library/media-mark-watched/` - Plex scrobble endpoint syntax and usage.
- `https://www.plexopedia.com/plex-media-server/api/library/media-mark-unwatched/` - Plex unscrobble endpoint syntax and usage.

### Tertiary (LOW confidence)
- `https://developer.plex.tv/pms/` - provider-feature context that references scrobble capability generally, not this project's exact route usage.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - entirely based on in-repo stack and config files.
- Architecture: MEDIUM - grounded in current code paths, but exact endpoint/schema choices still discretionary.
- Pitfalls: MEDIUM - mostly verified by existing integration patterns, with one explicit Plex season-bulk assumption.

**Research date:** 2026-05-27
**Valid until:** 2026-06-26
