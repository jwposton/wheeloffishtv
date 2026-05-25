# Phase 1: Foundations & packaging - Research

**Researched:** 2026-05-25
**Domain:** FastAPI backend packaging, Docker/Compose, SQLite/Alembic, encrypted secrets vault
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** SQLite primary DB for v1; SQLAlchemy + Alembic with documented PostgreSQL upgrade path
- **D-02:** Dev/CI SQLite; main-branch CI runs Postgres smoke job
- **D-03:** First migration creates `app_metadata` + `secrets` tables (not empty bootstrap)
- **D-04:** SQLite named Docker volume, WAL mode, path `/data/wheeloffish.db`; `compose.override.yml` bind-mount example; README backup docs
- **D-05:** Default `docker compose up` is API-only + SQLite volume
- **D-06:** No reverse proxy in repo; Phase 1 health via Compose healthcheck only
- **D-07:** Config via compose `environment:` defaults + `.env` overrides; secrets in `.env`; ship `.env.example`
- **D-08:** Optional Compose profiles (`--profile postgres` for CI); worker deferred Phase 5
- **D-09:** Monorepo: `backend/` + `frontend/` placeholder + root `compose.yml`
- **D-10:** Python tooling: `uv` with `backend/pyproject.toml` + lockfile
- **D-11:** Backend layout: `backend/src/wheeloffish/` with `api/`, `core/`, `db/`, `integrations/`, `tests/`, `alembic/`
- **D-12:** CI: Ruff + pytest + Docker build smoke + Postgres profile on main
- **D-13:** Vault namespaced CRUD: `get_secret`, `set_secret`, `delete_secret` with keys like `media_server/{connection_id}/token`
- **D-14:** Secrets encrypted at rest (Fernet) using `WOF_SECRET_KEY`
- **D-15:** `WOF_SECRET_KEY` required in `.env`; fail fast if missing
- **D-16:** Typed helpers only in Phase 1 — no HTTP routes for secrets

### Claude's Discretion
- Fernet/library choice, SQLite file naming, health endpoint path, JSON log field names, Plex/Jellyfin stub contents

### Deferred Ideas (OUT OF SCOPE)
- Bundled reverse-proxy Compose profile
- HTTPS reverse-proxy profile
- Worker Compose profile (Phase 5)
- Auth model, Plex vs Jellyfin priority, multipart heuristics
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Health/readiness | API/Backend | Docker Compose healthcheck | Compose probes container; app exposes `/health` |
| Config & secrets key | API/Backend | `.env` at runtime | Pydantic Settings loads env; never baked in image |
| Structured logging | API/Backend | stdout → container logs | JSON to stdout for log aggregation |
| Persistence (metadata + secrets) | Database/Storage | API/Backend (SQLAlchemy) | SQLite file on named volume |
| Vault encryption | API/Backend | Database/Storage | Fernet encrypt before write to `secrets` table |
| CI smoke | External (GitHub Actions) | Docker Compose | Builds image, runs compose healthcheck |
| Plex/Jellyfin stubs | API/Backend (integrations/) | — | Placeholder modules only; no live calls |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 1 is a greenfield FastAPI backend packaged for self-host Docker deployment. The standard 2025 stack for this shape is **FastAPI + Pydantic v2 Settings + SQLAlchemy 2.x + Alembic + uv + structlog JSON + Ruff + pytest**, built into a multi-stage Docker image with **uv sync --frozen** for reproducible installs.

SQLite is appropriate for ≤5 casual users with WAL mode and a fixed path on a named volume. Alembic autogenerate works with SQLAlchemy models; the first migration should create foundation tables explicitly. For PostgreSQL portability, use a `DATABASE_URL` env var with SQLAlchemy URL parsing and run a main-branch CI job against Postgres via Compose profile.

Secrets at rest should use **cryptography.fernet.Fernet** keyed from `WOF_SECRET_KEY` (32-byte hex or url-safe base64 derived key). Do not store plaintext tokens in the `secrets` table. Application startup must validate required env vars before serving traffic.

