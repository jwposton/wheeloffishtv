---
gsd_state_version: 1.0
milestone: v0.1.0
milestone_name: feature-complete MVP (provider writeback)
status: uat_complete
last_updated: "2026-05-28T02:27:55.535Z"
progress:
  total_phases: 9
  completed_phases: 8
  total_plans: 47
  completed_plans: 43
  percent: 89
---

# State — Wheel of Fish TV

**Updated:** 2026-05-26 (Phase 7 executed — provider writeback)

## Current phase

Phase **8 — UX polish & release readiness** — **complete** (reconciled from shipped releases).

**Release gate:** UAT passed 2026-05-26 — tag **v0.1.0**.

## Immediate next actions

1. Begin Phase 9 planning (`/gsd-plan-phase 9`)
2. Execute Phase 9 implementation
3. Verify Phase 9 flows (playlist detail/watch-state parity)

## Accumulated Context

### Roadmap Evolution

- Phase 9 added (2026-05-27): Series detail and watch state from playlists — Library / view-playlist / edit-playlist parity; edit pane “View series” + session-pinned new rows; episode list with watched / on-deck / unwatched and provider-backed watch edits; specials (S0) after seasons 1…N.

## Decisions (Phase 7 — plan 2026-05-25)

- **07-01:** Plex writeback via clear+replace items; guid→ratingKey resolution
- **07-02:** Jellyfin uses media item ids directly; entry ids for clear
- **07-03:** `provider_playlist_open_url` computed server-side; WritebackStatus component
- **Schema:** migration 009 — provider link on playlists, writeback audit on rebuild_runs

- Plex playlists are **server/account scoped** — no library picker
- Provider name **`{name} [WoF]`**; rename syncs; delete removes provider playlist
- **`provider_playlist_id`** on WheelOfFish playlist is ownership source of truth
- Create provider playlist on **first successful rebuild**; full item replace each rebuild
- Partial writeback OK — skip unmapped episodes with warnings
- UI: separate writeback status + **open in Plex/Jellyfin** link
- **Plex-first** for v0.1.0; Jellyfin in 07-02 wave if quick else v0.1.1

- **Phase 7 = provider playlist writeback** — push rebuild snapshots to native Plex/Jellyfin playlists; **v0.1.0 release gate**
- **Phase 8 = UX polish** — former Phase 7 scope deferred post-v0.1.0 (target v0.2.0)
- Export/push no longer out of scope for MVP — it is the delivery mechanism for playback in Plex/Jellyfin clients

- Import fixtures via `unit.fixtures` path for pytest testpaths compatibility
- Default `completion_event=SERIES_COMPLETE` per research assumption A4
- Null `part_index` anchor returns full block in forward expansion (D-07 fallback)
- Sort key `(part_index is None, part_index or 0, id)` for deterministic multipart ordering
- Playlist.default_completion_policy defaults to REMOVE; row policy wins at evaluation (D-14)
- Only SERIES_COMPLETE triggers in v1; season finish returns None (D-11)
- RESTART sets effective_mode=ORDERED; cursor reset via start_index_for_row(restart=True) (D-17)
- start_index_for_row skips ResumeService when restart=True, always returning 0
- Series complete returns len(order_episodes) as exhausted cursor index (D-21)
- next_block advances via max block member position in ordered list, not index + len(block)
- Episode.last_viewed_at defaults None; Plex lastViewedAt=0 maps to None (never-played sentinel)
- Malformed provider timestamps map to None via try/except — no ingestion exceptions
- Wave 3 builder must add every block member id to emitted_ids before next disordered pick (D-04, D-09)
- LAST_VIEWED_EXCLUSION_SIZE=15; tie-break equal last_viewed_at by id ascending
- SlotAllocation WILD/BALANCED/ROUND_ROBIN on Playlist; builder is stateless single entry point (D-23)
- PlaylistBuildResult.day_key stores opaque rebuild_seed; RNG from sha256(playlist.id:rebuild_seed) (D-24)
- episode_count defaults to 20; slot_allocation defaults to WILD (D-01, D-19)

