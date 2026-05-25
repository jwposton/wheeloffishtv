---
phase: 5
slug: orchestration-scheduling
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-25
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 + pytest-asyncio ≥0.24 |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && uv run pytest tests/unit/test_orchestrator.py tests/unit/test_playlist_cadence.py -q` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run module-scoped pytest for touched test file
- **After every plan wave:** Run `cd backend && uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full suite must be green + SPA manual UAT for status badges
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PLT-01–03 | T-05-01-01 | Alembic migration applies cleanly | integration | `cd backend && uv run alembic upgrade head` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | PLT-01–03 | T-05-01-02 | ORM→domain conversion matches Phase 4 | unit | `pytest tests/unit/test_playlist_models.py -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | SCH-01, D-03 | — | Cadence due filter daily/weekly | unit | `pytest tests/unit/test_playlist_cadence.py -x` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | SCH-01, D-07 | T-05-02-01 | Scheduler starts in lifespan smoke | unit | `pytest tests/unit/test_scheduler.py -x` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | D-11–D-14 | T-05-03-01 | Row skip on fetch failure | unit | `pytest tests/unit/test_orchestrator.py -k row_skip -x` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 3 | D-12, D-17 | T-05-03-02 | All excluded → failed, keep last good | unit | `pytest tests/unit/test_orchestrator.py -k all_excluded -x` | ❌ W0 | ⬜ pending |
| 05-03-03 | 03 | 3 | D-14 | T-05-03-03 | Empty snapshot row warning | unit | `pytest tests/unit/test_orchestrator.py -k empty_snapshot -x` | ❌ W0 | ⬜ pending |
| 05-03-04 | 03 | 3 | D-15, D-16 | — | Snapshot persist + prune to 3 | unit | `pytest tests/unit/test_orchestrator.py -k prune -x` | ❌ W0 | ⬜ pending |
| 05-04-01 | 04 | 4 | PLT-01–03, D-18 | T-05-04-01 | Cross-user playlist access denied | integration | `pytest tests/integration/test_playlists_api.py -x` | ❌ W0 | ⬜ pending |
| 05-04-02 | 04 | 4 | D-06, D-22 | T-05-04-02 | Owner-only manual rebuild | integration | `pytest tests/integration/test_playlists_api.py -k rebuild -x` | ❌ W0 | ⬜ pending |
| 05-05-01 | 05 | 5 | WEB-01, D-19–D-21 | — | Playlist list renders status badge | frontend | `npm run test -- --run src/pages/PlaylistsPage.test.tsx` | ❌ W0 | ⬜ pending |
| 05-06-01 | 06 | 6 | WEB-01, D-25–D-26 | — | Create/edit form saves playlist | frontend | `npm run test -- --run src/pages/PlaylistDetailPage.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_orchestrator.py` — orchestrator loop, failure isolation (D-11–D-14)
- [ ] `backend/tests/unit/test_playlist_cadence.py` — is_due logic per D-02–D-04
- [ ] `backend/tests/unit/test_playlist_models.py` — ORM + Pydantic validation
- [ ] `backend/tests/unit/test_scheduler.py` — APScheduler lifespan smoke
- [ ] Install APScheduler: `cd backend && uv add apscheduler`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Nightly cron fires at configured local time | SCH-01 | APScheduler timing hard to unit-test reliably | Set WOF_REBUILD_CRON to next minute; WOF_INSTALL_TIMEZONE=UTC; observe rebuild log |
| Status badge green/amber/red | D-21, WEB-01 | Visual semantic colors | Trigger success/partial/failed rebuilds; verify card badge + detail banner |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
