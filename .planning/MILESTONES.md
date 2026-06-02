# Milestones

## v0.1.0 feature-complete MVP (provider writeback) (Shipped: 2026-06-02)

**Phases completed:** 9 phases, 51 plans, 88 tasks

**Delivered:** Self-hosted TV playlist roulette with Plex/Jellyfin auth, nightly rebuild, provider writeback, Library UX, and series detail watch-state editing.

**Key accomplishments (curated):**

1. Dockerized FastAPI + React SPA with OAuth, catalog sync, and nightly orchestration
2. Deterministic playlist builder (ordered/disordered, completion policies, multipart adjacency)
3. Library-centric membership + two-pane playlist editor
4. Native Plex/Jellyfin playlist writeback after each rebuild
5. Series detail with season-grouped watch-state mutations from all playlist flows
6. Gap-closure passes closed UAT findings in Phases 6 and 9 without full re-plans

**Known deferred items at close:** 7 (see STATE.md Deferred Items). Backlog BL-03–BL-06 for v0.2.0.

**Full accomplishment log:**

**Key accomplishments:**

- 01-foundations-packaging
- 01-foundations-packaging
- 01-foundations-packaging
- 01-foundations-packaging
- 01-foundations-packaging
- Wave 0 domain primitives — composite IDs, ResumeService golden vectors, respx fixtures, and meta providers API
- Connections schema migration, per-user vault tokens, and REST CRUD with test-then-save validation
- Plex PIN OAuth connect flow and live PlexProvider listing TV libraries with stable guid-based composite IDs
- Jellyfin AuthenticateByName user linking and JellyfinProvider with identical Library/Series/Episode DTOs as Plex
- Chunked background catalog sync with cached series browse API, library scoping, and non-blocking sync triggers
- Live episode fetch and resume preview API with reusable ResumeService for Phase 4
- Phase 2 integration hardening: schema verified, CI green, operator docs and UAT checklist
- Env-synced connection boot plus Starlette session cookies with /auth/me admin and setup_mode gating
- Env-bound Plex/Jellyfin auth linking media accounts to boot-synced connection with session cookies and catalog admin library listing
- Vite+React operator shell with shadcn theme tokens, TanStack Query wiring, and FastAPI SPAStaticFiles served from Docker multi-stage build
- TanStack Query auth gate, provider-specific login wall, admin discovery copy panel, and read-only settings shell
- Admin checkbox library scoping with first-run checklist, settings editor, and role-based browse gating via LibraryScopeGuard
- Read-only series browser with TanStack infinite query, 300ms debounced search, grid/list layout toggle, and non-blocking sync banner
- Routed series detail with read-only resume preview, Enter-key browse navigation, Phase 3 operator docs, and manual UAT checklist
- Non-admin Plex users get working poster images and resume preview via admin-token fallback; resume uses cached ratingKey and parallel fetches
- Pydantic playlist config/build-result models with StrEnum row modes, completion policies, and shared golden-vector episode factories for Phase 4 builder waves
- Pure multipart helpers with D-07 forward-from-anchor and D-08 full-block expansion keyed by native multipart_group_id, proven by 10 golden vectors
- Series-complete detection via ResumeService with remove/restart/disordered RowBuildOutcome policies and per-playlist default_completion_policy hook
- ResumeService-driven ordered picker with multipart-forward blocks per slot, RESTART cursor reset, and position-based index advance for Wave 3 builder
- Last-15 exclusion disordered picker with Episode.last_viewed_at from Plex/Jellyfin mappers, multipart full-block expansion, and seeded random.Random determinism for Wave 3 builder
- Stateless PlaylistBuilder.build() orchestrates completion → slot allocation → ordered/disordered materialization with WILD/BALANCED/ROUND_ROBIN modes and 10 golden-vector proofs
- SQLAlchemy ORM models for playlists/series-rows/rebuild-runs, Alembic migration 008, and orm_to_playlist mapper with TDD green tests.
- APScheduler AsyncIOScheduler wired in FastAPI lifespan with install-timezone CronTrigger and is_due() cadence filter backed by 21 passing TDD tests.
- Live episode fetch + PlaylistBuilder wiring with per-row failure isolation, snapshot persistence, 3-run rolling history, and nightly batch sequencing backed by 6 passing TDD tests.
- FastAPI playlist CRUD with per-user ownership scoping, rebuild trigger (409 guard), snapshot detail, and 13 integration tests.
- Task 1: API types and usePlaylists hook
- Full playlist lifecycle UI — create/edit form with catalog series picker, detail page with output list, rebuild now with polling, and delete confirmation.
- Plex catalog sync now persists IMDb-like metadata (summary, genres, content rating, studio) into cached_series.provider_metadata; Jellyfin emits matching stub keys for frontend parity.
- Owner-scoped POST/DELETE/PATCH row endpoints let Library quick-add and the two-pane editor mutate playlist rows without full PUT replacement.
- Library nav rename with visible tile ⋯ menu, shared AddToPlaylistMenu (dropdown + context menu), quick-create dialog, and frontend hooks wired to row append API.
- Two-pane playlist editor with In/Available tile grids, bottom-sheet row settings, responsive mobile tabs, and optimistic row API mutations replacing SeriesPicker.
- Series detail page renders IMDb-like metadata hero from provider_metadata, primary Add to playlist via shared menu, and planning docs reflect cancelled global WheelOfFish scope.
- Fixed CR-01 blocker: playlist row DELETE/PATCH now encode composite Plex series IDs in URL paths, unblocking remove and row settings save in edit mode.
- Closed four Phase 6 UAT gaps: In-pane posters via API thumb_url, Advanced… in add menus, Library-style row context menus, and sticky playlist form Save/Cancel.
- Delivered migration-backed provider writeback primitives for Plex, including playlist CRUD/replace behavior and orchestrator integration after snapshot persistence.
- Extended provider writeback to cover Jellyfin so rebuild output can be pushed through the same phase-7 writeback path across supported providers.
- Completed provider-playlist lifecycle sync and surfaced writeback status in the SPA, then validated the v0.1.0 release gate via Phase 7 UAT.
- Recorded Phase 8 completion from already released polish and hardening work so GSD state matches shipped reality.
- Provider-level watched/unwatched mutation primitives now exist for Plex and Jellyfin using a typed shared contract plus adapter-specific endpoint routing.
- Catalog watch-state API now supports owner-scoped episode/season/series mutations with deterministic success/partial/failure envelopes for UI reconcile behavior.
- Playlist edit rows now deep-link into shared series detail while preserving return context, and newly-added rows are visually prioritized with a New marker.
- Series detail now groups episodes by season with watch-state affordances and provider-backed mutation actions using the catalog API reconcile strategy.
- UAT tests 1–3 are satisfied: playlist edit/view open shared series detail, back returns to the originating flow, and session-added rows stay on top without viewport jumps.
- Watch-state mutations now show a concise in-app progress banner that persists across navigation until the provider call completes.
- UAT test 6 is no longer skipped: API regression tests prove unauthenticated, provider-session, and cross-connection mutation paths fail deterministically.

---
