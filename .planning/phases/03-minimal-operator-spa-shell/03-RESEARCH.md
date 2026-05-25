# Phase 3: Minimal operator SPA shell - Research

**Researched:** 2026-05-25
**Domain:** React/Vite SPA, FastAPI session auth, env-synced connection config, TanStack Query catalog UI, same-container static serve
**Confidence:** HIGH (stack + Phase 2 API integration), MEDIUM (OAuth/session refactor scope), HIGH (frontend patterns from official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** **Media-server OAuth is the only app login** — no standalone local username/password accounts. If a user cannot authenticate against the configured Plex or Jellyfin server, they cannot use the app.
- **D-02:** **One provider per install** — operator sets `WOF_PROVIDER=plex` or `WOF_PROVIDER=jellyfin` in env at install time. Replaces Phase 2’s “both providers enabled” model for v1 UX simplicity.
- **D-03:** **Admin via env user ID** — `WOF_ADMIN_PROVIDER_USER_ID` matched against the provider user ID from OAuth. Primary admin identifier (stable for Apple/Google Plex sign-in); optional `WOF_ADMIN_USERNAME` may match username or email as convenience only, not primary.
- **D-04:** **Admin discovery flow** — fresh install may omit admin env var. First OAuth login shows a setup screen with the signed-in provider user ID (and username/email) to copy into `.env`; operator restarts container. Until admin env is set: **setup mode** — users may browse (when libraries scoped), but **no admin actions** (library scoping, etc.).
- **D-05:** **Session TTL** — `WOF_SESSION_DAYS` env optional; **unset = long-lived session cookie** (stay signed in across visits). When set, enforce that TTL.
- **D-06:** **Connection config lives in env only** — provider, server base URL, SSL verify, display name, OAuth callback base, etc. Version-controlled and auditable outside the container. **No wizard or settings UI** to edit server URL/provider (avoids duplicate sources of truth).
- **D-07:** **DB mirrors env on boot** — on startup, upsert the single `connections` row from env so Phase 2 APIs and vault token storage continue to work. Runtime source of truth for connection *config* is always the env file; DB holds derived runtime state (tokens, cache, links).
- **D-08:** **Read-only connection display** — Settings may show “Connected to {url} (from configuration)” but not edit it. Changing server = edit `.env` + restart (document in README).
- **D-09:** **Login wall only** — no server setup wizard. Operator configures env before `docker compose up`; users only see “Sign in with Plex/Jellyfin.”
- **D-10:** **Library scope in UI** — admin selects and maintains in-scope TV libraries via checkbox UI. Not env-only (exception to config-as-code: operational catalog policy).
- **D-11:** **First-run admin checklist + permanent settings** — on first admin login (after admin env set): forced “Pick libraries” step; thereafter **Settings → Libraries** for changes.
- **D-12:** **Non-admin holding page** — if admin has not scoped any libraries yet, non-admin users see a holding page (“Admin hasn’t finished setup”) rather than an empty browser.
- **D-13:** **Layout** — poster **grid default** with **compact list toggle**; preference persisted (e.g. localStorage).
- **D-14:** **Paging & search** — **infinite scroll** against existing page-based API (`page`, `limit`, default 50). **Debounced title search** via `?q=` (case-insensitive substring match — not typo-tolerant fuzzy search).
- **D-15:** **Sync UX** — non-blocking **top banner** (“Updating library…”) while background sync runs; show **stale cached series** underneath (aligns with Phase 2 D-18).
- **D-16:** **Series detail** — drawer or detail page with metadata plus **up-next / resume preview** from `GET …/series/{id}/resume` (Phase 2 hybrid resume rule). Read-only — no add-to-playlist actions.
- **D-17:** **Stack** — **Vite + React + TypeScript + Tailwind CSS + shadcn/ui (Radix primitives) + TanStack Query** for API state. Chosen for modern, responsive, accessible UI with low custom component churn.
- **D-18:** **Theming** — **light and dark mode from day one** — theme toggle plus `prefers-color-scheme` default.
- **D-19:** **Visual tone (Phase 3)** — **clean utilitarian** shell (neutral, functional). Design tokens / Tailwind theme variables so Phase 7 can shift to slicker/cinematic polish without rewrites.
- **D-20:** **Storybook** — **skip in Phase 3**; defer component catalog / visual regression stub to Phase 7 polish pass (ROADMAP listed it as optional).

### Claude's Discretion
- Exact env var names for connection fields (`WOF_PLEX_SERVER_URL` vs generic `WOF_MEDIA_SERVER_URL`), boot-time env→DB sync implementation, session cookie attributes (httpOnly, SameSite, secure behind proxy), SPA static file serving path in FastAPI/Docker, localStorage key for grid/list preference, debounce interval for search, detail drawer vs routed page — as long as decisions above and ROADMAP success criteria are met.

### Deferred Ideas (OUT OF SCOPE)
- **Hybrid env + UI connection config** — rejected; env-only for connection
- **Fuzzy/typo-tolerant search** — Phase 3 uses substring `ILIKE` only
- **Storybook / visual regression CI** — Phase 7 (ROADMAP optional stub)
- **Plex-inspired cinematic visual polish** — Phase 7
- **Grid/list toggle user account sync** — localStorage sufficient for Phase 3; server-persisted prefs optional later
- **Playlist CRUD, rebuild UI, WheelOfFish admin** — Phases 4–6 per roadmap
- **Dual Plex + Jellyfin on one install** — superseded by D-02 single-provider installs
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEB-01 (partial) | SPA foundation: authentication gate, connection config consumed from env, library scope UI, read-only series browse with search/infinite scroll/detail+resume | Session middleware + `app_users` migration; env→DB boot sync; refactor OAuth to link users to env connection; TanStack Query infinite scroll against existing `SeriesBrowseResponse`; shadcn/ui shell with auth routes and admin gating |
</phase_requirements>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| App session auth (login wall) | API / Backend | Browser (redirect to OAuth) | Signed httpOnly cookie; SPA never stores tokens |
| Env→DB connection sync | API / Backend (lifespan boot hook) | — | Single source of truth in `.env`; DB row is derived |
| Plex PIN OAuth / Jellyfin auth | API routes (existing, refactored) | Browser popup/poll | Provider tokens stored in vault; not in SPA |
| Admin detection + setup mode | API / Backend (`require_admin`, `/auth/me`) | Frontend (setup screen copy) | Admin ID from env; UI displays provider user ID for operator |
| Library scope admin UI | Browser / Client | API `PUT /admin/…/library-scope` | Only UI-managed policy per D-10 |
| Series browse + search + infinite scroll | Browser / Client | API cached series endpoint | TanStack Query pages client-side; server paginates |
| Sync status banner | Browser / Client | API `sync` embed on browse response | Non-blocking UX per D-15 / Phase 2 D-18 |
| Series detail + resume preview | Browser / Client | API `GET …/resume` | Live provider fetch; read-only display |
| SPA static serve + client routing | API / Backend (`StaticFiles` mount) | Browser (React Router) | Same port per Phase 1 D-06; no in-repo reverse proxy |
| Theme (light/dark) | Browser / Client | — | CSS variables + `next-themes`; no server state |
| Design tokens / component library | Browser / Client | — | shadcn/ui + Tailwind; Phase 7 polish layer |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 3 is a **greenfield frontend** (`frontend/` is README-only) plus **backend auth/session wiring** to replace Phase 2 stubs in `api/deps.py`. The Phase 2 catalog API is already SPA-ready: `SeriesBrowseResponse` exposes `page`, `limit`, `total`, `items`, and embedded `sync` status; resume preview is at `GET /api/v1/connections/{id}/series/{series_id}/resume`. The main backend work is **not** new catalog logic — it is (1) **session-based app identity**, (2) **env-only connection boot sync**, and (3) **OAuth flows refactored** to link the signed-in media account to the pre-configured connection row instead of accepting server URL from the client.

**Auth model:** Use Starlette `SessionMiddleware` (built into FastAPI/Starlette) with `secret_key` derived from `WOF_SECRET_KEY`, storing `app_user_id` in `request.session` after OAuth completes. [CITED: starlette.io/middleware/#sessionmiddleware] Cookie is httpOnly by default; set `max_age` from `WOF_SESSION_DAYS` (unset → browser session / long-lived per D-05). Replace `STUB_APP_USER_ID` and no-op `require_admin()` with session lookup + env admin match (D-03). Add migration `003_app_users_sessions` with an `app_users` table keyed by `provider_user_id` (unique per install since D-02 single provider).

**Connection model change:** Phase 2 OAuth currently accepts `base_url` / `display_name` in request bodies and calls `create_connection()` which 409s if a row exists. Phase 3 inverts this: **lifespan boot hook** reads `WOF_PROVIDER`, `WOF_MEDIA_SERVER_URL`, `WOF_MEDIA_SERVER_DISPLAY_NAME`, `WOF_VERIFY_SSL` and **upserts** the single `connections` row (D-06, D-07). OAuth callback only creates/updates `app_users`, `user_media_links`, and vault token against that row. Deprecate or gate Phase 2 `POST /connections` for operator use.

**Frontend scaffold:** Vite + React + TS + Tailwind v4 + shadcn/ui + TanStack Query v5 + React Router v7. [CITED: ui.shadcn.com/docs/installation/vite] [CITED: tanstack.com/query/latest/docs/framework/react/guides/infinite-queries] Dev proxy `/api` → backend; production build copied into backend image and served via custom `SPAStaticFiles` mounted at `/` after all `/api` routes. [CITED: fastapi.tiangolo.com/tutorial/static-files/]

**Primary recommendation:** Ship vertical slices — (1) backend session + env boot sync + `/auth/me`, (2) Vite scaffold + login gate + Docker multi-stage build, (3) library scope admin UI, (4) series browser with infinite scroll/search/sync banner/detail+resume — reusing Phase 2 API shapes verbatim and generating TS types from OpenAPI where practical.

**ROADMAP drift note:** ROADMAP Phase 3 success criteria still mention “local account” and “wizard to paste server credentials.” CONTEXT D-01/D-06/D-09 **override** these — planner should follow CONTEXT, not stale ROADMAP wording.
</research_summary>

<standard_stack>
## Standard Stack

### Core — Frontend (new)
| Library | Version (verified 2026-05-25) | Purpose | Why Standard |
|---------|-------------------------------|---------|--------------|
| vite | 8.0.14 [ASSUMED: npm registry] | Dev server + production bundle | Project stack choice D-17; official React template |
| react | 19.2.6 [ASSUMED: npm registry] | UI runtime | Ecosystem default with Vite |
| typescript | 6.0.3 [ASSUMED: npm registry] | Type safety | Matches backend OpenAPI contracts |
| tailwindcss | 4.3.0 [ASSUMED: npm registry] | Utility styling + design tokens D-19 | shadcn/ui v4 path uses `@tailwindcss/vite` [CITED: ui.shadcn.com/docs/installation/vite] |
| @tanstack/react-query | 5.100.14 [ASSUMED: npm registry] | Server state, infinite scroll D-14 | Official infinite query API for page-based backends [CITED: tanstack.com/query/latest/docs/framework/react/guides/infinite-queries] |
| react-router-dom | 7.15.1 [ASSUMED: npm registry] | Client routing, auth gates | Standard for Vite SPAs; deep-link support needs backend SPA fallback |
| shadcn/ui + Radix | via CLI [ASSUMED] | Accessible primitives D-17, keyboard nav baseline | Radix focus management; copy-in components avoid churn |
| next-themes | 0.4.6 [ASSUMED: npm registry] | Light/dark D-18 | Pairs with shadcn theme toggle; respects `prefers-color-scheme` |
| lucide-react | 1.16.0 [ASSUMED: npm registry] | Icons | shadcn default icon set |

### Core — Backend (extend existing)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | ≥0.115 (installed) | API + static mount | Phase 1 baseline |
| starlette SessionMiddleware | via FastAPI | Signed session cookie | httpOnly cookie sessions [CITED: starlette.io/middleware/#sessionmiddleware] |
| itsdangerous | 2.2.0 (transitive) | Session signing | Starlette session dependency |
| SQLAlchemy + Alembic | ≥2.0 / ≥1.13 | `app_users` table | Existing migration pattern |

### Dev / test — Frontend
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | latest stable [ASSUMED] | Unit/component tests | Nyquist per-task sampling |
| @testing-library/react | latest stable [ASSUMED] | Component behavior | Auth gate, browser UI |
| msw | latest stable [ASSUMED] | API mocking in tests | Mock `/api/v1/*` without live backend |
| @playwright/test | latest stable [ASSUMED] | Optional smoke e2e | Manual gate only if Wave 0 budget tight |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SessionMiddleware + cookie | JWT in localStorage | XSS token theft; rejected for operator SPA |
| OpenAPI codegen (openapi-typescript) | Hand-written TS types | Codegen reduces drift; hand types OK for MVP if small surface |
| Drawer for series detail | Routed `/series/:id` page | Both meet D-16; routed page better for keyboard/a11y deep links |
| `@tanstack/react-query` debounce option | Debounce value before queryKey | Built-in debounce not shipped; debounce input in queryKey per TanStack guidance [CITED: github.com/TanStack/query/discussions/3132] |

**Installation (frontend bootstrap):**
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss @tailwindcss/vite @tanstack/react-query react-router-dom next-themes lucide-react
npx shadcn@latest init
```

**Docker multi-stage pattern:**
```dockerfile
# stage: frontend-build (node:22-alpine)
# RUN npm ci && npm run build  →  dist/

# stage: runtime (existing python slim)
# COPY --from=frontend-build /frontend/dist /app/static/spa
```

**Version verification:** npm view confirmed 2026-05-25. slopcheck unavailable in sandbox — all npm packages tagged `[ASSUMED]`; planner must human-verify before install.
</standard_stack>

## Package Legitimacy Audit

> slopcheck install failed in research environment (PATH not updated after pip install). All packages tagged `[ASSUMED]`.

| Package | Registry | slopcheck | Disposition |
|---------|----------|-----------|-------------|
| vite | npm | unavailable | `[ASSUMED]` — checkpoint before install |
| react | npm | unavailable | `[ASSUMED]` |
| @tanstack/react-query | npm | unavailable | `[ASSUMED]` |
| tailwindcss | npm | unavailable | `[ASSUMED]` |
| react-router-dom | npm | unavailable | `[ASSUMED]` |
| next-themes | npm | unavailable | `[ASSUMED]` |
| vitest | npm | unavailable | `[ASSUMED]` |

**Packages removed due to slopcheck [SLOP] verdict:** none (slopcheck not run)
**Packages flagged as suspicious [SUS]:** none

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory found in repository — no additional project-specific agent directives beyond user rules and GSD CONTEXT.

<implementation_patterns>
## Implementation Patterns

### System Architecture Diagram

```
Operator .env (WOF_PROVIDER, WOF_MEDIA_SERVER_URL, WOF_ADMIN_*)
        │
        ▼ boot upsert
┌───────────────────────────────────────────────────────────────┐
│ FastAPI (single port :8000)                                    │
│  SessionMiddleware → app_user_id in signed cookie              │
│  /api/v1/auth/*  /oauth/*  /catalog/*  /admin/*               │
│  SPAStaticFiles("/") → frontend/dist (index.html fallback)     │
└───────────────┬───────────────────────────────┬───────────────┘
                │                               │
                ▼                               ▼
         SQLite (connections,            Browser SPA
          app_users, cached_*,           React Router + TanStack Query
          user_media_links, vault)       grid/list browse, admin settings
                │
                ▼ httpx (per-user token)
         Plex PMS / Jellyfin (operator server)
```

### Recommended Project Structure

```
frontend/
├── index.html
├── vite.config.ts              # @ alias, /api dev proxy, base: "/"
├── src/
│   ├── main.tsx                # QueryClientProvider, Router, ThemeProvider
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts           # fetch wrapper, credentials: 'include'
│   │   └── types.ts            # SeriesBrowseResponse, AuthMe, etc.
│   ├── components/
│   │   ├── ui/                 # shadcn generated
│   │   ├── layout/             # AppShell, SyncBanner, ThemeToggle
│   │   ├── auth/               # LoginWall, AdminSetupPanel
│   │   └── browse/             # SeriesGrid, SeriesList, SeriesDetail
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useDebouncedValue.ts
│   │   └── useSeriesInfiniteQuery.ts
│   ├── pages/
│   │   LoginPage.tsx
│   │   BrowsePage.tsx
│   │   SettingsPage.tsx
│   │   AdminLibrarySetupPage.tsx
│   │   HoldingPage.tsx
│   └── routes/
│       ProtectedRoute.tsx
│       AdminRoute.tsx

backend/src/wheeloffish/
├── api/
│   ├── deps.py                 # get_current_user, require_admin, require_session
│   ├── routes/
│   │   ├── auth.py             # GET /auth/me, POST /auth/logout
│   │   └── spa.py              # SPAStaticFiles helper (optional module)
├── core/
│   ├── boot.py                 # sync_connection_from_env()
│   └── auth.py                 # admin check, setup mode, app_user upsert
├── db/models/
│   └── app_user.py             # migration 003
```

### Pattern 1: Env→DB connection boot sync (D-06, D-07)

**What:** On application startup (lifespan), read env and upsert exactly one `connections` row matching `WOF_PROVIDER`.

**Recommended env names:**
```
WOF_PROVIDER=plex|jellyfin
WOF_MEDIA_SERVER_URL=https://plex.example.com:32400
WOF_MEDIA_SERVER_DISPLAY_NAME=Home Plex
WOF_VERIFY_SSL=true
WOF_OAUTH_CALLBACK_BASE=https://wof.example.com
WOF_ADMIN_PROVIDER_USER_ID=          # optional until configured
WOF_ADMIN_USERNAME=                  # optional convenience match
WOF_SESSION_DAYS=                    # optional; unset = long-lived
```

**When:** Every container start; idempotent upsert by `provider_type`.

```python
# core/boot.py — pattern sketch
def sync_connection_from_env(db: Session, settings: Settings) -> Connection:
    provider = settings.WOF_PROVIDER  # new setting; replaces dual-provider gate for UX
    row = db.query(Connection).filter(Connection.provider_type == provider).one_or_none()
    if row is None:
        row = Connection(id=str(uuid.uuid4()), provider_type=provider, ...)
        db.add(row)
    row.base_url = settings.WOF_MEDIA_SERVER_URL
    row.display_name = settings.WOF_MEDIA_SERVER_DISPLAY_NAME
    row.verify_ssl = settings.WOF_VERIFY_SSL
    db.commit()
    return row
```

Replace `WOF_ENABLED_PROVIDERS` checks in OAuth routes with single `WOF_PROVIDER` match (D-02).

### Pattern 2: Session auth replacing stubs

**What:** Starlette `SessionMiddleware` + `app_users` table; session stores `app_user_id` only (not media tokens).

```python
# main.py — middleware order: SessionMiddleware before routes
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,  # derive from WOF_SECRET_KEY bytes
    max_age=settings.session_max_age_seconds,  # None if WOF_SESSION_DAYS unset
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production",  # discretion
)

# deps.py
def get_current_user(request: Request, db: Session = Depends(get_db)) -> AppUser:
    app_user_id = request.session.get("app_user_id")
    if not app_user_id:
        raise HTTPException(401, detail={"code": "unauthenticated"})
    ...
```

**`/api/v1/auth/me` response shape (suggested):**
```json
{
  "app_user_id": "uuid",
  "provider_user_id": "12345",
  "provider_username": "operator@icloud.com",
  "is_admin": false,
  "setup_mode": true,
  "connection": { "id": "uuid", "provider": "plex", "display_name": "...", "base_url": "..." },
  "has_media_link": true,
  "libraries_scoped": false
}
```

Frontend uses `setup_mode` + `is_admin` for admin discovery screen (D-04) and library setup gate (D-11, D-12).

### Pattern 3: OAuth refactor (link user, not create connection)

**Plex (changes from Phase 2):**
- `POST /connections/plex/oauth/start` — **no client-supplied base_url**; read connection from DB; store `app_user_id` in pin state only if session exists, or create anonymous pin then bind on callback after session established
- `GET /connections/plex/oauth/callback` — validate token, upsert `app_user`, upsert `user_media_link` + vault token against env connection row, set session cookie, redirect to SPA `/` or `/setup`

**Jellyfin:**
- Replace body `{ base_url, display_name, ... }` with `{ username, password }` only; server URL from env connection row
- Same link-user flow as Plex post-auth

**SPA login UX:**
- Plex: open `auth_url` in same window or popup; poll `/status/{pin_id}` or follow redirect callback
- Jellyfin: inline username/password form posting to `/connections/jellyfin/auth` with session cookie

### Pattern 4: SPA static serve + client routing

Mount API routers first, then SPA last:

```python
# Source: FastAPI StaticFiles + community SPA fallback pattern
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise ex

app.mount("/", SPAStaticFiles(directory=settings.SPA_DIST_DIR, html=True), name="spa")
```

Vite `base: "/"` so asset paths work at root. [CITED: vite.dev/guide/build.html]

### Pattern 5: TanStack Query infinite scroll + debounced search (D-14)

```tsx
// Source: tanstack.com/query/latest/docs/framework/react/guides/infinite-queries
// Source: github.com/TanStack/query/discussions/3132 (debounce queryKey input)
const debouncedQ = useDebouncedValue(searchInput, 300)

const seriesQuery = useInfiniteQuery({
  queryKey: ['series', connectionId, debouncedQ],
  initialPageParam: 1,
  queryFn: ({ pageParam }) =>
    api.getSeries(connectionId, { page: pageParam, limit: 50, q: debouncedQ || undefined }),
  getNextPageParam: (lastPage) =>
    lastPage.page * lastPage.limit < lastPage.total ? lastPage.page + 1 : undefined,
})

// Infinite scroll trigger
useEffect(() => {
  if (inView && seriesQuery.hasNextPage && !seriesQuery.isFetchingNextPage) {
    seriesQuery.fetchNextPage()
  }
}, [inView, seriesQuery.hasNextPage, seriesQuery.isFetchingNextPage])
```

Show `lastPage.sync.status === 'running'` in top `SyncBanner` (D-15). Poll `sync` refetch interval (e.g. 3s) while running.

### Pattern 6: Library scope admin UI (D-10, D-11)

1. `GET /connections/{id}/libraries` — list all cached libraries (extend Phase 2 to return `in_scope` flag on each `Library` DTO if not already exposed)
2. Admin checkbox list → `PUT /admin/connections/{id}/library-scope` with `{ in_scope_library_native_ids: [...] }`
3. First admin login when `libraries_scoped === false` → route guard to `/setup/libraries` before `/browse`
4. Non-admin + zero scoped libraries → `HoldingPage` (D-12)

### Pattern 7: Theming (D-18, D-19)

shadcn init with CSS variables in `src/index.css`; wrap app in `ThemeProvider` from `next-themes` with `defaultTheme="system"`. Utilitarian neutral palette — defer cinematic tokens to Phase 7.

### Anti-Patterns to Avoid
- **Accepting server URL from SPA** — violates D-06; enables config drift
- **Storing Plex/Jellyfin tokens in localStorage** — use vault + httpOnly session only
- **Debouncing queryFn instead of queryKey** — creates orphan cache entries [CITED: github.com/TanStack/query/discussions/3132]
- **Mounting StaticFiles at `/` before API routes** — shadows `/api/*` [CITED: fastapi.tiangolo.com/tutorial/static-files/]
- **Using Phase 2 `POST /connections` in operator flow** — bypasses env-only config
- **Blocking browse until sync completes** — violates D-15 / Phase 2 D-18
</implementation_patterns>

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accessible dialogs/menus/checkboxes | Custom focus-trapped modals | shadcn/ui (Radix) | Focus management, ARIA, keyboard nav |
| Server state caching/refetch | Manual useEffect fetch | TanStack Query | Pagination, stale-while-revalidate, sync polling |
| Session signing | Custom cookie crypto | Starlette SessionMiddleware | httpOnly, signed, battle-tested |
| Dark/light mode | CSS class toggling alone | next-themes + CSS variables | system preference + persistence |
| OpenAPI type sync | Copy-paste DTOs forever | openapi-typescript (optional) | Reduces frontend/backend drift |
| Infinite scroll state | Manual page counter | useInfiniteQuery | Correct merge/refetch semantics |

**Key insight:** Phase 3 value is wiring existing Phase 2 APIs into a usable operator shell — custom auth UI components or fetch caches will slow delivery without differentiation.

<risks_and_mitigations>
## Risks and Mitigations

### Risk 1: Phase 2 OAuth assumes client-supplied connection fields
**What goes wrong:** Current `PlexOAuthStartRequest` and `JellyfinAuthRequest` include `base_url` / `display_name`; `create_connection()` 409s on duplicate provider.
**Mitigation:** Add `link_media_user()` core function that upserts `user_media_link` against boot-synced connection; refactor OAuth routes; gate legacy `POST /connections` to admin-only or remove from OpenAPI.
**Warning signs:** OAuth succeeds but wrong server URL stored; 409 on login.

### Risk 2: Session secret coupling with WOF_SECRET_KEY
**What goes wrong:** `WOF_SECRET_KEY` is 64 hex chars (32 bytes) — valid for itsdangerous; rotating key invalidates all sessions and vault (Fernet).
**Mitigation:** Document that rotating `WOF_SECRET_KEY` logs everyone out and requires re-linking media tokens; consider separate `WOF_SESSION_SECRET` in discretion if rotation policies diverge later.
**Warning signs:** Mass 401 after env edit.

### Risk 3: SPA routing 404 on refresh
**What goes wrong:** Direct navigation to `/browse` returns 404 without index.html fallback.
**Mitigation:** `SPAStaticFiles` 404→index.html pattern; register mount last; add smoke test fetching `/browse` returns 200 HTML.
**Warning signs:** Refresh on deep link fails in production only.

### Risk 4: Docker build size/complexity
**What goes wrong:** Adding Node build stage increases CI time and cache invalidation.
**Mitigation:** Multi-stage with npm ci cache mount; copy only `dist/` to runtime image; keep frontend `package-lock.json` committed.
**Warning signs:** Image build >5 min on clean CI.

### Risk 5: Admin setup friction (Apple Sign-In Plex)
**What goes wrong:** Operator copies username instead of provider user ID; admin gate fails silently.
**Mitigation:** Setup screen prominently displays `provider_user_id` with copy button; README documents restart-after-env; optional username match as secondary (D-03).
**Warning signs:** Admin cannot access library scope despite "being admin."

### Risk 6: Jellyfin is not OAuth — credential form UX
**What goes wrong:** Users expect "Sign in with Jellyfin" OAuth redirect; instead need username/password form.
**Mitigation:** Clear copy on login page; POST over HTTPS only; never log passwords; same session cookie on success.
**Warning signs:** UAT confusion on Jellyfin installs.

### Risk 7: CORS/credentials in dev vs prod
**What goes wrong:** Dev Vite on :5173 calling :8000 needs CORS + credentials; prod same-origin does not.
**Mitigation:** Vite dev proxy `/api` → backend (same-origin from browser perspective); production same-container serve eliminates CORS.
**Warning signs:** 401 on API calls only in dev.

### Risk 8: ROADMAP vs CONTEXT success criteria mismatch
**What goes wrong:** Planner implements local accounts or connection wizard per ROADMAP.
**Mitigation:** Treat CONTEXT D-01/D-06/D-09 as authoritative; update ROADMAP during transition.
**Warning signs:** Settings UI allows editing server URL.

### Risk 9: Keyboard navigation baseline
**What goes wrong:** Grid tiles not focusable; drawer trap broken.
**Mitigation:** Use shadcn Button/Sheet with Radix; ensure series cards are `<button>` or `tabIndex=0`; visible focus rings; manual keyboard UAT checklist.
**Warning signs:** Tab order skips browse items.

### Risk 10: Open libraries endpoint missing in_scope
**What goes wrong:** Admin UI cannot show current scope without extra API.
**Mitigation:** Verify `GET /libraries` returns all libraries with `in_scope` boolean; extend DTO if Phase 2 only returns scoped set.
**Warning signs:** Checkboxes don't reflect DB state.
</risks_and_mitigations>

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend framework | pytest ≥8 + pytest-asyncio (existing) |
| Backend config | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Backend quick run | `cd backend && uv run pytest tests/unit -q` |
| Backend full suite | `cd backend && uv run ruff check . && uv run pytest` |
| Frontend framework | vitest + @testing-library/react [ASSUMED — Wave 0] |
| Frontend config | `frontend/vitest.config.ts` (Wave 0) |
| Frontend quick run | `cd frontend && npm run test -- --run` |
| Frontend full suite | `cd frontend && npm run test -- --run && npm run build` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Unauthenticated `/auth/me` → 401 | backend integration | `uv run pytest tests/api/test_auth_routes.py -k unauthenticated -x` | ❌ Wave 0 |
| WEB-01 | Session cookie set on OAuth callback | backend integration | `uv run pytest tests/api/test_auth_routes.py -k session_cookie -x` | ❌ Wave 0 |
| WEB-01 | `require_admin` returns 403 for non-admin | backend integration | `uv run pytest tests/api/test_auth_routes.py -k require_admin -x` | ❌ Wave 0 |
| WEB-01 | Boot sync upserts connection from env | backend unit | `uv run pytest tests/unit/test_boot_sync.py -x` | ❌ Wave 0 |
| WEB-01 | Setup mode allows browse, blocks admin PUT | backend integration | `uv run pytest tests/api/test_catalog_routes.py -k setup_mode -x` | ❌ Wave 0 |
| WEB-01 | SPA index served at `/` | backend integration | `uv run pytest tests/api/test_spa_routes.py -k index -x` | ❌ Wave 0 |
| WEB-01 | SPA fallback for `/browse` | backend integration | `uv run pytest tests/api/test_spa_routes.py -k fallback -x` | ❌ Wave 0 |
| WEB-01 | Login wall redirects unauthenticated users | frontend component | `npm run test -- --run src/routes/ProtectedRoute.test.tsx` | ❌ Wave 0 |
| WEB-01 | Infinite query fetches next page | frontend unit | `npm run test -- --run src/hooks/useSeriesInfiniteQuery.test.ts` | ❌ Wave 0 |
| WEB-01 | Debounced search resets pages | frontend unit | `npm run test -- --run src/hooks/useDebouncedValue.test.ts` | ❌ Wave 0 |
| WEB-01 | Sync banner shown when sync.status=running | frontend component | `npm run test -- --run src/components/SyncBanner.test.tsx` | ❌ Wave 0 |
| WEB-01 | Grid/list preference persists localStorage | frontend unit | `npm run test -- --run src/hooks/useBrowseLayout.test.ts` | ❌ Wave 0 |
| WEB-01 | Keyboard: series grid items focusable | manual UAT | Tab through browse grid; Enter opens detail | manual |
| WEB-01 | Admin library scope checkbox saves | manual UAT | Admin toggles library → refresh → scope persists | manual |

### Sampling Rate
- **Per task commit:** backend `uv run pytest tests/unit -q` OR frontend `npm run test -- --run` (whichever changed)
- **Per wave merge:** full backend pytest + frontend vitest + `npm run build`
- **Phase gate:** Full suites green + manual keyboard/browse UAT before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Migration `003_app_users.py` + `AppUser` model
- [ ] `core/boot.py` env→DB sync + unit tests
- [ ] `api/routes/auth.py` + session middleware wiring
- [ ] Refactor `oauth_plex.py` / `oauth_jellyfin.py` for env connection
- [ ] `SPAStaticFiles` mount + `tests/api/test_spa_routes.py`
- [ ] `frontend/` Vite scaffold + shadcn init + vitest config
- [ ] Docker multi-stage frontend build in `backend/Dockerfile`
- [ ] Update `.env.example` with Phase 3 vars
- [ ] Extend `Library` DTO with `in_scope` if missing for admin UI

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Media-server OAuth / Jellyfin auth only; session cookie |
| V3 Session Management | yes | Starlette SessionMiddleware; httpOnly; TTL via `WOF_SESSION_DAYS` |
| V4 Access Control | yes | `require_admin` env provider ID; setup mode gating |
| V5 Input Validation | yes | Pydantic on API; React form validation for Jellyfin creds |
| V6 Cryptography | yes | Existing Fernet vault; session signed with server secret |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS stealing session | Spoofing | httpOnly session cookie; no tokens in JS |
| CSRF on state-changing API | Tampering | SameSite=Lax cookie; same-origin SPA |
| Non-admin library scope mutation | Elevation | `require_admin` + setup mode check |
| Jellyfin password in logs | Information disclosure | Never log request bodies for auth routes |
| SSL stripping behind proxy | Spoofing | Operator HTTPS via external proxy; `https_only` cookie in prod |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | frontend build | ✓ | v23.10.0 | Required — no fallback |
| npm | frontend package install | ✓ | 11.2.0 | — |
| Python | backend | ✓ | 3.12 (Docker) | — |
| Docker | production serve | ✓ | (host) | — |
| ctx7 CLI | doc lookup | ✗ | — | WebFetch official docs used |
| slopcheck | package audit | ✗ | — | All npm packages `[ASSUMED]` |

**Missing dependencies with no fallback:**
- Node.js + npm for frontend scaffold and Docker build stage

## Code Examples

### Infinite scroll with page-based API
```tsx
// Source: https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries
const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
  queryKey: ['series', connectionId, debouncedQ],
  queryFn: ({ pageParam }) => api.getSeries(connectionId, { page: pageParam, q: debouncedQ }),
  initialPageParam: 1,
  getNextPageParam: (last) =>
    last.page * last.limit < last.total ? last.page + 1 : undefined,
})
```

### Session middleware
```python
# Source: https://www.starlette.io/middleware/#sessionmiddleware
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")
```

### SPA fallback static files
```python
# Source: https://fastapi.tiangolo.com/tutorial/static-files/ + SPA fallback community pattern
app.mount("/", SPAStaticFiles(directory="static/spa", html=True), name="spa")
```

## State of the Art

| Old Approach (Phase 2) | Current Approach (Phase 3) | Impact |
|------------------------|----------------------------|--------|
| `STUB_APP_USER_ID` in deps | Session cookie + `app_users` table | Real multi-user identity |
| Client POST connection config | Env boot sync only | Config-as-code D-06 |
| `WOF_ENABLED_PROVIDERS=plex,jellyfin` | `WOF_PROVIDER=plex` OR `jellyfin` | Single-provider installs D-02 |
| JSON root at `/` | React SPA at `/` | Operator UI live |
| No frontend tests | vitest + Testing Library | Nyquist validation |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `GET /libraries` must expose `in_scope` for all libraries | Pattern 6 | Admin checkbox UI needs extra endpoint work |
| A2 | `WOF_SECRET_KEY` bytes suitable for SessionMiddleware signing | Pattern 2 | May need dedicated session secret |
| A3 | Vite 8 + Tailwind 4 + shadcn current CLI flags stable | Standard Stack | Init command drift; pin versions in lockfile |
| A4 | React Router 7 API compatible with standard `<BrowserRouter>` patterns | Standard Stack | Route API changes require doc check at init |
| A5 | Phase 2 catalog series route works without auth today | Integration | Must add session requirement without breaking tests |

## Open Questions (RESOLVED)

1. **Does `Library` DTO expose `in_scope` today?** *(RESOLVED — Plan 02)*
   - **Decision:** Extend `Library` DTO with `in_scope: bool`; add `GET /admin/connections/{id}/libraries` returning all libraries with scope flags for admin checkbox UI (Plan 02 Task 2).

2. **Plex OAuth start before session exists?** *(RESOLVED — Plan 01 + 04)*
   - **Decision:** `POST /api/v1/auth/bootstrap-session` creates provisional `AppUser` + session cookie; LoginPage calls it on mount before `POST /connections/plex/oauth/start` (Plan 01 Task 2, Plan 04 Task 2). OAuth callback upserts real `provider_user_id`.

3. **Keep `POST /connections` for API completeness?** *(RESOLVED — Plan 02)*
   - **Decision:** Return 403 with code `env_config_only` for operator POST; env boot sync is sole write path (D-06). Document in README (Plan 07).

## Sources

### Primary (HIGH confidence)
- [Starlette SessionMiddleware](https://www.starlette.io/middleware/#sessionmiddleware) — cookie attributes, httpOnly, max_age
- [FastAPI StaticFiles](https://fastapi.tiangolo.com/tutorial/static-files/) — mount semantics
- [TanStack Query Infinite Queries](https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries) — useInfiniteQuery pagination
- [shadcn/ui Vite installation](https://ui.shadcn.com/docs/installation/vite) — Tailwind v4 + alias setup
- [Vite production build](https://vite.dev/guide/build.html) — dist output, base path
- Phase 3 `03-CONTEXT.md` — locked decisions
- Existing codebase — `catalog.py`, `deps.py`, `oauth_plex.py`, `main.py`, `compose.yml`

### Secondary (MEDIUM confidence)
- [TanStack Query debounce discussion #3132](https://github.com/TanStack/query/discussions/3132) — debounce queryKey not queryFn
- SPA fallback patterns (Stack Overflow / community) — mount order + 404→index.html

### Tertiary (validate during implementation)
- Exact shadcn CLI init flags for Tailwind v4 — verify at scaffold time
- `Library.in_scope` field availability — verify in Phase 2 DTO mappers

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — npm versions verified; slopcheck unavailable; shadcn CLI evolves
- Architecture: HIGH — clear split between env config, session auth, existing catalog API
- Pitfalls: HIGH — Phase 2 OAuth/connection coupling is concrete code debt

**Research date:** 2026-05-25
**Valid until:** 2026-06-25

---

## RESEARCH COMPLETE
