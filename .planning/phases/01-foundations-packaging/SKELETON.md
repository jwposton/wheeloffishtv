# Walking Skeleton — Wheel of Fish TV

**Phase:** 1
**Generated:** 2026-05-25

## Capability Proven End-To-End

An operator can run `docker compose up --wait` and the container passes its healthcheck, exposing a JSON health response that confirms the API process, database connectivity, and schema version — with structured JSON logs on stdout and secrets vault infrastructure ready for Phase 2 media tokens.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI + uvicorn | Async-ready; OpenAPI for Phase 3 SPA; user preference |
| Data layer | SQLite (WAL) + SQLAlchemy 2 + Alembic | D-01 scale; portable Postgres upgrade via `DATABASE_URL` |
| Auth | Deferred Phase 3 | Phase 1 is backend-only; no HTTP auth routes |
| Secrets | Fernet + SQLite `secrets` table | D-14/D-15; encrypted at rest from day one |
| Deployment target | Docker Compose (API-only service) | D-05; no in-repo reverse proxy |
| Package manager | uv (`backend/pyproject.toml` + lockfile) | D-10; reproducible Docker/CI installs |
| Directory layout | Monorepo: `backend/src/wheeloffish/{api,core,db,integrations}` | D-09/D-11 |
| Logging | structlog JSON → stdout | ROADMAP success criterion #1 |
| CI | GitHub Actions: Ruff + pytest + Docker smoke + Postgres profile on main | D-12/D-02 |

## Stack Touched in Phase 1

- [x] Project scaffold (uv, pyproject, ruff, pytest, layered src package)
- [x] Routing — `/health` endpoint with DB status
- [x] Database — Alembic migration + read/write via vault and app_metadata
- [ ] UI — deferred (`frontend/README.md` placeholder only; Phase 3)
- [x] Deployment — `docker compose up --wait` healthcheck passes

## Out of Scope (Deferred to Later Slices)

- SPA / React (Phase 3)
- Plex/Jellyfin live API calls (Phase 2)
- HTTP routes for secrets or media credentials (Phase 2+)
- Worker / scheduler containers (Phase 5)
- Reverse proxy / HTTPS termination (operator external infra)
- User authentication (Phase 3)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- **Phase 2:** Live Plex connector + normalized DTOs + watch-state cache (uses vault helpers + integrations/)
- **Phase 3:** React SPA shell + auth gate + connection wizard (upstream to same app HTTP port)
- **Phase 4:** Playlist mathematics engine
- **Phase 5:** Scheduler/worker profile + nightly rebuild orchestration
- **Phase 6:** Admin WheelOfFish RBAC
- **Phase 7:** UX polish + release readiness
