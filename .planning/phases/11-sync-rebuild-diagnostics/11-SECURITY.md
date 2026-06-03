---
phase: 11
slug: sync-rebuild-diagnostics
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-03
---

# Phase 11 — Security

> Sync & rebuild diagnostics: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser ↔ API | Operator session cookie; playlist detail GET | `last_rebuild.diagnostics`, prune events, provider URLs |
| API ↔ DB | Owner-scoped playlist reads; row DELETE | Rebuild run JSON, series/episode IDs |
| API ↔ Media server | Provider open URL (server-built) | Connection `base_url`, playlist provider id |
| Diagnostics resolver | DB/orchestrator outcomes → display copy | `reason_text`, `error_message`, writeback warnings |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-11-01 | Information Disclosure (IDOR) | `GET /playlists/{id}` diagnostics embed | mitigate | `_get_owned_playlist` on detail route (`playlists.py:369`); diagnostics built only in `_playlist_to_detail` after ownership check; `remove_playlist_row` uses same gate (`playlists.py:535`); `test_get_other_users_playlist_404`, `test_playlist_detail_diagnostics` | closed |
| T-11-02 | Tampering (open redirect) | `open_provider` action | mitigate | URL from `_playlist_open_url` → `provider_playlist_open_url` only (`rebuild_diagnostics.py:153-161`); never from client/request; frontend `runDiagnosticAction` uses `window.open(..., "noopener,noreferrer")` (`rebuildDiagnostics.ts:51`) | closed |
| T-11-03 | Information Disclosure (XSS) | Modal/banner diagnostic text | mitigate | `RebuildDiagnosticsDialog` renders labels/reasons via React text nodes only (no `dangerouslySetInnerHTML` in playlists components); unknown writeback reasons map to catalog `writeback_warning` (`rebuild_diagnostics.py:131-140`); failed-run `error_message` shown as text in modal Rebuild section per D-07 | closed |
| T-11-SC | Tampering (supply chain) | npm/pip dependencies | accept | Phase added no new packages (per plan RESEARCH audit); reuses existing Dialog/Button/API stack | closed |

*Register authored at plan time (all 8 `*-PLAN.md` files include `<threat_model>`).*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-11-SC | T-11-SC | No new third-party packages in Phase 11; dependency surface unchanged from prior phases. | gsd-secure-phase | 2026-06-03 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-03 | 4 | 4 | 0 | gsd-secure-phase (inline verification) |

### Audit 2026-06-03

| Metric | Count |
|--------|-------|
| Threats found | 4 |
| Closed | 4 |
| Open | 0 |

**Evidence summary**

- **T-11-01:** `get_playlist` → `_get_owned_playlist` before `_playlist_to_detail`; diagnostics assignment at `playlists.py:235` inside detail builder only.
- **T-11-02:** `DiagnosticAction.url` set only from `ctx.provider_open_url`; integration tests in `test_provider_playlist_urls.py`.
- **T-11-03:** Grep: no `dangerouslySetInnerHTML` under `frontend/src/components/playlists/`; modal uses `{row.reason_text}` JSX text.
- **T-11-SC:** Accepted per plan disposition; no install tasks in phase plans.

**Unregistered flags:** None (no `## Threat Flags` in phase SUMMARY files).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-03
