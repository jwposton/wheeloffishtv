---
status: diagnosed
phase: 03-minimal-operator-spa-shell
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md
started: 2026-05-25T18:00:00Z
updated: 2026-05-25T19:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill running stack, start fresh. Server boots without errors, boot sync completes, homepage loads at `/`.
result: pass

### 2. Sign In via Media-Server OAuth
expected: Open `/login`. Complete Plex PIN OAuth or Jellyfin username/password sign-in (matching your `WOF_PROVIDER`). Session established; redirected to browse, setup, or holding page — not stuck on login wall.
result: pass

### 3. Admin Discovery Setup Screen
expected: On first login with `WOF_ADMIN_PROVIDER_USER_ID` unset, visit `/setup/admin`. Provider user ID displayed with copy button and restart instructions. Setup mode blocks admin library PUT until env var is set and container restarted.
result: pass

### 4. Admin Library Scope
expected: With admin env set and restarted, open Settings → Libraries or `/setup/libraries`. Toggle in-scope checkboxes, save. Refresh page — selected libraries remain in scope. Browse shows series from scoped libraries only.
result: pass

### 5. Browse Scoped TV Libraries
expected: Open `/browse` with scoped libraries. Poster grid loads series. Scroll down — additional pages load (infinite scroll). Type in search box — debounced filter narrows titles. Grid/list toggle switches layout.
result: issue
reported: "pass for admin; fail for non-admin — broken poster images on browse grid"
severity: major

### 6. Series Detail with Resume Preview
expected: From browse, open a series with watch history. Detail page shows series metadata and read-only resume/up-next preview (episode title, season/episode, watch state). No playlist or rebuild controls.
result: issue
reported: "series detail is blank returns after a longish wait: Resume preview — Could not load resume data for this series."
severity: major

### 7. Outcome — Catalog Data Verifiable
expected: As operator, you can confirm catalog data is trustworthy before playlist authoring — series titles/posters match your media server, search finds expected shows, resume pointer reflects your watch history.
result: issue
reported: "resume pointer not correct — see test 6 (Could not load resume data for this series)"
severity: major

### 8. Non-Admin Holding Page
expected: As a non-admin user before libraries are scoped, navigate to `/browse`. See holding page ("Admin hasn't finished setup") instead of an empty grid.
result: issue
reported: "without admin defined I see browse with shows populated instead of holding page"
severity: major

### 9. Sync Banner During Catalog Sync
expected: Trigger catalog sync (admin action or background). Stay on `/browse` during sync. Top banner shows "Updating library…"; stale cached series remain visible below.
result: pass

### 10. Keyboard Navigation on Browse Grid
expected: On `/browse` grid view, Tab through series cards until one is focused (visible focus ring). Press Enter on focused card — navigates to `/series/{id}` detail page.
result: pass

### 11. Light/Dark Theme Toggle and Persistence
expected: Toggle theme in header — switches immediately. Reload page — preference persists. With no saved preference, OS `prefers-color-scheme` is respected.
result: pass

### 12. Settings Read-Only Connection Display
expected: Open Settings. Shows connected server URL from configuration with instruction to edit `.env` + restart to change. No editable server URL or provider fields.
result: pass

### 13. Coverage — User Story Outcome Delivered
expected: Phase goal satisfied — operator can sign in via OAuth, browse scoped libraries with search/scroll, and inspect resume preview to verify catalog data before Phase 4 playlist work.
result: pass

## Summary

total: 13
passed: 9
issues: 4
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Open `/browse` with scoped libraries. Poster grid loads series with visible poster images for all authenticated users."
  status: failed
  reason: "User reported: pass for admin; fail for non-admin — broken poster images on browse grid"
  severity: major
  test: 5
  root_cause: "Artwork proxy (`GET /connections/{id}/artwork`) fetches Plex thumbs with the requesting user's OAuth token. Home/managed Plex users often lack permission on rating-key thumb paths cached during admin catalog sync, returning 401/404 while server-owner admin token succeeds."
  artifacts:
    - path: backend/src/wheeloffish/api/routes/catalog.py
      issue: "get_connection_artwork uses _build_provider_for_user only — no fallback for shared-library thumb paths"
    - path: backend/src/wheeloffish/core/media_artwork.py
      issue: "Rewrites thumb paths to per-session proxy URLs that inherit user token permissions"
    - path: frontend/src/components/browse/SeriesCard.tsx
      issue: "<img src> hits artwork proxy; broken when proxy returns error for non-admin token"
  missing:
    - "Artwork proxy should serve catalog thumbs with a token that can read library metadata (admin fallback or connection service token)"
    - "Add integration test: non-admin session can load artwork for cached series thumb path"
  debug_session: .planning/debug/non-admin-broken-posters.md

