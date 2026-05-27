# Wheel of Fish TV

Self-hosted Dockerized Plex/Jellyfin random TV playlist builder. Users connect a media server, configure playlists with ordered or disordered show rows, and get daily rebuilt episode lists.

## License

MIT — see [LICENSE](LICENSE). Release notes: [CHANGELOG.md](CHANGELOG.md).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

## Quickstart

1. Copy the environment template and generate a secret key:

   ```bash
   cp .env.example .env
   openssl rand -hex 32
   ```

2. Paste the generated value into `.env` as `WOF_SECRET_KEY`.

3. Start the stack and wait for the healthcheck:

   ```bash
   docker compose up --wait --build
   ```

4. Verify the container is healthy:

   ```bash
   docker compose ps
   ```

   The `app` service should show `healthy`.

5. Open the app (default `http://localhost:8000`), sign in with Plex or Jellyfin, and use **Settings → Libraries** if you want to limit which TV libraries appear in Browse. On first link, all TV libraries from your account are in scope by default.

### First run (browser)

| Step | What happens |
|------|----------------|
| 1 | Operator sets `.env` (`WOF_SECRET_KEY`, `WOF_PROVIDER`, `WOF_MEDIA_SERVER_URL`, `WOF_OAUTH_CALLBACK_BASE`) and starts the stack |
| 2 | User opens the app and completes Plex PIN OAuth or Jellyfin login |
| 3 | App redirects to **Library**; background catalog sync runs if needed |
| 4 | Optional: **Settings → Libraries** narrows in-scope TV libraries (per signed-in user) |
| 5 | User creates playlists, adds shows from Library, triggers rebuilds; playlists sync to Plex/Jellyfin as `{name} [WoF]` |

There is **no** admin env var, setup wizard, or “wait for operator” holding page. Media server URL and provider stay in `.env`; library visibility is per user in the UI.

### Upgrading from older installs

If your `.env` still has `WOF_ADMIN_PROVIDER_USER_ID` or `WOF_ADMIN_USERNAME`, you can remove them — they are ignored. Library scope is stored per user in the database. Use **Settings → Libraries** instead of the removed `/setup/admin` flow.

API clients should use `PUT /api/v1/connections/{id}/library-scope` (not `/api/v1/admin/...`). `GET /api/v1/auth/me` returns `has_media_link` and `libraries_scoped` only (no `is_admin` or `setup_mode`).

## Release deployment (pre-built image)

Published multi-arch images (`linux/amd64`, `linux/arm64`) are on GitHub Container Registry:

```text
ghcr.io/jwposton/wheeloffishtv:0.1.5
ghcr.io/jwposton/wheeloffishtv:latest
```

No git clone or local build required:

```bash
curl -O https://raw.githubusercontent.com/jwposton/wheeloffishtv/main/compose.release.yml
curl -O https://raw.githubusercontent.com/jwposton/wheeloffishtv/main/.env.example
cp .env.example .env
# edit .env, then:
docker compose -f compose.release.yml pull
docker compose -f compose.release.yml up -d
```

