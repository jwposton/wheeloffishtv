# Phase 1: Foundations & packaging - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 1-Foundations & packaging
**Areas discussed:** Database engine, Compose topology, Repo layout & Python packaging, Secrets vault stub

---

## Database engine

| Option | Description | Selected |
|--------|-------------|----------|
| PostgreSQL from day 1 | Postgres in Compose; dev/prod parity | |
| SQLite first, Postgres later | SQLite primary with documented upgrade path | ✓ |
| PostgreSQL in Compose, SQLite for unit tests | Postgres prod + SQLite test convenience | |
| You decide | Agent picks | |

**Q1 — Primary database:** SQLite primary with portable SQLAlchemy/Alembic and clear PostgreSQL upgrade path for possible community rollout.

| Option | Description | Selected |
|--------|-------------|----------|
| SQLite everywhere | Dev/CI SQLite; Postgres manual only | |
| SQLite dev + Postgres smoke in CI | Main-branch CI verifies postgres DATABASE_URL | ✓ |
| Docker Compose profiles | Opt-in postgres profile locally | |
| You decide | Agent picks | |

**Q2 — Dev/test/CI:** SQLite day-to-day; Postgres smoke on main-branch CI.

| Option | Description | Selected |
|--------|-------------|----------|
| Alembic-only bootstrap | No app tables in first migration | |
| Minimal foundation tables | app_metadata + secrets placeholder | ✓ |
| Full Phase 2-ready skeleton | users, connections, etc. upfront | |
| You decide | Agent picks | |

**Q3 — Initial schema:** Minimal foundation tables.

| Option | Description | Selected |
|--------|-------------|----------|
| Named volume + WAL | Default volume; README backup | |
| Bind mount to host | ./data on host | |
| Named volume + bind override | Default volume + compose.override.yml example | ✓ |
| You decide | Agent picks | |

**Q4 — Persistence/backup:** Named volume + WAL + optional bind override via compose.override.yml.

**Notes:** User scale ≤5 users, rare visits — SQLite chosen over Postgres operational overhead; Postgres path kept for future community offer.

---

## Compose topology

| Option | Description | Selected |
|--------|-------------|----------|
| API only | Single app + SQLite volume | ✓ |
| API + reverse proxy | Caddy/Traefik in Compose | |
| API + placeholder worker | Idle worker container | |
| You decide | Agent picks | |

**Q1 — Default services:** API-only stack.

| Option | Description | Selected |
|--------|-------------|----------|
| Publish API port only | e.g. 8000:8000 | |
| Publish + LAN bind | 0.0.0.0 for home network | |
| Internal-only | No host publish; healthcheck only | ✓ (amended) |
| You decide | Agent picks | |

**Q2 — Port exposure:** No in-repo proxy. Phase 3 publishes one HTTP port for external proxy upstream (SPA + API). Phase 1 health via Compose healthcheck.

**Notes:** User clarified external reverse proxy is separate infra — this repo is frontend + backend service only.

| Option | Description | Selected |
|--------|-------------|----------|
| .env + .env.example | Standard env file pattern | |
| .env + fail-fast required vars | Startup validation | |
| environment: defaults + .env overrides | Inline compose defaults with .env override | ✓ |
| You decide | Agent picks | |

**Q3 — Config injection:** compose.yml environment defaults + .env overrides + .env.example.

| Option | Description | Selected |
|--------|-------------|----------|
| Profiles only | --profile postgres, etc. | ✓ |
| Separate override files | compose.postgres.yml merge | |
| Profiles + override files | Both patterns | |
| You decide | Agent picks | |

**Q4 — Future services:** Compose profiles; postgres for CI; worker deferred Phase 5; no in-repo proxy.

---

## Repo layout & Python packaging

| Option | Description | Selected |
|--------|-------------|----------|
| Monorepo stub | backend/ + frontend/ stub + root compose | ✓ |
| Backend-only now | Add frontend in Phase 3 | |
| Flat at root | app/ at repo root | |
| You decide | Agent picks | |

**Q1 — Top-level structure:** Monorepo stub.

| Option | Description | Selected |
|--------|-------------|----------|
| uv | pyproject.toml + lockfile | ✓ |
| Poetry | poetry.lock | |
| pip + requirements.txt | Minimal tooling | |
| You decide | Agent picks | |

**Q2 — Python tooling:** uv.

| Option | Description | Selected |
|--------|-------------|----------|
| src/ layout | backend/src/wheeloffish/ | |
| Flat app/ layout | backend/app/ | |
| Layered by domain | src/ with api/, core/, db/, integrations/ | ✓ |
| You decide | Agent picks | |

**Q3 — Backend layout:** Layered src/ with domain folders (agent recommended option 3; user confirmed).

| Option | Description | Selected |
|--------|-------------|----------|
| Ruff + pytest | Light CI | |
| Ruff + pytest + mypy | Type checking from day one | |
| Ruff + pytest + Docker smoke | Build image + compose health + postgres profile on main | ✓ |
| You decide | Agent picks | |

**Q4 — CI baseline:** Ruff + pytest + Docker/Compose smoke + Postgres profile on main.

---

## Secrets vault stub

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal CRUD | get/set/delete by key | |
| CRUD + namespacing | media_server/{id}/token style keys | ✓ |
| Full KMS-shaped interface | rotate/list stubs | |
| You decide | Agent picks | |

**Q1 — Vault interface:** CRUD + namespaced keys.

| Option | Description | Selected |
|--------|-------------|----------|
| SQLite plaintext stub | TODO encrypt later | |
| SQLite + encryption day one | Fernet via WOF_SECRET_KEY | ✓ |
| Env-only stub | No DB persistence yet | |
| You decide | Agent picks | |

**Q2 — Storage:** SQLite + app-level encryption from day one.

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-generate key on first run | Write to data volume | |
| Required in .env at install | Fail fast; README documents generation | ✓ |
| Required + rotation stub | Placeholder rotate_master_key() | |
| You decide | Agent picks | |

**Q3 — WOF_SECRET_KEY lifecycle:** Required in .env; documented generation.

| Option | Description | Selected |
|--------|-------------|----------|
| Test secrets only | Dummy namespace in tests | |
| Placeholder HTTP route | Dev POST endpoint | |
| Typed helpers + constants | store_media_token(); no HTTP in Phase 1 | ✓ |
| You decide | Agent picks | |

**Q4 — Phase 1 surface:** Typed helpers and namespace constants only; no HTTP routes.

---

## Claude's Discretion

- SQLite vs Postgres recommendation for user's scale (recommended SQLite; user accepted with Postgres path).
- Backend layout recommendation (layered src/ — user accepted option 3).
- CI baseline recommendation (option 3 aligned with Docker deliverable).

## Deferred Ideas

- Bundled reverse-proxy Compose profile for users without external infra.
- HTTPS reverse-proxy profile for community deployments.
- Worker profile — Phase 5.
