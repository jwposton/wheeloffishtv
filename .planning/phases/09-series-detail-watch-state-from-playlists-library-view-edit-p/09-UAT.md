---
status: complete
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
source: [09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md]
started: 2026-05-28T03:11:00Z
updated: 2026-05-28T04:09:00Z
---

## Current Test

[testing complete]

## Tests

### 1. View series action from playlist edit row
expected: In playlist edit, opening a row menu in the In playlist pane shows a View series action that navigates to the shared series detail page for that show.
result: pass

### 2. Series detail back affordance returns to playlist edit context
expected: After opening series detail from playlist edit, the back affordance returns to the originating playlist edit flow (not generic library), with a sensible fallback only if context is invalid.
result: pass

### 3. Session-added rows prioritized with New badge
expected: In playlist edit, shows added during the current session appear at the top of the In playlist pane in add order and display a transient New badge.
result: pass

### 4. Watch-state API mutation updates a single target
expected: Sending a watched/unwatched mutation for one episode/season/series target to the catalog watch-state endpoint returns a successful normalized response envelope with updated counts and no failures.
result: pass

### 5. Watch-state API bulk mutation reports partial failures deterministically
expected: Sending a bulk mutation where some targets fail still returns a deterministic envelope with status plus updated_count, failed_count, failed_ids, and error_code fields.
result: pass

### 6. Watch-state mutation ownership and auth guardrails
expected: Mutation requests are rejected for unauthorized or cross-connection access with normalized auth/forbidden/not_found style error signaling instead of silent success.
result: skipped
reason: "skip"

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 1
blocked: 0

## Gaps

- truth: "Show add/remove actions remain immediate in view/edit flows, while playlist settings have explicit Save Settings / Cancel controls."
  status: failed
  reason: "User reported: changed requirement — keep add/remove immediate as before; move Save/Cancel to playlist settings only with explicit labels."
  severity: major
  test: 0
  artifacts: []
  missing:
    - "Revert staged-membership behavior so show add/remove persists immediately in view/edit flows"
    - "Scope Save/Cancel to playlist settings section only"
    - "Rename controls to explicit 'Save Settings' and 'Cancel' within playlist settings UI"

## Gap Closure Execution Notes (2026-05-27)

- Implemented fix for test 0 in `backend/src/wheeloffish/core/resume.py` and added regression in `backend/tests/unit/test_resume_service.py`.
- Implemented playlist detail "View series" parity and origin-aware back behavior for tests 1-2.
- Implemented no-scroll-jump guard for session-priority add flow (test 3).
- Implemented global watch-state mutation progress banner that persists across route changes (tests 4-5).
- Automated suites covering these paths pass locally; rerun UAT checklist to convert status from failed to passed.