Images are built automatically when a `v*` tag is pushed (see `.github/workflows/publish-image.yml`). After the first publish, set the package to **Public** under GitHub → Packages if pulls fail with “denied”.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WOF_SECRET_KEY` | Yes | — | 64-char hex key from `openssl rand -hex 32`; encrypts stored secrets |
| `WOF_PROVIDER` | Yes | `plex` | Media provider for this install: `plex` or `jellyfin` |
| `WOF_MEDIA_SERVER_URL` | Yes | — | Media server base URL (no trailing slash) |
| `WOF_MEDIA_SERVER_DISPLAY_NAME` | No | `Media Server` | Display name in Settings |
| `WOF_VERIFY_SSL` | No | `true` | Verify TLS when connecting to media server |
| `WOF_OAUTH_CALLBACK_BASE` | No | `http://localhost:8000` | Base URL for OAuth callback redirects |
| `WOF_SESSION_DAYS` | No | — | Session cookie TTL in days; unset = long-lived |
| `DATABASE_URL` | No | `sqlite:////data/wheeloffish.db` | SQLAlchemy database URL |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `LOG_FORMAT` | No | `json` | `json` for production; `console` for local dev |
| `ENVIRONMENT` | No | `production` | Environment label in logs and health |
| `PUID` | No | `1000` | UID for `/data` and the app process (entrypoint remaps on start) |
| `PGID` | No | `1000` | GID for `/data` and the app process |
| `WOF_ENABLED_PROVIDERS` | No | `plex,jellyfin` | **Deprecated for operators** — use `WOF_PROVIDER` instead; retained for multi-provider test fixtures |
| `WOF_PLEX_PRODUCT_NAME` | No | `Wheel of Fish TV` | Product name shown during Plex PIN flow |
| `WOF_CATALOG_SYNC_CHUNK_SIZE` | No | `100` | Series fetched per sync chunk |
| `WOF_CATALOG_PAGE_DEFAULT` | No | `50` | Default page size for series browse |
| `WOF_SCOPED_LIBRARY_IDS` | No | — | Optional comma-separated library native IDs to mark in-scope on sync (bootstrap only; users normally manage scope in **Settings → Libraries**) |
| `WOF_INSTALL_TIMEZONE` | No | `UTC` | IANA timezone for nightly rebuild schedule |
| `WOF_REBUILD_CRON` | No | `04:00` | Local rebuild time (`HH:MM` in install timezone) |
| `WOF_ARTWORK_CACHE_DIR` | No | `/data/artwork` | On-disk poster cache |
| `WOF_ARTWORK_CACHE_TTL_DAYS` | No | `30` | Poster cache TTL (days; `0` = never expire) |

## Data storage

The entrypoint starts as **root**, remaps the internal `app` user to **`PUID`/`PGID`** (defaults `1000`), `chown`s `/data`, then drops privileges. There is **no** `user:` line in compose — same pattern as LinuxServer and many homelab images.

**Named volume (default)** — no host setup:

```bash
docker compose up -d
```

**Bind mount (optional)** — host-visible `./data`:

```bash
mkdir -p data
cp compose.override.yml.example compose.override.yml
# set PUID/PGID in .env to match your host user: id -u && id -g
docker compose up -d
```

The entrypoint fixes `/data` ownership on each start, so you usually do **not** need a manual host `chown`. Set `PUID`/`PGID` to your host uid/gid when using a bind mount (Synology/NAS installs often use something other than 1000).

## Backup

SQLite data lives on the Docker volume `wof_data` (or `./data` if using the override).

1. Stop the stack: `docker compose down`
2. Copy the database file:
   - **Named volume:** use `docker run --rm -v wof_data:/data -v $(pwd):/backup alpine cp /data/wheeloffish.db /backup/wheeloffish.db`
   - **Bind mount:** copy `./data/wheeloffish.db` directly

## PostgreSQL upgrade path

For larger deployments, point `DATABASE_URL` at PostgreSQL (e.g. `postgresql+psycopg://user:pass@host:5432/wof`) and run migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Main-branch CI runs a Postgres profile smoke test to guard portability.

## Reverse proxy

The production image serves the API and SPA on one HTTP port. Terminate TLS with your own reverse proxy (Caddy, Traefik, nginx, etc.) and set `WOF_OAUTH_CALLBACK_BASE` to the public HTTPS origin users use in the browser.

## Phase 2 — Connections and catalog

Phase 2 adds Plex and Jellyfin connectors with cached series browse, background sync, and resume preview. Set `WOF_ENABLED_PROVIDERS` to gate which providers appear in `GET /api/v1/providers`.

### Connection setup

**Plex (OAuth PIN flow)**

1. `POST /api/v1/connections/plex/oauth/start` — returns PIN and auth URL
2. Authorize at plex.tv, then poll `GET /api/v1/connections/plex/oauth/status/{pin_id}`
3. Callback creates the connection and stores the token in the secrets vault

**Jellyfin (username/password)**

1. `POST /api/v1/connections/jellyfin/auth` with `base_url`, `username`, and `password`
2. Connection is created and the access token is stored per user

**Direct token (either provider)**

- `POST /api/v1/connections` with `provider_type`, `base_url`, and `token`

Use `POST /api/v1/connections/{id}/test` to verify connectivity.

