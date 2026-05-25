# Wheel of Fish TV

Self-hosted Dockerized Plex/Jellyfin random TV playlist builder. Users connect a media server, configure playlists with ordered or disordered show rows, and get daily rebuilt episode lists.

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

   The `app` service should show `healthy`. Phase 1 does not publish host ports — health is verified via Compose healthcheck. Phase 3 will expose an HTTP port for an external reverse proxy.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WOF_SECRET_KEY` | Yes | — | 64-char hex key from `openssl rand -hex 32`; encrypts stored secrets |
| `DATABASE_URL` | No | `sqlite:////data/wheeloffish.db` | SQLAlchemy database URL |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `LOG_FORMAT` | No | `json` | `json` for production; `console` for local dev |
| `ENVIRONMENT` | No | `production` | Environment label in logs and health |
| `WOF_ENABLED_PROVIDERS` | No | `plex,jellyfin` | Comma-separated media providers to expose |
| `WOF_PLEX_PRODUCT_NAME` | No | `Wheel of Fish TV` | Product name shown during Plex PIN flow |
| `WOF_OAUTH_CALLBACK_BASE` | No | `http://localhost:8000` | Base URL for OAuth callback redirects |
| `WOF_CATALOG_SYNC_CHUNK_SIZE` | No | `100` | Series fetched per sync chunk |
| `WOF_CATALOG_PAGE_DEFAULT` | No | `50` | Default page size for series browse |
| `WOF_SCOPED_LIBRARY_IDS` | No | — | Optional comma-separated library IDs to auto-scope |

Optional bind-mount for host backups:

```bash
cp compose.override.yml.example compose.override.yml
```

This mounts `./data` to `/data` inside the container.

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

## Development

```bash
cd backend
uv sync
export WOF_SECRET_KEY=$(openssl rand -hex 32)
uv run pytest
uv run uvicorn wheeloffish.main:app --reload
```

## Project layout

```
backend/          FastAPI application, Alembic migrations, Docker context
frontend/         SPA placeholder (Phase 3)
compose.yml       Default API-only stack with SQLite volume
```
