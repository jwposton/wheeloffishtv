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
