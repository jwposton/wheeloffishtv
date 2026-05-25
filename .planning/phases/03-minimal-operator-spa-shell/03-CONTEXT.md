# Phase 3: Minimal operator SPA shell - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Bootstrap the React/Vite SPA served from the same container as the FastAPI backend: media-server OAuth as the only app login, env-driven connection config, admin library scoping in UI, and a read-only series browser wired to Phase 2 catalog/resume APIs. No playlist CRUD, rebuild jobs, or WheelOfFish admin (Phases 4–6).

**In scope:** WEB-01 foundation — auth gate, connection config consumed from env, library scope UI, series browse (search, infinite scroll, detail with up-next preview), design system bootstrap, optional accessibility baseline for keyboard nav per ROADMAP.

**Out of scope:** Playlist mathematics/CRUD (Phase 4), scheduler/rebuild UI (Phase 5), WheelOfFish RBAC (Phase 6), full UX polish/motion/Lighthouse pass (Phase 7), server URL/provider editor in UI, standalone local username/password accounts, supporting Plex and Jellyfin simultaneously on one install.

</domain>

<decisions>
## Implementation Decisions

### Authentication & sessions
- **D-01:** **Media-server OAuth is the only app login** — no standalone local username/password accounts. If a user cannot authenticate against the configured Plex or Jellyfin server, they cannot use the app.
- **D-02:** **One provider per install** — operator sets `WOF_PROVIDER=plex` or `WOF_PROVIDER=jellyfin` in env at install time. Replaces Phase 2’s “both providers enabled” model for v1 UX simplicity.
- **D-03:** **Admin via env user ID** — `WOF_ADMIN_PROVIDER_USER_ID` matched against the provider user ID from OAuth. Primary admin identifier (stable for Apple/Google Plex sign-in); optional `WOF_ADMIN_USERNAME` may match username or email as convenience only, not primary.
- **D-04:** **Admin discovery flow** — fresh install may omit admin env var. First OAuth login shows a setup screen with the signed-in provider user ID (and username/email) to copy into `.env`; operator restarts container. Until admin env is set: **setup mode** — users may browse (when libraries scoped), but **no admin actions** (library scoping, etc.).
- **D-05:** **Session TTL** — `WOF_SESSION_DAYS` env optional; **unset = long-lived session cookie** (stay signed in across visits). When set, enforce that TTL.

### Connection config (env-only)
- **D-06:** **Connection config lives in env only** — provider, server base URL, SSL verify, display name, OAuth callback base, etc. Version-controlled and auditable outside the container. **No wizard or settings UI** to edit server URL/provider (avoids duplicate sources of truth).
- **D-07:** **DB mirrors env on boot** — on startup, upsert the single `connections` row from env so Phase 2 APIs and vault token storage continue to work. Runtime source of truth for connection *config* is always the env file; DB holds derived runtime state (tokens, cache, links).
- **D-08:** **Read-only connection display** — Settings may show “Connected to {url} (from configuration)” but not edit it. Changing server = edit `.env` + restart (document in README).

### Onboarding & library scope
- **D-09:** **Login wall only** — no server setup wizard. Operator configures env before `docker compose up`; users only see “Sign in with Plex/Jellyfin.”
- **D-10:** **Library scope in UI** — admin selects and maintains in-scope TV libraries via checkbox UI. Not env-only (exception to config-as-code: operational catalog policy).
- **D-11:** **First-run admin checklist + permanent settings** — on first admin login (after admin env set): forced “Pick libraries” step; thereafter **Settings → Libraries** for changes.
- **D-12:** **Non-admin holding page** — if admin has not scoped any libraries yet, non-admin users see a holding page (“Admin hasn’t finished setup”) rather than an empty browser.

### Series browser (read-only)
- **D-13:** **Layout** — poster **grid default** with **compact list toggle**; preference persisted (e.g. localStorage).
- **D-14:** **Paging & search** — **infinite scroll** against existing page-based API (`page`, `limit`, default 50). **Debounced title search** via `?q=` (case-insensitive substring match — not typo-tolerant fuzzy search).
- **D-15:** **Sync UX** — non-blocking **top banner** (“Updating library…”) while background sync runs; show **stale cached series** underneath (aligns with Phase 2 D-18).
- **D-16:** **Series detail** — drawer or detail page with metadata plus **up-next / resume preview** from `GET …/series/{id}/resume` (Phase 2 hybrid resume rule). Read-only — no add-to-playlist actions.

### Design system & frontend stack
- **D-17:** **Stack** — **Vite + React + TypeScript + Tailwind CSS + shadcn/ui (Radix primitives) + TanStack Query** for API state. Chosen for modern, responsive, accessible UI with low custom component churn.
- **D-18:** **Theming** — **light and dark mode from day one** — theme toggle plus `prefers-color-scheme` default.
- **D-19:** **Visual tone (Phase 3)** — **clean utilitarian** shell (neutral, functional). Design tokens / Tailwind theme variables so Phase 7 can shift to slicker/cinematic polish without rewrites.
- **D-20:** **Storybook** — **skip in Phase 3**; defer component catalog / visual regression stub to Phase 7 polish pass (ROADMAP listed it as optional).