## Decisions (Phase 3)

- WOF_PROVIDER drives single-provider installs; legacy WOF_ENABLED_PROVIDERS retained for multi-provider tests
- Session cookie https_only only when ENVIRONMENT=production
- ProtectedRoute requires has_media_link (not just session bootstrap)
- Storybook deferred to Phase 8 (D-20)

## Decisions (Phase 6 — planning)

- **WheelOfFish admin playlist cancelled** — ADM-01/ADM-02 removed; users manage own playlists
- **Browse nav → Library**; tiles get ⋯ + context menu / long-press for add-to-playlist
- **Series detail:** primary Add button + shared menu; enrich with provider metadata (summary, genres, rating) — no external IMDb API
- **Quick create:** inline name + Advanced… link to full form
- **Playlist edit:** two-pane tile picker (In | Available); row settings via bottom sheet; mobile tabs

## Decisions (Phase 6 — plan 05)

- SeriesProviderMetadata typed interface; hero omits null/empty fields (no N/A placeholders)
- Detail page primary Add to playlist reuses AddToPlaylistMenu with Button trigger (D-09)
- PLT-03 UX marked Complete in REQUIREMENTS after Phase 6 vertical slice ships

## Decisions (Phase 6 — plan 04)

- TwoPanePicker uses optimistic row mutations with revert on API failure (T-06-04-01)
- Create flow keeps rows local; edit flow uses incremental append/remove/patch APIs
- SeriesPicker removed; TwoPanePicker is sole playlist membership UI (D-21)
- Form page max-width widened to max-w-6xl for two-column picker layout

## Decisions (Phase 6 — plan 03)

- DropdownMenuTrigger `render` prop for tile ⋯ — avoids invalid nested buttons with base-ui
- Route stays `/browse`; nav label and page heading read Library (D-03)
- Quick create rejects empty trimmed name client-side (T-06-03-01)

## Decisions (Phase 6 — plan 02)

- Append row defaults match create: ordered/remove/series_complete
- Duplicate append returns 409; cross-user row ops return 404 via `_get_owned_playlist`
- sort_order=max(existing)+1 on append; PATCH requires at least one mutable field

## Decisions (Phase 6 — plan 01)

- Missing Plex metadata fields present as None/[] defaults — not omitted keys
- Jellyfin Phase 6 stubs defer real Overview/Genres mapping to Phase 8 polish spike (or Phase 7 if cheap)
- Genre extraction filters malformed entries; wrong-type string fields coerced to None via `_str_or_none`

## Decisions (Phase 5 — planning)

- **Install timezone (D-01 amendment 2026-05-25):** `WOF_INSTALL_TIMEZONE` (IANA, default UTC) + `WOF_REBUILD_CRON` (HH:MM local). Single cron job; weekly DOW in same TZ. Per-user timezone deferred.

## Decisions (Phase 5 — plan 01)

- SQLAlchemy proper constructors required in tests — `__new__` bypasses instance state initialization; use `Model(col=val, ...)` instead
- `rebuild_run.created_at` always-present; `started_at` nullable for queued state (job created before it begins)

## Decisions (Phase 5 — plan 02)

- `install_tz()` is a regular method (not computed_field) — ZoneInfo is not JSON-serialisable; avoids Pydantic serialization issues
- `orchestrator.py` created as stub no-op for 05-02; `run_nightly_rebuilds` fully implemented in 05-03
- `recover_interrupted_rebuilds` uses direct ORM query at startup (sync session from session_factory)

## Decisions (Phase 5 — plan 03)

