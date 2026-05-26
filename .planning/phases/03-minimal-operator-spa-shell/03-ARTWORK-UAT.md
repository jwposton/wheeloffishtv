---
status: resolved
phase: 03-minimal-operator-spa-shell
source: fix(03-08) local poster cache — commit 1dd8390
started: 2026-05-25T18:00:00Z
updated: 2026-05-25T23:45:00Z
---

## Current Test

complete — all tests passed

## Tests

### 1. Stack rebuilt with poster cache
expected: App rebuilt with commit 1dd8390. Health check passes. `/data/artwork` exists in container.
result: pass
notes: "Auto-verified: 92 pytest pass, health OK, /data/artwork present (0 files until sync)"

### 2. Catalog sync populates local poster cache
expected: As admin, trigger catalog sync (Settings or wait for boot sync). After sync completes, poster files appear under `/data/artwork/{connection_id}/` in the container. Browse grid shows posters for all series.
result: pass
notes: "Group 1 UAT pass — user confirmed 2026-05-25"

### 3. Admin browse posters
expected: Signed in as admin, open `/browse`. Every series card shows a visible poster image (no broken-image icons).
result: pass
notes: "Group 1 UAT pass — user confirmed 2026-05-25"

### 4. Non-admin browse posters (no token elevation)
expected: Sign in as a home/managed Plex user (non-admin). Open `/browse`. Posters match admin view — all visible. DevTools Network tab: poster requests go to `/api/v1/connections/.../series/.../artwork` and return 200 with image/jpeg (not 401/404 from Plex).
result: pass
notes: "Retest pass — user confirmed 2026-05-25. Prior issue (posters only visible after admin scroll) no longer reproduces."
reported: "Non-admin only sees posters admin already scrolled to — cache populated on-demand during admin browse, not full sync"
severity: major
root_cause: "Sync downloaded posters inline per chunk without a completion backfill; failures left gaps. Admin browse lazy-fill cached visible rows; non-admin cannot lazy-fill with home-user token."
fix: "Post-sync backfill_artwork_for_connection downloads all in-scope posters with sync user token before marking sync complete"

### 5. Lazy backfill on cache miss (optional)
expected: If a series had no poster at sync time, first load as a user who CAN see that show on Plex may fetch once via their token; subsequent loads serve from disk. Users who cannot see the show get placeholder/404 — no admin escalation.
result: pass
notes: "Group 1 UAT pass — user confirmed 2026-05-25"

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

### Gap: Non-admin poster visibility (Test 4)
status: resolved
severity: major
fix: Post-sync `backfill_artwork_for_connection` — download all in-scope posters with sync user token before marking sync complete
resolved: "Retest pass 2026-05-25 — non-admin browse posters match admin view"
