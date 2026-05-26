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

## Release deployment (pre-built image)

Published multi-arch images (`linux/amd64`, `linux/arm64`) are on GitHub Container Registry:

```text
ghcr.io/jwposton/wheeloffishtv:0.1.3
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
| `WOF_ADMIN_PROVIDER_USER_ID` | No | — | Admin provider user ID (set after first OAuth login) |
| `WOF_ADMIN_USERNAME` | No | — | Optional secondary admin match on username/email |
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
| `WOF_SCOPED_LIBRARY_IDS` | No | — | Optional comma-separated library IDs to auto-scope |

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

This repository ships the API service only — no bundled HTTPS reverse proxy. Terminate TLS with your own infrastructure (Caddy, Traefik, nginx, etc.) upstream of the app HTTP port when the SPA lands in Phase 3.

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
| `GET /api/v1/connections/{id}/libraries` | TV libraries (cached, in-scope only) |
| `GET /api/v1/connections/{id}/series` | Paginated cached series browse (`page`, `limit`, `q`) |
| `POST /api/v1/connections/{id}/sync` | Trigger background series sync (202) |
| `GET /api/v1/connections/{id}/sync/status` | Poll sync progress |
| `PUT /api/v1/admin/connections/{id}/library-scope` | Admin: set in-scope library IDs |

### Resume preview (UAT)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/connections/{id}/series/{series_id}/episodes` | Live episode list from provider |
| `GET /api/v1/connections/{id}/series/{series_id}/resume` | Computed resume pointer for a series |

Compare resume output to Plex On Deck or Jellyfin Next Up. See `.planning/phases/02-media-ingestion-catalogs/02-UAT-CHECKLIST.md` for manual verification steps.

## Phase 3 — Operator SPA

Phase 3 ships the React/Vite SPA served from the same container as the API. Users sign in via media-server OAuth only — there is no standalone local username/password login and no in-app server setup wizard.

### Operator setup (before `docker compose up`)

Configure connection settings in `.env` (D-06, D-09). The runtime reads env on boot and upserts the single `connections` row; changing server URL or provider requires editing `.env` and restarting the container (D-08).

| Variable | Required | Description |
|----------|----------|-------------|
| `WOF_PROVIDER` | Yes | `plex` or `jellyfin` — one provider per install (D-02) |
| `WOF_MEDIA_SERVER_URL` | Yes | Base URL of your Plex or Jellyfin server |
| `WOF_MEDIA_SERVER_DISPLAY_NAME` | No | Friendly label shown in Settings |
| `WOF_VERIFY_SSL` | No | Verify TLS when connecting to the media server |
| `WOF_ADMIN_PROVIDER_USER_ID` | After first login | Provider user ID for admin RBAC (D-03) |
| `WOF_ADMIN_USERNAME` | No | Optional secondary admin match on username/email |
| `WOF_OAUTH_CALLBACK_BASE` | Yes | Public base URL for OAuth redirects |
| `WOF_SESSION_DAYS` | No | Session cookie TTL in days; unset = long-lived (D-05) |

Copy `.env.example` to `.env`, set `WOF_SECRET_KEY`, provider, and media server URL before starting the stack.

### Admin discovery (D-04)

If `WOF_ADMIN_PROVIDER_USER_ID` is unset on first OAuth login, the app enters **setup mode**: users may browse once libraries are scoped, but admin actions (library scope) are blocked until the operator copies the signed-in provider user ID from **Setup → Admin** (`/setup/admin`) into `.env` and restarts.

### Local frontend development

With the backend running on port 8000:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to the backend. Use `npm run test -- --run` for unit tests and `npm run build` for production assets (bundled into the backend image via multi-stage Docker build).

### SPA features (Phase 3 scope)

- Login wall: Plex PIN OAuth or Jellyfin username/password
- Admin library scope UI with first-run checklist and Settings → Libraries
- Series browse: grid/list toggle, infinite scroll, debounced search, sync banner
- Series detail at `/series/{composite_id}` with read-only resume/up-next preview (D-16)
- Light/dark theme toggle with `prefers-color-scheme` default (D-18)

**Storybook** is explicitly deferred to Phase 7 (D-20) — no Storybook config in this phase.

Manual keyboard, OAuth, and theme verification steps: `.planning/phases/03-minimal-operator-spa-shell/03-UAT-CHECKLIST.md`.

## Security

Automated scans (Gitleaks, Semgrep, pip-audit, npm audit, Trivy, API auth guard tests) run on every PR via [`.github/workflows/security.yml`](.github/workflows/security.yml). Local run: `./scripts/security-local.sh`. Details: [SECURITY.md](SECURITY.md).

## Development

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
