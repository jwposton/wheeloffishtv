---
phase: 1
slug: foundations-packaging
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && uv run pytest -q` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q`
- **After every plan wave:** Run `cd backend && uv run ruff check . && uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DEP-01 | — | N/A | source | `test -f backend/pyproject.toml` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DEP-01 | — | N/A | lint | `cd backend && uv run ruff check .` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | DEP-01 | — | N/A | unit | `pytest tests/test_health.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | D-15 | T-01 | Fail fast without WOF_SECRET_KEY | unit | `pytest tests/test_config.py -k secret_key` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | D-03 | — | N/A | integration | `alembic upgrade head` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | D-04 | — | WAL mode enabled | unit | `pytest tests/test_db.py -k wal` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 3 | INT-01 | T-02 | Secrets encrypted at rest | unit | `pytest tests/test_secrets.py -k encrypt` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 3 | INT-01 | — | CRUD round-trip | unit | `pytest tests/test_secrets.py` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 4 | DEP-01 | — | N/A | integration | `docker compose up --wait` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 4 | D-02 | — | Postgres profile smoke | integration | CI job `compose --profile postgres` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — SQLite temp DB + settings fixtures
- [ ] `backend/tests/test_health.py` — health endpoint stubs
- [ ] `backend/tests/test_secrets.py` — vault encryption stubs
- [ ] `backend/tests/test_config.py` — WOF_SECRET_KEY validation
- [ ] Ruff + pytest in `backend/pyproject.toml`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Compose volume backup | D-04 | Requires operator stop/copy | Stop container, copy volume or bind-mounted file per README |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
