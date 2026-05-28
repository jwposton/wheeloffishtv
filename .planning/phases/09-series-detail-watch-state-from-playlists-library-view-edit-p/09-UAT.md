---
status: complete
phase: 09-series-detail-watch-state-from-playlists-library-view-edit-p
source: [09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md]
started: 2026-05-28T03:11:00Z
updated: 2026-05-28T03:26:00Z
---

## Current Test

[testing complete]

## Tests

### 1. View series action from playlist edit row
expected: In playlist edit, opening a row menu in the In playlist pane shows a View series action that navigates to the shared series detail page for that show.
result: issue
reported: "hmm I don't see a view series action"
severity: major

### 2. Series detail back affordance returns to playlist edit context
expected: After opening series detail from playlist edit, the back affordance returns to the originating playlist edit flow (not generic library), with a sensible fallback only if context is invalid.
result: issue
reported: "oh wait. I see it on the edit screen but not the view screen"
severity: major

### 3. Session-added rows prioritized with New badge
expected: In playlist edit, shows added during the current session appear at the top of the In playlist pane in add order and display a transient New badge.
result: issue
reported: "so function works as designed badge and appears at top of list. Howevrer, user's view is also scrolled to the top of the page losing their place if they had scrolled down. User should not have focus/scroll changed."
severity: major

### 4. Watch-state API mutation updates a single target
expected: Sending a watched/unwatched mutation for one episode/season/series target to the catalog watch-state endpoint returns a successful normalized response envelope with updated counts and no failures.
result: issue
reported: "so it runs in teh background even as I change pages (which is fine, just need some indication that the update is running like \"executing update of Show/Season/Episode\" or something clear and concise maybe floating on the site?"
severity: major

### 5. Watch-state API bulk mutation reports partial failures deterministically
expected: Sending a bulk mutation where some targets fail still returns a deterministic envelope with status plus updated_count, failed_count, failed_ids, and error_code fields.
result: issue
reported: "pass same thing about progress as noted on test 4"
severity: major

### 6. Watch-state mutation ownership and auth guardrails
expected: Mutation requests are rejected for unauthorized or cross-connection access with normalized auth/forbidden/not_found style error signaling instead of silent success.
result: skipped
reason: "not sure how to test this as I can't do it"

## Summary

total: 6
passed: 0
issues: 5
pending: 0
skipped: 1
blocked: 0

## Gaps

- truth: "In playlist edit, opening a row menu in the In playlist pane shows a View series action that navigates to the shared series detail page for that show."
  status: failed
  reason: "User reported: hmm I don't see a view series action"
  severity: major
  test: 1
  artifacts: []
  missing: []
- truth: "After opening series detail from playlist edit, the back affordance returns to the originating playlist edit flow (not generic library), with a sensible fallback only if context is invalid."
  status: failed
  reason: "User reported: oh wait. I see it on the edit screen but not the view screen"
  severity: major
  test: 2
  artifacts: []
  missing: []
- truth: "In playlist edit, shows added during the current session appear at the top of the In playlist pane in add order and display a transient New badge."
  status: failed
  reason: "User reported: so function works as designed badge and appears at top of list. Howevrer, user's view is also scrolled to the top of the page losing their place if they had scrolled down. User should not have focus/scroll changed."
  severity: major
  test: 3
  artifacts: []
  missing:
    - "Preserve user scroll/focus position when reordering in-session rows"
- truth: "Sending a watched/unwatched mutation for one episode/season/series target to the catalog watch-state endpoint returns a successful normalized response envelope with updated counts and no failures."
  status: failed
  reason: "User reported: so it runs in teh background even as I change pages (which is fine, just need some indication that the update is running like \"executing update of Show/Season/Episode\" or something clear and concise maybe floating on the site?"
  severity: major
  test: 4
  artifacts: []
  missing:
    - "Show a concise in-app progress indicator while watch-state mutation is running in background"
    - "Keep feedback visible across route changes until mutation resolves"
- truth: "Sending a bulk mutation where some targets fail still returns a deterministic envelope with status plus updated_count, failed_count, failed_ids, and error_code fields."
  status: failed
  reason: "User reported: pass same thing about progress as noted on test 4"
  severity: major
  test: 5
  artifacts: []
  missing:
    - "Show a concise in-app progress indicator while bulk watch-state mutation is running in background"
    - "Keep progress feedback visible across route changes until bulk mutation resolves"
