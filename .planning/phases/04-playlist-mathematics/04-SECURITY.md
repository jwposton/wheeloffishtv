---
phase: 04
slug: playlist-mathematics
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-25
verified: 2026-05-25
---

# Phase 4 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Domain ↔ Orchestrator (Phase 5) | `PlaylistBuilder.build()` receives in-memory Pydantic snapshots from a trusted caller | Playlist config, episode metadata, rebuild seed — no network I/O in Phase 4 |
| Domain ↔ ResumeService | Completion and ordered pickers delegate resume math to Phase 2 service | Series ID, episode list, on-deck pointer |
| Mappers ↔ Provider payloads | Plex/Jellyfin mappers parse optional `last_viewed_at` from existing episode fetch | Provider timestamps (already user-scoped media metadata) |

Phase 4 is **pure domain logic** — no HTTP endpoints, DB writes, auth surface, or scheduler in this phase.

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-01-01 | Tampering | domain/playlist.py | mitigate | `Field(ge=1)` on `episode_count`; builder returns empty result when zero active rows after completion (builder.py:90–97) | closed |
| T-04-01-SC | Tampering | pip/uv deps | accept | No new runtime deps in Wave 0 | closed |
| T-04-02-01 | Tampering | multipart.py | mitigate | Pure functions over Episode DTO; deterministic sort tiebreakers (part_index, id) | closed |
| T-04-02-02 | Information Disclosure | multipart.py | accept | No PII; no auth surface in pure-domain module | closed |
| T-04-02-SC | Tampering | pip/uv deps | accept | No new runtime deps | closed |
| T-04-03-01 | Tampering | completion.py | mitigate | Pure functions; `ResumeService().compute()` sole completion source (completion.py:23) | closed |
| T-04-03-02 | Repudiation | RowBuildOutcome | mitigate | `policy_applied` field records which policy fired (playlist.py:63, completion.py:40–71) | closed |
| T-04-03-SC | Tampering | pip/uv deps | accept | No new runtime deps | closed |
| T-04-04-01 | Tampering | ordered.py cursor state | mitigate | `@dataclass(frozen=True) OrderedCursor`; new cursor returned per slot (ordered.py:20–21, builder.py:142) | closed |
| T-04-04-02 | Denial of Service | ordered.py next_block | mitigate | Returns `([], index)` at exhaustion; `assert block` when index < len; index advances by ≥1 (ordered.py:51–65) | closed |
| T-04-04-SC | Tampering | pip/uv deps | accept | No new runtime deps | closed |
| T-04-05-01 | Tampering | last_viewed_at parsing | mitigate | Plex/Jellyfin mappers wrap timestamp parse in try/except → None on failure | closed |
| T-04-05-02 | Information Disclosure | last_viewed_at | accept | Field mirrors provider data already available via episode endpoints; no new exposure surface | closed |
| T-04-05-03 | Tampering | disordered pool determinism | mitigate | `pick_disordered_block` accepts caller-owned `random.Random`; no `time.time()` or global random (disordered.py:46, builder.py:29–34) | closed |
| T-04-05-04 | Denial of Service | disordered picker loop | mitigate | Single-call picker returns one block; slot iteration bounded by `episode_count` in builder | closed |
| T-04-05-SC | Tampering | pip/uv deps | accept | No new runtime deps | closed |
| T-04-06-01 | Tampering | builder.py | mitigate | Early return when `not active_series_ids` after completion filter; Pydantic `ge=1` on episode_count | closed |
| T-04-06-SC | Tampering | pip/uv deps | accept | No new runtime deps | closed |

*Status: closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-01-SC, T-04-02-SC, T-04-03-SC, T-04-04-SC, T-04-05-SC, T-04-06-SC | Phase 4 adds no new pip/uv runtime dependencies — stdlib + existing project deps only | security audit | 2026-05-25 |
| AR-04-02 | T-04-02-02 | Pure-domain multipart module contains no PII and exposes no auth surface | security audit | 2026-05-25 |
| AR-04-03 | T-04-05-02 | `last_viewed_at` on Episode DTO reflects provider metadata already returned by ingestion; Phase 5 must enforce auth on any new API exposing it | security audit | 2026-05-25 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-25 | 18 | 18 | 0 | gsd-secure-phase orchestrator |

### Security Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Threats found | 18 |
| Closed | 18 |
| Open | 0 |

**Evidence:** All 6 PLAN.md `<threat_model>` registers parsed. Mitigations verified against implementation in `domain/playlist.py`, `core/playlist/*`, and Plex/Jellyfin mappers. No SUMMARY.md threat flags reported.

**Advisory (non-blocking):** Code review CR-01 — empty episode snapshot treated as series-complete under default REMOVE — logged in `04-REVIEW.md` and `04-VERIFICATION.md` for Phase 5 orchestration guard; not a Phase 4 auth/STRIDE gap.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-25