- truth: "From browse, open a series with watch history. Detail page shows series metadata and read-only resume/up-next preview (episode title, season/episode, watch state)."
  status: failed
  reason: "User reported: series detail is blank returns after a longish wait: Resume preview — Could not load resume data for this series."
  severity: major
  test: 6
  root_cause: "Resume endpoint makes sequential live Plex calls (guid→ratingKey twice, allLeaves, onDeck). Failures surface as 422 → frontend isError. Slow path + failures likely from resolve_guid_to_rating_key on `/library/all?guid=` when user token lacks access or guid lookup misses; cached provider_metadata.ratingKey is not used."
  artifacts:
    - path: backend/src/wheeloffish/api/routes/catalog.py
      issue: "get_series_resume calls list_episodes + get_on_deck_episode without sharing ratingKey resolution"
    - path: backend/src/wheeloffish/integrations/plex/client.py
      issue: "_rating_key_for_series re-resolves guid on every call; no use of cached ratingKey from sync"
    - path: frontend/src/hooks/useSeriesResume.ts
      issue: "422 from resume API maps to generic 'Could not load resume data' error state"
  missing:
    - "Resolve ratingKey once per request using cached provider_metadata.ratingKey when available"
    - "Parallelize episode list + on-deck fetch; return partial preview on on-deck-only success"
    - "Add API test for resume with home-user token against synced series"
  debug_session: .planning/debug/resume-preview-failure.md

- truth: "As operator, resume pointer reflects watch history — catalog data verifiable before playlist authoring."
  status: failed
  reason: "User reported: resume pointer not correct — see test 6 (Could not load resume data for this series)"
  severity: major
  test: 7
  root_cause: "Duplicate of test 6 — resume preview API failure blocks catalog verification outcome."
  artifacts:
    - path: backend/src/wheeloffish/api/routes/catalog.py
      issue: "Same resume endpoint failure as test 6"
  missing:
    - "Fix test 6 resume path (see test 6 missing items)"
  debug_session: .planning/debug/resume-preview-failure.md

- truth: "As a non-admin user before libraries are scoped, navigate to `/browse` and see holding page instead of populated browse grid."
  status: failed
  reason: "User reported: without admin defined I see browse with shows populated instead of holding page"
  severity: major
  test: 8
  root_cause: "UAT scenario conflated setup_mode (WOF_ADMIN_PROVIDER_USER_ID unset) with libraries_scoped=false. LibraryScopeGuard gates on DB in_scope flags, not admin env. Prior admin library scoping (test 4) left libraries_scoped=true, so non-admin browse is correct per D-04. Re-test requires clearing all in_scope libraries first."
  artifacts:
    - path: frontend/src/routes/LibraryScopeGuard.tsx
      issue: "Shows HoldingPage only when libraries_scoped=false — working as designed"
    - path: backend/src/wheeloffish/core/auth.py
      issue: "libraries_scoped() is connection-level DB state, independent of setup_mode"
  missing:
    - "Re-run test 8 with zero in_scope libraries to confirm holding page"
    - "Optional UX: banner in setup_mode explaining browse is available because libraries were previously scoped"
  debug_session: .planning/debug/holding-page-setup-mode.md
  note: "Re-test requires libraries_scoped=false — clear all in_scope flags in Settings → Libraries (or DB) before signing in as non-admin. setup_mode (WOF_ADMIN_PROVIDER_USER_ID unset) is independent of libraries_scoped; prior admin scoping leaves browse populated by design (D-04)."
