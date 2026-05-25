---
phase: 2
slug: media-ingestion-catalogs
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio + respx |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && uv run pytest -q` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q`
- **After every plan wave:** Run `cd backend && uv run ruff check . && uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INT-01 | T-01 | Tokens encrypted in vault, never in DB | unit | `pytest tests/unit/test_composite_ids.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | INT-01 | T-02 | Test-then-save rejects bad creds | unit | `pytest tests/api/test_connections_routes.py -k unauthorized` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | INT-01 | — | Plex OAuth PIN start | unit | `pytest tests/integrations/test_plex_client.py -k oauth_start` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | INT-01 | — | Plex OAuth callback stores vault token | integration | `pytest tests/api/test_connections_routes.py -k plex_oauth` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | INT-01 | — | Jellyfin auth stores per-user token | unit | `pytest tests/integrations/test_jellyfin_client.py -k auth` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | INT-01 | — | provider_disabled when gated | unit | `pytest tests/api/test_connections_routes.py -k provider_disabled` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 2 | INT-02 | — | Plex lists TV libraries from fixture | unit | `pytest tests/integrations/test_plex_client.py -k libraries` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 2 | INT-02 | — | Cached series paging + search | integration | `pytest tests/api/test_catalog_routes.py -k series_page` | ❌ W0 | ⬜ pending |
| 02-04-03 | 04 | 2 | INT-02 | — | Background sync non-blocking | integration | `pytest tests/api/test_catalog_routes.py -k sync_status` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 3 | INT-03 | — | Watch classification thresholds | unit | `pytest tests/unit/test_watch_classification.py` | ❌ W0 | ⬜ pending |
| 02-05-02 | 05 | 3 | INT-03 | — | Resume hybrid + specials golden vectors | unit | `pytest tests/unit/test_resume_service.py` | ❌ W0 | ⬜ pending |
| 02-06-01 | 06 | 3 | INT-03 | — | Live episodes endpoint (not cached) | integration | `pytest tests/api/test_catalog_routes.py -k episodes` | ❌ W0 | ⬜ pending |
| 02-06-02 | 06 | 3 | INT-03 | — | Resume preview matches ResumeService | integration | `pytest tests/api/test_catalog_routes.py -k resume` | ❌ W0 | ⬜ pending |
| 02-07-01 | 07 | 4 | INT-01/02/03 | — | Alembic migration applies | integration | `cd backend && uv run alembic upgrade head` | ❌ W0 | ⬜ pending |
| 02-07-02 | 07 | 4 | D-03 | — | Fixtures contain no real tokens | source | `grep -r X-Plex-Token tests/fixtures/ && exit 1 || true` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `respx` added to dev dependencies in `backend/pyproject.toml`
- [ ] `backend/tests/conftest.py` — extend with httpx AsyncClient, vault, connection_factory fixtures
- [ ] `backend/tests/fixtures/plex/` — sanitized JSON fixtures (pin, libraries, shows, episodes, ondeck)
- [ ] `backend/tests/fixtures/jellyfin/` — sanitized JSON fixtures (auth, folders, series, episodes, next_up)
- [ ] `backend/tests/unit/test_composite_ids.py` — composite ID parse/format
- [ ] `backend/tests/unit/test_watch_classification.py` — D-11 thresholds
- [ ] `backend/tests/unit/test_resume_service.py` — D-10/D-12 golden vectors
- [ ] `backend/tests/integrations/test_plex_client.py`, `test_jellyfin_client.py` — respx routes
- [ ] `backend/tests/api/test_connections_routes.py`, `test_catalog_routes.py` — FastAPI TestClient

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Plex OAuth E2E | INT-01, D-03 | Requires real Plex account + PMS | Complete PIN flow; verify libraries visible |
| Jellyfin auth E2E | INT-01, D-03 | Requires real Jellyfin server | Authenticate; verify libraries visible |
| Resume vs On Deck | INT-03 | Provider-specific metadata | Compare resume preview to Plex On Deck / Jellyfin Next Up for 3 series |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