### Claude's Discretion
- Exact env var names for connection fields (`WOF_PLEX_SERVER_URL` vs generic `WOF_MEDIA_SERVER_URL`), boot-time env→DB sync implementation, session cookie attributes (httpOnly, SameSite, secure behind proxy), SPA static file serving path in FastAPI/Docker, localStorage key for grid/list preference, debounce interval for search, detail drawer vs routed page — as long as decisions above and ROADMAP success criteria are met.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Product scope, “modern slick” UX goal, self-host constraints
- `.planning/REQUIREMENTS.md` — WEB-01 traceability (partial bootstrap in Phase 3)
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria (auth, browse, a11y keyboard nav)
- `.planning/research/SUMMARY.md` — Directional frontend stack (Vite/React/Radix/TanStack Query)

### Prior phase context (read for integration; Phase 3 overrides where noted below)
- `.planning/phases/01-foundations-packaging/01-CONTEXT.md` — Monorepo layout, same HTTP port for SPA + API, no in-repo reverse proxy
- `.planning/phases/02-media-ingestion-catalogs/02-CONTEXT.md` — Catalog API, OAuth, resume semantics, sync behavior (**Note:** Phase 3 D-02/D-06 override dual-provider and UI-editable connection assumptions)

### Phase 2 API surface (implementation reference)
- `backend/src/wheeloffish/api/routes/connections.py` — Connection CRUD (env-synced row; tokens via OAuth)
- `backend/src/wheeloffish/api/routes/oauth_plex.py` — Plex PIN OAuth flow
- `backend/src/wheeloffish/api/routes/oauth_jellyfin.py` — Jellyfin auth flow
- `backend/src/wheeloffish/api/routes/catalog.py` — Series browse (`page`, `q`), library scope admin routes, resume preview, sync status
- `backend/src/wheeloffish/api/deps.py` — Replace `STUB_APP_USER_ID` / stub `require_admin` with real session auth
- `backend/src/wheeloffish/core/config.py` — Existing env patterns (`WOF_OAUTH_CALLBACK_BASE`, `WOF_CATALOG_PAGE_DEFAULT`, etc.)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2 REST API under `/api/v1` — connections, OAuth callbacks, series browse with embedded sync status, library scope PUT, resume preview
- `SeriesBrowseResponse` with `page`, `limit`, `total`, `items`, `sync` — ready for TanStack Query infinite scroll
- `WOF_CATALOG_PAGE_DEFAULT` (50) — default page size for infinite scroll chunks
- `frontend/README.md` — placeholder only; greenfield Vite scaffold expected
- FastAPI `main.py` router registration pattern — extend with static SPA mount + auth/session routes

### Established Patterns
- Monorepo: `backend/` + `frontend/` + root `compose.yml` (Phase 1)
- Config via `.env` + compose environment; secrets/tokens in vault, never in images
- Composite series IDs `{connection_id}:{provider}:{native_id}` — use as route keys in UI
- Phase 2 non-blocking catalog sync — UI must not block on full library pull

### Integration Points
- Replace `get_app_user_id()` stub and `require_admin()` no-op in `api/deps.py` with session middleware tied to OAuth identity
- Boot hook: read connection env vars → upsert `connections` row before serving traffic
- OAuth login creates/updates `user_media_links` + vault per-user token (existing Phase 2 flow)
- Admin library scope: `PUT /api/v1/admin/connections/{id}/library-scope` (or equivalent admin route from Phase 2)
- Docker build: multi-stage or separate frontend build artifact copied into backend image for single-port serve

</code_context>

<specifics>
## Specific Ideas

- **Config-as-code:** Operator wants connection settings in version-controlled `.env`, not duplicated in UI — DB/env drift was explicitly rejected.
- **Apple Sign-In to Plex:** Admin must not rely on Plex username alone; provider user ID + first-login discovery screen is the operator-friendly path.
- **Library scope is the one UI-managed policy** — connection is env, scope is admin checkbox UI with first-run checklist.
- **Utilitarian now, slick later:** Phase 3 visual tone is functional; Phase 7 adjusts tokens/theme without architectural change (Tailwind + CSS variables).
- **Up-next on detail:** User expects detail view to show On Deck / resume episode for the signed-in user — matches Phase 2 `ResumeService` hybrid rule.

</specifics>

<deferred>
## Deferred Ideas

- **Hybrid env + UI connection config** — rejected; env-only for connection
- **Fuzzy/typo-tolerant search** — Phase 3 uses substring `ILIKE` only
- **Storybook / visual regression CI** — Phase 7 (ROADMAP optional stub)
- **Plex-inspired cinematic visual polish** — Phase 7
- **Grid/list toggle user account sync** — localStorage sufficient for Phase 3; server-persisted prefs optional later
- **Playlist CRUD, rebuild UI, WheelOfFish admin** — Phases 4–6 per roadmap
- **Dual Plex + Jellyfin on one install** — superseded by D-02 single-provider installs

</deferred>

---

*Phase: 3-Minimal operator SPA shell*
*Context gathered: 2026-05-25*
