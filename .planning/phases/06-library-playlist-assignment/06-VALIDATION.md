---
phase: 6
slug: library-playlist-assignment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-25
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 + pytest-asyncio ≥0.24 (backend); vitest 3.2.4 + @testing-library/react (frontend) |
| **Config file** | `backend/pyproject.toml` `[tool.pytest.ini_options]`; `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && uv run pytest tests/integration/test_playlists_api.py -x -q` |
| **Full suite command** | `cd backend && uv run ruff check . && uv run pytest && cd ../frontend && npm run test -- --run` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run module-scoped pytest or vitest for touched test file
- **After every plan wave:** Run `cd backend && uv run pytest tests/integration -q` + frontend component tests
- **Before `/gsd-verify-work`:** Full suite green + manual UAT for Library assignment flows
- **Max feedback latency:** 35 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | D-11 | T-06-01-01 | Plex map_series persists summary/genres/rating/studio | unit | `pytest tests/unit/test_plex_metadata_mapper.py -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | D-10 | — | Series detail API returns enriched provider_metadata | integration | `pytest tests/integration/test_catalog_api.py -k metadata -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | D-20, PLT-03 | T-06-02-01 | POST append row owner-scoped | integration | `pytest tests/integration/test_playlists_api.py -k append -x` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | D-20, PLT-03 | T-06-02-02 | DELETE row owner-scoped; 404 cross-user | integration | `pytest tests/integration/test_playlists_api.py -k remove -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 3 | D-19, D-04–D-06 | — | SeriesCard ⋯ + context menu stopPropagation | unit | `npm run test -- --run src/components/browse/SeriesCard.test.tsx` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 3 | D-08, D-09 | — | AddToPlaylistMenu quick-create + Advanced link | unit | `npm run test -- --run src/components/playlists/AddToPlaylistMenu.test.tsx` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 4 | D-13–D-17 | — | TwoPanePicker responsive tabs vs grid | unit | `npm run test -- --run src/components/playlists/TwoPanePicker.test.tsx` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 4 | D-16 | — | Row settings sheet opens from In pane | unit | `npm run test -- --run src/components/playlists/RowSettingsSheet.test.tsx` | ❌ W0 | ⬜ pending |
| 06-05-01 | 05 | 5 | D-03, D-10, WEB-01 | — | Library nav label + detail metadata hero | unit | `npm run test -- --run src/pages/SeriesDetailPage.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/unit/test_plex_metadata_mapper.py` — enriched map_series (D-11)
- [ ] `backend/tests/integration/test_playlists_api.py` — append/remove row endpoints (D-20)
- [ ] `frontend/src/components/playlists/AddToPlaylistMenu.test.tsx` — menu + quick create
- [ ] `frontend/src/components/playlists/TwoPanePicker.test.tsx` — two-pane + responsive
- [ ] `frontend/src/components/browse/SeriesCard.test.tsx` — context menu interactions

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Long-press opens menu on mobile | D-04 | Touch timing hard to simulate reliably | Open Library on phone; long-press tile; verify same menu as ⋯ |
| Two-pane side-by-side at md+ | D-17 | Visual layout breakpoint | Resize browser; verify columns at ≥768px, tabs below |
| Metadata displays after sync | D-10, D-11 | Requires live Plex library | Sync catalog; open series detail; verify summary/genres/rating |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 35s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
