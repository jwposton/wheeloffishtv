---
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
plan: 07
subsystem: api
tags: [fastapi, watch-state, auth, gap-closure, pytest]
gap_closure: true
requires:
  - phase: 09-02
    provides: Watch-state mutation routes and envelopes
provides:
  - Automated guardrail tests for unauthenticated, provider-auth, and cross-connection denial
  - UAT test 6 rerun evidence and operator checklist
affects: [catalog-api, uat]
tech-stack:
  added: []
  patterns:
    - HTTP 401 for missing app session on watch mutations
    - HTTP 200 failed envelope for provider auth and cross-scope targets
key-files:
  modified:
    - backend/tests/api/test_catalog_watch_mutations.py
    - .planning/phases/09-series-detail-watch-state-from-playlists-library-view-edit-p/09-UAT.md
requirements-completed: [INT-01, INT-02]
duration: 8min
completed: 2026-06-02
---

# Phase 9 Plan 07: Watch mutation guardrails gap closure Summary

**UAT test 6 is no longer skipped: API regression tests prove unauthenticated, provider-session, and cross-connection mutation paths fail deterministically.**

## Task Commits

1. **Task 1: API regression tests** — `test_watch_mutation_requires_app_authentication` added; existing unauthorized/cross-connection tests retained
2. **Task 2: UAT checklist** — `09-UAT.md` test 6 marked pass with automated evidence notes

## Operator checklist (live stack optional)

1. POST watch-state without session cookie → expect `401` / `unauthenticated`.
2. POST with expired provider token → expect `error_code: auth` envelope, zero updates.
3. POST with target id from another connection → expect `error_code: forbidden`.

## Automated Verification

- `cd backend && uv run pytest tests/api/test_catalog_watch_mutations.py -q` — 12 passed

## UAT

- Test 6 in `09-UAT.md`: **pass** (automated regression + documented manual steps)

## Self-Check: PASSED