- `run_nightly_batch(db, settings)` exposed as public for test isolation (avoids session factory mock)
- empty_snapshot rows excluded from valid_inputs — D-14: not treated as series_complete/REMOVE
- `row_outcomes_json` keys: `outcomes` (builder + fetch_warning annotations), `fetch_warnings` (list)
- `recover_interrupted_rebuilds` is sync; `rebuild_playlist` and `run_manual_rebuild` are async
- `SecretsVault` created inside `rebuild_playlist` from `get_settings()` — self-contained orchestrator

## Decisions (Phase 5 — plan 04)

- `_get_owned_playlist()` returns 404 for non-owner (not 403) to avoid existence leakage (D-18)
- Rebuild endpoint co-located in `playlists.py` with CRUD routes for cohesion
- Integration tests use `_set_user(user)` helper switching override inline per-call (avoids shared TestClient fixture collision)
- 409 `rebuild_in_progress` returned when a RebuildRun with status=running exists for the playlist

## Decisions (Phase 5 — plan 05)

- Inline `formatRelativeTime` helper in `PlaylistCard.tsx` — no date-fns dependency added (not in project; plan allowed ISO fallback)
- Route `/playlists` placed inside `LibraryScopeGuard` + `ProtectedRoute` at same level as `/browse` (D-20)

## Decisions (Phase 5 — plan 06)

- AlertDialog delete copy: 'This removes the playlist and its rebuild history. This cannot be undone.' (D-22, T-05-06-02)
- RebuildBanner error_message rendered as plain text JSX node only (T-05-06-03 XSS mitigation)
- SeriesPicker uses connection-scoped /connections/:id/series API with 20-item limit (D-25)
- Edit link uses Button render={<Link>} — pre-existing project convention (same as PlaylistCard)

## Working notes

- **Backlog:** `.planning/BACKLOG.md` (BL-01, BL-02 completed 2026-05-26)
- Phase 6 plan 05: `.planning/phases/06-library-playlist-assignment/06-05-SUMMARY.md`
- Phase 6 plan 04: `.planning/phases/06-library-playlist-assignment/06-04-SUMMARY.md`
- Phase 6 plan 03: `.planning/phases/06-library-playlist-assignment/06-03-SUMMARY.md`
- Phase 6 plan 02: `.planning/phases/06-library-playlist-assignment/06-02-SUMMARY.md`
- Phase 6 plan 01: `.planning/phases/06-library-playlist-assignment/06-01-SUMMARY.md`
- Phase 5 plan 06: `.planning/phases/05-orchestration-scheduling/05-06-SUMMARY.md`
- Phase 5 plan 05: `.planning/phases/05-orchestration-scheduling/05-05-SUMMARY.md`
- Phase 5 plan 04: `.planning/phases/05-orchestration-scheduling/05-04-SUMMARY.md`
- Phase 5 plan 03: `.planning/phases/05-orchestration-scheduling/05-03-SUMMARY.md`
- Phase 5 plan 02: `.planning/phases/05-orchestration-scheduling/05-02-SUMMARY.md`
- Phase 5 plan 01: `.planning/phases/05-orchestration-scheduling/05-01-SUMMARY.md`
- Phase 4 plan 06: `.planning/phases/04-playlist-mathematics/04-06-SUMMARY.md`
- Phase 4 plan 05: `.planning/phases/04-playlist-mathematics/04-05-SUMMARY.md`
- Phase 4 plan 04: `.planning/phases/04-playlist-mathematics/04-04-SUMMARY.md`
- Phase 4 plan 03: `.planning/phases/04-playlist-mathematics/04-03-SUMMARY.md`
- Phase 4 plan 02: `.planning/phases/04-playlist-mathematics/04-02-SUMMARY.md`
- Phase 4 plan 01: `.planning/phases/04-playlist-mathematics/04-01-SUMMARY.md`
- Phase 3 UAT: `.planning/phases/03-minimal-operator-spa-shell/03-UAT-CHECKLIST.md`
- Phase 2 complete: 7/7 plans
- Phase 1 complete: 5/5 plans

---

*Auto-maintain during `/gsd-transition` / `/gsd-progress`.*
