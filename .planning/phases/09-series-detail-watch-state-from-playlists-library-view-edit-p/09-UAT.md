---
status: complete
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
source: [09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md]
started: 2026-05-28T03:11:00Z
updated: 2026-05-28T04:30:00Z
---

## Tests

### 0. Save Settings scope (gap closure)
expected: Add/remove shows save immediately; Save Settings and Cancel apply only to playlist settings (name, counts, allocation, policies, refresh).
result: pass

### 0b. Playlist settings help text and configured refresh time (gap closure)
expected: |
  Refresh hint reads like "Refreshes playlist daily|weekly at [DOW if weekly] at {time} {timezone}".
  Slot allocation has a ? icon that opens a popup explaining Wild, Balanced, and Round-robin.
result: pass

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
result: pass
notes: |
  Automated API regression (`backend/tests/api/test_catalog_watch_mutations.py`):
  - `test_watch_mutation_requires_app_authentication` → HTTP 401 `unauthenticated` without session.
  - `test_watch_mutation_maps_unauthorized_provider_session` → envelope `error_code: auth`, no updates.
  - `test_watch_mutation_rejects_cross_connection_targets_as_forbidden` → envelope `error_code: forbidden`.
  Operator may still spot-check with curl against a live stack; steps documented in 09-07-SUMMARY.md.

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

## Gap Closure Execution Notes (2026-05-27)

- Implemented fix for S0 specials ordering in `backend/src/wheeloffish/core/resume.py` and added regression in `backend/tests/unit/test_resume_service.py`.
- Implemented playlist detail "View series" parity and origin-aware back behavior for tests 1-2.
- Implemented no-scroll-jump guard for session-priority add flow (test 3).
- Implemented global watch-state mutation progress banner that persists across route changes (tests 4-5).
- Playlist settings Save/Cancel scope, immediate membership mutations, `install_schedule` on auth me, simplified refresh hint, and slot-allocation ? help (tests 0, 0b).
