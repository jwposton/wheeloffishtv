---
phase: 10
slug: safe-catalog-prune
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-02
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 + pytest-asyncio |
| **Config file** | `backend/pyproject.toml` (`asyncio_mode = "auto"`) |
| **Quick run command** | `cd backend && python3 -m pytest tests/unit/test_catalog_prune.py -x` |
| **Full suite command** | `cd backend && python3 -m pytest -x` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python3 -m pytest tests/unit/test_catalog_prune.py -x`
- **After every plan wave:** Run `cd backend && python3 -m pytest tests/unit/ tests/integration/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-02-* | 02 | 1 | PRUNE-01 | — | Sub-threshold rows not deleted | unit | `pytest tests/unit/test_catalog_prune.py::test_sub_threshold_no_prune -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-01 | — | fetch_failure does not increment | unit | `pytest tests/unit/test_catalog_prune.py::test_fetch_failure_no_increment -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-02 | — | Counter 3 deletes row + audit | unit | `pytest tests/unit/test_catalog_prune.py::test_auto_prune_at_threshold -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-02 | — | Failed sync resets counters | unit | `pytest tests/unit/test_catalog_prune.py::test_reset_on_failed_sync -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-02 | — | Unreachable provider no increment | unit | `pytest tests/unit/test_catalog_prune.py::test_no_increment_when_unreachable -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-02 | — | Recovery clears counter | unit | `pytest tests/unit/test_catalog_prune.py::test_clear_on_recovery -x` | ❌ W0 | ⬜ pending |
| 10-03-* | 03 | 2 | PRUNE-02 | — | ProviderNotFound increments when reachable | unit | `pytest tests/unit/test_catalog_prune.py::test_not_found_increments -x` | ❌ W0 | ⬜ pending |
| 10-06-* | 06 | 5 | PRUNE-03 | T-10-01 | manual_removed on delete | integration | `pytest tests/integration/test_playlists_api.py::test_manual_removed_audit -x` | ❌ W0 | ⬜ pending |
| 10-06-* | 06 | 5 | PRUNE-03 | T-10-01 | recent_prune_events in detail GET | integration | `pytest tests/integration/test_playlists_api.py::test_prune_events_in_detail -x` | ❌ W0 | ⬜ pending |
| 10-02-* | 02 | 1 | PRUNE-03 | — | Audit retention max 50 | unit | `pytest tests/unit/test_catalog_prune.py::test_audit_retention_50 -x` | ❌ W0 | ⬜ pending |
| 10-03-* | 03 | 2 | PRUNE-04 | — | empty_snapshot warning preserved | unit | `pytest tests/unit/test_orchestrator.py::test_empty_snapshot_row_warning` | ✅ | ⬜ pending |
| 10-03-* | 03 | 2 | PRUNE-04 | — | fetch_failure warning preserved | unit | `pytest tests/unit/test_orchestrator.py::test_row_skip_on_fetch_failure` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_catalog_prune.py` — PRUNE-01/02/03 unit cases
- [ ] `backend/tests/integration/test_playlists_api.py` — prune embed + manual_removed (extend or add tests)
- [ ] Update `tests/unit/test_orchestrator.py` mocks for `FetchResult` return type

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No prune UI / silent removal | PRUNE-01, D-12–14 | No new SPA surfaces | Confirm playlist edit UI unchanged; row disappears on reload after 3/3 in staging |
| Rebuild banner copy unchanged | PRUNE-04, D-13 | Copy regression | Visual check `RebuildBanner.tsx` text vs prior release |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
