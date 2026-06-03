---
status: complete
phase: 11-sync-rebuild-diagnostics
source: 11-01-SUMMARY.md, 11-02-SUMMARY.md, 11-03-SUMMARY.md, 11-04-SUMMARY.md, 11-05-SUMMARY.md, 11-06-SUMMARY.md, 11-07-SUMMARY.md, 11-08-SUMMARY.md
started: 2026-06-02T12:00:00Z
updated: 2026-06-02T22:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. View details trigger on warning/error runs
expected: On playlist detail with partial/failed rebuild, writeback warn/error, or slots_filled < slots_requested, "View details" link at panel bottom; not on list cards.
result: pass

### 2. View details hidden on clean success
expected: When latest rebuild and writeback are both successful (no warnings/errors) and slots are fully filled, "View details" does not appear on playlist detail.
result: pass

### 3. Compact rebuild banner
expected: Playlist detail banner shows status badges and one-line summaries only — no bulleted per-episode warning lists and no standalone failed-rebuild error paragraph in the banner.
result: pass

### 4. Playlist list cards unchanged
expected: On the playlists list, each card still shows compact writeback/rebuild badges only (no "View details" and no expanded diagnostic lists).
result: pass

### 5. Open diagnostics modal
expected: Clicking "View details" opens a scrollable "Rebuild diagnostics" dialog with a status badge and relative finish time (e.g. "Finished 2h ago") in the header.
result: pass

### 6. Modal sections and ordering
expected: Modal shows only non-empty sections in order — Rebuild (failed run error), Shows skipped, Episode sync, Prune history — each with titled rows (label, reason text, optional remediation hint). Sections with no data are omitted.
result: pass

### 7. Modal empty state
expected: If you open the modal when the run has no structured diagnostic rows and no prune events, you see "No detailed diagnostics available for this run" plus the finish timestamp — the dialog stays open (does not auto-close).
result: pass

### 8. Diagnostic row actions
expected: Rows that include actions from the API show inline link buttons (e.g. remove from playlist, open provider, view series). Clicking them performs the expected action (row removed with feedback, new tab for provider, or navigation to series detail without full page reload).
result: pass

### 9. Prune history in modal
expected: When the playlist has recent prune events (from catalog prune), a "Prune history" section lists them with reason text and a "View series" action — separate from rebuild run sections.
result: skipped
reason: Optional — only testable when prune events exist on a playlist.

## Summary

total: 9
passed: 8
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

- truth: "View details appears when latest rebuild is partial/failed or writeback is partial/failed"
  status: addressed
  reason: "Gap plans 11-06–11-08 shipped: underfill trigger, slot_unfilled warnings, resolver edge cases. Re-testing Test 1."
  severity: major
  test: 1
  artifacts: []
  missing: []