### Catalog browse and sync

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/connections/{id}/libraries` | All cached TV libraries for the signed-in user, each with `in_scope` |
| `GET /api/v1/connections/{id}/series` | Paginated series browse — **in-scope libraries only** (`page`, `limit`, `q`) |
| `POST /api/v1/connections/{id}/sync` | Trigger background series sync (202) |
| `GET /api/v1/connections/{id}/sync/status` | Poll sync progress |
| `PUT /api/v1/connections/{id}/library-scope` | Set in-scope library IDs for the signed-in user |

### Resume preview (UAT)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/connections/{id}/series/{series_id}/episodes` | Live episode list from provider |
| `GET /api/v1/connections/{id}/series/{series_id}/resume` | Computed resume pointer for a series |

Compare resume output to Plex On Deck or Jellyfin Next Up. See `.planning/phases/02-media-ingestion-catalogs/02-UAT-CHECKLIST.md` for manual verification steps.

## Web UI

The React/Vite SPA is served from the same container as the API. Users sign in with Plex PIN OAuth or Jellyfin credentials only — there is no local username/password account and no in-app media-server URL wizard (server URL lives in `.env`).

### Install-time configuration (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `WOF_SECRET_KEY` | Yes | 64-char hex; encrypts stored tokens |
| `WOF_PROVIDER` | Yes | `plex` or `jellyfin` — one provider per install |
| `WOF_MEDIA_SERVER_URL` | Yes | Base URL of your Plex or Jellyfin server |
| `WOF_OAUTH_CALLBACK_BASE` | Yes | Public URL for OAuth redirects (HTTPS in production) |
| `WOF_MEDIA_SERVER_DISPLAY_NAME` | No | Label in Settings |
| `WOF_VERIFY_SSL` | No | TLS verification for media server API calls |
| `WOF_SESSION_DAYS` | No | Session cookie TTL; unset = long-lived |

Changing provider or server URL requires editing `.env` and restarting the container.

### Per-user library scope

- Scope is stored **per signed-in user** (`app_user_id`), not install-wide.
- After first OAuth link, **all TV libraries** visible to that account are in scope until the user changes **Settings → Libraries**.
- `GET /api/v1/auth/me` exposes `libraries_scoped` (at least one in-scope library) and `has_media_link`.
- If Browse is blocked, the app redirects to **Settings → Libraries** until scope is set (or defaults apply after sync).

### Local frontend development

With the backend running on port 8000:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the backend. Use `npm run test -- --run` for unit tests and `npm run build` for production assets (bundled into the backend image via multi-stage Docker build).

### SPA features

- Login: Plex PIN OAuth or Jellyfin username/password
- **Settings → Libraries** for per-user TV library scope (any linked user)
- Library browse: grid/list toggle, infinite scroll, debounced search, sync banner
- Playlists: two-pane editor, rebuild controls, provider writeback status
- Series detail at `/series/{id}` with read-only resume preview
- Playlist edit: optional **Don’t ask again** on remove-from-playlist confirmation (resets after save or leaving the page)
- Light/dark theme toggle

Manual verification: `.planning/phases/03-minimal-operator-spa-shell/03-UAT-CHECKLIST.md` (updated for per-user scope; some historical rows may still mention removed admin flows).

## Security

Automated scans (Gitleaks, Semgrep, pip-audit, npm audit, Trivy, API auth guard tests) run on every PR via [`.github/workflows/security.yml`](.github/workflows/security.yml). Local run: `./scripts/security-local.sh`. Details: [SECURITY.md](SECURITY.md).

## Development

Enable git hooks once per clone (strips Cursor `Co-authored-by` trailers from commit messages; required for agent commits):

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

```bash
cd backend
uv sync
export WOF_SECRET_KEY=$(openssl rand -hex 32)
uv run pytest
uv run pytest tests/security -q   # auth guard regression only
uv run pip-audit                  # dependency CVE check
uv run uvicorn wheeloffish.main:app --reload
```

## Project layout

```
backend/          FastAPI application, Alembic migrations, Docker context
frontend/         React/Vite SPA (Phase 3 operator shell)
compose.yml       Default API-only stack with SQLite volume
```