**Primary recommendation:** Scaffold with uv monorepo layout, ship a single `app` Compose service with internal healthcheck (no host port publish in Phase 1), prove DB round-trip via Alembic + integration test, and gate CI with Ruff/pytest/Docker/Postgres profile smoke on main.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | LTS; good Docker slim images |
| FastAPI | ≥0.115 | HTTP API | Async, OpenAPI, Pydantic native |
| uvicorn | ≥0.30 | ASGI server | Standard FastAPI deployment |
| pydantic-settings | ≥2.0 | Config from env | Fail-fast validation, `.env` support |
| SQLAlchemy | ≥2.0 | ORM | Alembic compatibility, Postgres path |
| Alembic | ≥1.13 | Migrations | Industry standard for SQLAlchemy |
| structlog | ≥24.0 | Structured logging | JSON renderer for container logs |
| cryptography | ≥42.0 | Fernet encryption | Well-audited; simple API for vault |
| httpx | ≥0.27 | HTTP client (future) | Async client for Phase 2 integrations |
| uv | latest | Package manager | Fast lockfile installs in Docker/CI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | ≥0.8 | Lint + format | CI baseline per D-12 |
| pytest | ≥8.0 | Tests | Unit + integration smoke |
| pytest-asyncio | ≥0.24 | Async tests | FastAPI TestClient async routes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fernet | libsodium/age | Fernet simpler for single master key MVP |
| structlog | python-json-logger | structlog better processor pipeline |
| SQLite | Postgres day 1 | User chose SQLite for v1 scale; CI Postgres smoke suffices |

**Installation (local dev):**
```bash
cd backend && uv sync
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### System Architecture Diagram

```
Operator `.env` + compose.yml
        │
        ▼
