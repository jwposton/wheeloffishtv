# Phase 1: Foundations & packaging - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a runnable, containerized FastAPI backend skeleton with Docker Compose, Alembic migrations, structured logging baseline, CI smoke tests, and a secrets vault abstraction stub anticipating Plex/Jellyfin credential storage. No live media connectivity, no SPA implementation, and no in-repo reverse proxy — this phase is repo skeleton, tooling, and deployment baseline only.

Requirements covered: **DEP-01**, **INT-01** (structural vault surfaces only).

</domain>

<decisions>
## Implementation Decisions

### Database engine
- **D-01:** **SQLite is the primary database** for v1 self-host MVP (≤5 casual users). Use portable **SQLAlchemy + Alembic** patterns with a documented **PostgreSQL upgrade path** for possible future community rollout.
- **D-02:** **Dev and CI use SQLite** (in-memory where appropriate for fast tests). **Main-branch CI runs a Postgres smoke job** (`DATABASE_URL=postgresql://…`) to prove portability and catch regressions early.
- **D-03:** **First migration creates minimal foundation tables:** `app_metadata` (schema version, install id) plus a **secrets storage table** for the vault stub — not an empty Alembic-only bootstrap.
- **D-04:** **SQLite persistence:** named Docker volume by default, **WAL mode enabled**, fixed path (e.g. `/data/wheeloffish.db`). Ship **`compose.override.yml` example** for bind-mounting `./data` on the host. README documents backup (stop container → copy volume or file).

### Compose topology
- **D-05:** **Default `docker compose up` is API-only:** single `app` service + SQLite data volume. No Postgres, worker, or reverse proxy in the default stack.
- **D-06:** **No reverse proxy container in this repo.** Operator may terminate HTTPS with an **external reverse proxy** (separate infra). Phase 3 publishes **one HTTP port** on the app for upstream (built SPA + `/api/…` on the same service). Phase 1 health is verified via **Compose `healthcheck`**, not as a public-facing API product surface.
- **D-07:** **Config injection:** sane defaults in `compose.yml` `environment:` block; **`.env` overrides** for local customization. Secrets (including `WOF_SECRET_KEY`) live in **`.env` at runtime**, never baked into images. Ship **`.env.example`**.
- **D-08:** **Optional services via Compose profiles** in a single `compose.yml`: `--profile postgres` for CI smoke; **`worker` profile deferred to Phase 5**; no bundled proxy profile for MVP.

### Repo layout & Python packaging
- **D-09:** **Monorepo stub:** `backend/` (FastAPI, Alembic, Docker context) + `frontend/` (README placeholder until Phase 3) + **root `compose.yml`**.
- **D-10:** **Python tooling:** **`uv`** with `backend/pyproject.toml` + lockfile for local dev, Docker builds, and CI.
- **D-11:** **Backend layout:** layered **`src/` package** at `backend/src/wheeloffish/` with domain folders: `api/`, `core/`, `db/`, `integrations/` (Plex/Jellyfin placeholder modules in Phase 1); plus `tests/` and `alembic/`.
- **D-12:** **CI baseline:** **Ruff** (lint + format) + **pytest** + **Docker build smoke** (image builds, `docker compose up` healthcheck passes). **Postgres profile smoke on main branch** per D-02.

### Secrets vault stub (INT-01 structural)
- **D-13:** Vault exposes **namespaced CRUD:** `get_secret`, `set_secret`, `delete_secret` with keys like `media_server/{connection_id}/token`.
- **D-14:** Secrets **persist in SQLite** and are **encrypted at rest from day one** (e.g. Fernet) using master key from **`WOF_SECRET_KEY` env var**.
- **D-15:** **`WOF_SECRET_KEY` is required in `.env` at install** — app fails fast if missing. README documents generation (e.g. `openssl rand -hex 32`). No auto-generated key files in v1.
- **D-16:** Phase 1 exposes **typed helper functions** (e.g. `store_media_token(connection_id, token)`) and **namespace constants** only — **no HTTP routes** for secrets or Plex creds until Phase 2.

### Claude's Discretion
- Exact Fernet/library choice, SQLite file naming, health endpoint path shape, structured JSON log field names, and placeholder Plex/Jellyfin stub module contents — as long as they honor decisions above and Phase 1 success criteria in ROADMAP.md.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition & requirements
- `.planning/PROJECT.md` — Product scope, constraints (Python/FastAPI, Docker, secrets not in images), self-host persona
- `.planning/REQUIREMENTS.md` — DEP-01, INT-01 traceability; v1 requirement boundaries
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria (Compose health, Alembic round-trip, vault stub, CI green)
- `.planning/research/SUMMARY.md` — Directional stack notes (FastAPI, React/Vite later, job runner, resume/multipart pitfalls for future phases)

</canonical_refs>

<code_context>
## Existing Code Insights

Greenfield repository — planning artifacts only; no application code yet.

### Reusable Assets
- None — Phase 1 establishes the skeleton.

### Established Patterns
- None yet — decisions in this document define the patterns to implement.

### Integration Points
- Root `compose.yml` orchestrates `backend/` Docker build and SQLite data volume.
- `backend/src/wheeloffish/integrations/` receives Plex/Jellyfin client module stubs (no live calls in Phase 1).
- `backend/src/wheeloffish/core/` hosts config, logging, and secrets vault implementation.
- External reverse proxy (operator-managed) upstreams to the app's published HTTP port in Phase 3+.

</code_context>

<specifics>
## Specific Ideas

- **Scale expectation:** ≤5 users, visiting rarely (once or twice a month) — favors SQLite simplicity over Postgres operational overhead for v1.
- **Deployment model:** Operator runs this service in Docker; **HTTPS/reverse proxy is separate infrastructure**, not part of this repo's Compose stack.
- **Future community offer:** PostgreSQL upgrade path and CI Postgres smoke are intentional portability guardrails, not current production requirements.

</specifics>

<deferred>
## Deferred Ideas

- **Bundled reverse-proxy Compose profile** for users who lack external infra (all-in-one demo stack).
- **HTTPS reverse-proxy profile** for community deployments without operator-managed proxy.
- **Worker Compose profile** — add when Phase 5 orchestration jobs land.
- **Auth model, Plex vs Jellyfin priority, multipart heuristics** — belong in Phases 2–4 (noted in STATE.md open questions).

</deferred>

---

*Phase: 1-Foundations & packaging*
*Context gathered: 2026-05-25*
