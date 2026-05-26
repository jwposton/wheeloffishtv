---
phase: 4
slug: playlist-mathematics
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-25
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 + pytest-asyncio ≥0.24 |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && uv run pytest tests/unit/test_playlist_builder.py tests/unit/test_multipart.py -q` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run module-scoped pytest for touched test file
- **After every plan wave:** Run `cd backend && uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | PLT-01–04 | T-04-01-01 | Pydantic rejects N=0 | unit | `pytest tests/unit/test_playlist_models.py -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | SCH-02 | — | Multipart blocks contiguous | unit | `pytest tests/unit/test_multipart.py -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | PLT-06 | — | remove/restart/disordered policies | unit | `pytest tests/unit/test_completion_policies.py -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 3 | PLT-05 | — | Ordered serial from resume | unit | `pytest tests/unit/test_ordered_picker.py -x` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 4 | PLT-04 | — | Disordered last-15 + seed stability | unit | `pytest tests/unit/test_disordered_picker.py -x` | ❌ W0 | ⬜ pending |
| 04-06-01 | 06 | 5 | PLT-02 | — | End-to-end builder slot allocation | unit | `pytest tests/unit/test_playlist_builder.py -x` | ❌ W0 | ⬜ pending |
| 04-07-01 | 07 | 6 | ROADMAP | — | Hypothesis property invariants (optional) | property | `pytest tests/unit/test_playlist_properties.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/fixtures/playlist_vectors.py` — episode factories with multipart helpers
- [ ] `backend/src/wheeloffish/domain/playlist.py` — config + result models
- [ ] `backend/src/wheeloffish/core/playlist/` — package scaffold
- [ ] Optional: `uv add --dev hypothesis` — property tests Wave 6

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