┌───────────────────┐
│  Docker Compose   │
│  service: app     │
│  healthcheck ─────┼──► GET /health (inside container)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────┐
│  FastAPI (uvicorn)│────►│ structlog → stdout  │
│  /health          │     └─────────────────────┘
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌────────┐  ┌──────────────┐
│Settings│  │ Vault service │
│WOF_*   │  │ Fernet CRUD   │
└────────┘  └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ SQLite WAL   │
            │ /data/*.db   │
            │ app_metadata │
            │ secrets      │
            └──────────────┘
```

### Recommended Project Structure
```
wheeloffishtv/
├── compose.yml
├── compose.override.yml.example
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── src/wheeloffish/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── secrets.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models/
│   │   └── integrations/
│   │       ├── plex.py
│   │       └── jellyfin.py
│   └── tests/
├── frontend/
│   └── README.md
└── .github/workflows/ci.yml
```

### Pattern 1: Pydantic Settings with fail-fast
**What:** Load config from environment; raise on missing required vars at import/startup.
**When to use:** All deployment config including `WOF_SECRET_KEY`, `DATABASE_URL`.

### Pattern 2: Alembic with SQLAlchemy 2.0 declarative models
**What:** Models in `db/models/`; Alembic env imports metadata; first revision creates foundation tables.
**When to use:** Any schema change; run `alembic upgrade head` in Docker entrypoint or CI.

### Pattern 3: structlog JSON for containers
**What:** Configure structlog with `JSONRenderer` when not in dev; bind `request_id` per request via middleware.
**When to use:** All production/Compose logging.

### Anti-Patterns to Avoid
- **Baking secrets into Docker image:** Use `.env` + runtime env only (D-07, D-15)
- **Publishing host ports in Phase 1:** Healthcheck-only per D-06
- **Plaintext secrets column:** Encrypt before INSERT (D-14)
- **Horizontal-only plans:** MVP mode requires end-to-end slices per plan
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config parsing | Custom env reader | pydantic-settings | Validation, types, `.env` file support |
| Migrations | Raw SQL scripts only | Alembic | Upgrade/downgrade, autogenerate, CI reproducibility |
| Encryption | XOR/base64 "encryption" | cryptography.fernet | Audited crypto; key derivation documented |
| Docker deps install | pip install in Dockerfile | uv sync --frozen | Lockfile reproducibility, layer caching |
| Lint/format | flake8+black+isort | Ruff | Single tool, fast CI |

**Key insight:** Phase 1 establishes patterns every later phase inherits — use battle-tested libraries now to avoid rework in Phase 2 media connectors.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: SQLite locking without WAL
**What goes wrong:** Concurrent reads/writes block or fail under test + healthcheck
**How to avoid:** `PRAGMA journal_mode=WAL` on engine connect (D-04)
**Warning signs:** "database is locked" in logs

### Pitfall 2: Missing WOF_SECRET_KEY in Compose
**What goes wrong:** App starts with weak default or silently generates key
**How to avoid:** Required field in Settings with no default; document in `.env.example` (D-15)
**Warning signs:** Secrets decrypt failures after container recreate

### Pitfall 3: Alembic not run in container startup
**What goes wrong:** Health passes but tables missing on fresh volume
**How to avoid:** Entrypoint or startup event runs `alembic upgrade head` before accepting traffic
**Warning signs:** `no such table` on first vault operation

### Pitfall 4: Postgres-incompatible SQL in migrations
**What goes wrong:** Main-branch Postgres smoke fails
**How to avoid:** Avoid SQLite-only types; use portable SQLAlchemy types; test postgres profile in CI (D-02)
**Warning signs:** CI postgres job fails on migration apply
</common_pitfalls>

<code_examples>
## Code Examples

### Fernet key from hex secret
```python
# Source: cryptography docs pattern
import base64
from cryptography.fernet import Fernet

def fernet_from_secret_key(hex_key: str) -> Fernet:
    raw = bytes.fromhex(hex_key)
    # Fernet requires 32 url-safe base64-encoded bytes
    return Fernet(base64.urlsafe_b64encode(raw))
```

### structlog JSON configuration
```python
# Source: structlog logging best practices
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
```

### Compose healthcheck (no host publish)
```yaml
# Phase 1: internal healthcheck only (D-06)
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```
</code_examples>

<sota_updates>
## State of the Art (2024-2026)

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| pip + requirements.txt | uv + pyproject.toml + lockfile | Faster CI/Docker; reproducible builds |
| logfmt/plain text in containers | structlog JSON to stdout | Better aggregation in Loki/Datadog |
| Poetry default | uv for new projects | Simpler Docker integration |

**Deprecated/outdated:**
- `--no-dev` uv flag → use `--no-dev` / dependency groups per uv 0.4+ docs
</sota_updates>

<open_questions>
## Open Questions

1. **Health endpoint path: `/health` vs `/api/health`**
   - Recommendation: Use `/health` for Compose probe simplicity; Phase 3 can namespace API under `/api/` when SPA mounts

2. **Single vs multiple workers in Docker CMD**
   - Recommendation: Single uvicorn worker in Phase 1 (SQLite + single container); document scale-out for Postgres later

3. **Alembic run: entrypoint script vs FastAPI lifespan**
   - Recommendation: Shell entrypoint `alembic upgrade head && exec uvicorn ...` — explicit, visible in logs, fails container if migration fails
</open_questions>

## Validation Architecture

| Requirement | Behavior to Verify | Test Type | Command / Assertion |
|-------------|-------------------|-----------|---------------------|
| DEP-01 | Docker image builds | integration | `docker build -t wof-test backend` exits 0 |
| DEP-01 | Compose healthcheck passes | integration | `docker compose up --wait` exits 0 |
| DEP-01 | README documents quickstart | source | `grep -q 'docker compose' README.md` |
| INT-01 | Vault stores encrypted blob | unit | `pytest tests/test_secrets.py -k encrypt` exits 0 |
| INT-01 | Vault round-trip get/set/delete | unit | `pytest tests/test_secrets.py` exits 0 |
| D-03 | Migration creates tables | integration | `alembic upgrade head` + query `app_metadata`, `secrets` |
| D-12 | Ruff clean | lint | `uv run ruff check .` exits 0 |
| D-12 | pytest green | unit | `uv run pytest` exits 0 |
| D-02 | Postgres profile smoke (main) | integration | CI job with `--profile postgres` |
| D-15 | Missing WOF_SECRET_KEY fails startup | unit | pytest raises ValidationError / exit 1 on boot |

**Wave 0 (test infrastructure):**
- `backend/tests/conftest.py` — temp SQLite DB, settings override fixture
- `backend/tests/test_health.py` — health endpoint smoke
- `backend/tests/test_secrets.py` — vault CRUD + encryption assertions
- Ruff + pytest configured in `pyproject.toml`

**Sampling:**
- After each task: `uv run pytest -q` (target <30s)
- After each plan wave: `uv run ruff check . && uv run pytest`
- Before phase verify: full CI script locally

<sources>
## Sources

### Primary (HIGH confidence)
- FastAPI official docs — project structure, TestClient, lifespan
- structlog 25.x docs — JSON logging best practices
- cryptography docs — Fernet usage
- uv docs — Docker integration, `uv sync --frozen`
- Alembic tutorial — SQLAlchemy 2.0 style

### Secondary (MEDIUM confidence)
- Production FastAPI + uv Docker patterns (2025 articles) — multi-stage build, non-root user

### Tertiary (LOW confidence)
- None requiring validation beyond implementation smoke tests
</sources>

<metadata>
## Metadata

**Research scope:** FastAPI packaging, Docker/Compose, SQLite/Alembic, Fernet vault, CI baseline

**Confidence breakdown:**
- Standard stack: HIGH — well-documented ecosystem
- Architecture: HIGH — aligns with CONTEXT.md decisions
- Pitfalls: HIGH — common SQLite/Docker pitfalls documented
- Code examples: HIGH — from official library docs

**Research date:** 2026-05-25
**Valid until:** 2026-06-25
</metadata>

---

*Phase: 01-foundations-packaging*
*Research completed: 2026-05-25*
*Ready for planning: yes*

## RESEARCH COMPLETE
