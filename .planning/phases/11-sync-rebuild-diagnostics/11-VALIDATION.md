---
phase: 11
slug: sync-rebuild-diagnostics
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-02
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 (backend), vitest (frontend) |
| **Config file** | `backend/pyproject.toml`; `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && python3 -m pytest tests/unit/test_rebuild_diagnostics.py -x` |
| **Full suite command** | `cd backend && python3 -m pytest tests/ -q` and `cd frontend && npm test -- --run` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Backend unit test for touched resolver codes; frontend component test if UI changed
- **After every plan wave:** `pytest tests/integration/test_playlists_api.py -q` + `npm test -- --run`
- **Before `/gsd-verify-work`:** Full backend + frontend suites green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-* | 01 | 0 | DIAG-02 | — | Resolver maps fetch_warning codes | unit | `pytest tests/unit/test_rebuild_diagnostics.py -x` | ❌ W0 | ⬜ pending |
| 11-02-* | 02 | 1 | DIAG-02 | T-11-01 | Diagnostics via owner-gated detail GET | integration | `pytest tests/integration/test_playlists_api.py::test_playlist_detail_diagnostics -x` | ❌ W0 | ⬜ pending |
| 11-02-* | 02 | 1 | DIAG-03 | — | Unknown label + id fallback | unit | `pytest tests/unit/test_rebuild_diagnostics.py::test_unknown_series_label -x` | ❌ W0 | ⬜ pending |
| 11-02-* | 02 | 1 | DIAG-04 | — | actions[] on show issues | unit | `pytest tests/unit/test_rebuild_diagnostics.py::test_show_issue_actions -x` | ❌ W0 | ⬜ pending |
| 11-03-* | 03 | 2 | DIAG-01 | — | View details trigger visibility | unit | `npm test -- --run RebuildBanner.test.tsx` | ❌ W0 | ⬜ pending |
| 11-03-* | 03 | 2 | DIAG-05 | — | No inline lists on detail | unit | `npm test -- --run WritebackStatus.test.tsx` | ❌ W0 | ⬜ pending |
| 11-04-* | 04 | 2 | DIAG-01–04 | — | Modal sections + empty state | unit | `npm test -- --run RebuildDiagnosticsDialog` | ❌ W0 | ⬜ pending |
| 11-* | * | * | PRUNE-03 | T-11-01 | recent_prune_events regression | integration | `pytest tests/integration/test_playlists_api.py::test_prune_events_in_detail -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_rebuild_diagnostics.py` — resolver + reason catalog
- [ ] `backend/tests/integration/test_playlists_api.py::test_playlist_detail_diagnostics`
- [ ] `frontend/src/components/playlists/RebuildDiagnosticsDialog.tsx` + tests
- [ ] `frontend/src/components/playlists/RebuildBanner.test.tsx`
- [ ] `frontend/src/components/playlists/WritebackStatus.test.tsx`
- [ ] `frontend/src/api/playlists.ts` — diagnostics + prune types

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Modal scroll + long issue lists | DIAG-02 | Visual density | Open playlist with partial rebuild; confirm sections scroll |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
