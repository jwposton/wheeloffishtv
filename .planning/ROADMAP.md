# Roadmap — Wheel of Fish TV

**Milestone:** v0.1.0 feature-complete self-host release (provider writeback) → v0.2.0 polish  
**Mode default:** MVP vertical slices (per-phase **Mode:** mvp)

---

## Overview

Build a dockerized FastAPI/Python service backing a SPA that nightly rebuilds user-defined mixed-order TV playlists wired to Plex or Jellyfin watch state.

| Phase | Name | Goal | Req coverage |
|-------|------|------|---------------|
| 1 | Foundations & packaging | Dockerized API, health, migrations, secrets scaffold | DEP-01, INT-01 (structural) | Complete 2026-05-25 |
| 2 | Media ingestion & catalogs | Robust connectors enumerate libraries/episodes/watch progress cache | INT-01, INT-02, INT-03 | Complete |
| 3 | Minimal operator SPA shell | 8/8 | Complete   | 2026-05-25 |
| 4 | 6/6 | Complete    | 2026-05-25 |
| 5 | 6/6 | Complete   | 2026-05-25 |
| 6 | 7/7 | Complete + gap closure    | 2026-05-26 |
| 7 | Provider playlist writeback | Push rebuilt snapshots to native Plex/Jellyfin playlists | EXP-01 | Complete 2026-05-26 |
| 8 | UX polish pass | Motion, dark mode, dashboards of last rebuild, QA | WEB-01 completion | post-v0.1.0 |
| 9 | Series detail & watch from playlists | 1/4 | In Progress|  |

*(Phase numbers align with REQ traceability columns — adjust if phasedown needed later.)*

---

### Phase 1: Foundations & packaging

**Goal:** As a self-host operator, I want to run docker compose up for Wheel of Fish TV, so that the API reports healthy with database and secrets wiring ready.  
**Mode:** mvp  

**Success criteria**

1. `docker compose up` exposes health endpoint & logs structured JSON baseline  
2. Migrations scaffold exist (Alembic or equivalent) proving DB round-trip  
3. Secret storage abstraction exists (stubbed KMS-like interface) anticipating INT auth materials  
4. Baseline lint/test CI job green  

Requirements: DEP-01, INT-01 (structural surfaces)

---

### Phase 2: Media ingestion & catalogs

**Goal:** Live connectivity to one backend (ship Plex first unless parity demand flips decision) plus normalized domain models bridging eventual Jellyfin.  
**Mode:** mvp  

**Success criteria**

1. Authenticated Plex session can list selectable TV libraries + episodes with stable IDs  
2. Cached watch percent / viewed flags sufficient to compute canonical resume pointers per series  
3. Parallel Jellyfin provider behind interface with identical returned DTOs (feature-flag ok if phased)  

Requirements: INT-01, INT-02, INT-03

---

### Phase 3: Minimal operator SPA shell

**Goal:** As a self-host operator, I want to sign in via Plex/Jellyfin OAuth and browse scoped TV libraries with resume preview, so that I can verify catalog data before playlist authoring.  
**Mode:** mvp  
**UI hint:** yes  
**Plans:** 8/8 plans complete

**Success criteria**

1. User signs in via media-server OAuth only (env-configured connection — no server wizard in UI)  
2. Admin scopes libraries in UI; non-admins see holding page until scoped  
3. Series browser: grid/list toggle, infinite scroll, debounced search, sync banner, detail with up-next preview  
4. Light/dark theme from day one; keyboard nav baseline on browse grid  
5. Storybook deferred to Phase 8 (D-20)  

**Plans:**
**Wave 1**

- [x] 03-01-PLAN.md — Session auth, env→DB boot sync, /auth/me, Wave 0 tests
- [x] 03-02-PLAN.md — OAuth refactor to env connection; session on callback; catalog auth
- [x] 03-03-PLAN.md — Vite/shadcn scaffold, SPA static serve, Docker multi-stage

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-04-PLAN.md — Login wall, admin discovery, read-only settings

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-05-PLAN.md — Library scope admin UI, first-run checklist, holding page

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-06-PLAN.md — Series browse: infinite scroll, search, sync banner, grid/list

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-07-PLAN.md — Series detail + resume preview, docs, UAT checklist

Requirements: WEB-01 (foundation)

---

### Phase 4: Playlist mathematics

**Goal:** Deterministic nightly builder respecting ordered vs disordered, completion policies, multipart adjacency proofs via property tests where feasible.  
**Mode:** mvp  
**Plans:** 6/6 plans complete

**Success criteria**

1. Golden-vector tests illustrate ordered traversal + disordered stochastic seed stability per day-key  
2. Multipart arcs never split incorrectly in ordered contexts  
3. Completion policies enumerated + covered by tests  

**Plans:**

**Wave 0**

- [x] 04-01-PLAN.md — Domain models, test fixtures, model validation

**Wave 1**

- [x] 04-02-PLAN.md — Multipart grouping and adjacency helpers (SCH-02)
- [x] 04-03-PLAN.md — Completion policies (PLT-06)

**Wave 2**

- [x] 04-04-PLAN.md — Ordered serial picker from resume (PLT-05)
- [x] 04-05-PLAN.md — Disordered picker + last_viewed_at mappers (PLT-04)

**Wave 3** *(blocked on Waves 1–2 completion)*

- [x] 04-06-PLAN.md — PlaylistBuilder integration + end-to-end golden vectors (PLT-01–06, SCH-02)

Requirements: PLT-01 … PLT-06

---

### Phase 5: Orchestration & scheduling

**Goal:** Persist results, enqueue daily jobs, resilient retries, observability.  
**Mode:** mvp  

**Success criteria**

1. Scheduler triggers deterministic rebuild respecting **install timezone** config (`WOF_INSTALL_TIMEZONE` + `WOF_REBUILD_CRON`)
2. API returns last rebuilt snapshot + timestamps + failures surfaced to UI badges  
3. Failure isolation: one unhealthy playlist/server doesn’t deadlock others  

Requirements: SCH-01, SCH-02 (+ cross-cutting glue)

**Wave 1**

- [x] 05-01-PLAN.md — Alembic schema, ORM models, domain mappers (PLT-01–03)

**Wave 2** *(blocked on Wave 1)*

- [x] 05-02-PLAN.md — APScheduler lifespan + cadence evaluation (SCH-01)

**Wave 3** *(blocked on Waves 1–2)*

- [x] 05-03-PLAN.md — Rebuild orchestrator, failure isolation, snapshot persist (SCH-02)

**Wave 4** *(blocked on Wave 3)*

- [x] 05-04-PLAN.md — Playlist REST CRUD + manual rebuild API (PLT-01–03, SCH-01)

**Wave 5** *(blocked on Wave 4)*

- [x] 05-05-PLAN.md — SPA playlist list + status badges (WEB-01)

**Wave 6** *(blocked on Wave 5)*

- [x] 05-06-PLAN.md — SPA create/edit, series picker, rebuild now, output view (WEB-01, PLT-03)

**Cross-cutting constraints:**

- `PlaylistBuilder.build()` is the sole rebuild entry point — manual and scheduled paths share orchestrator (D-06, D-23)
- Playlists scoped by `app_user_id`; owner-only rebuild (D-18, D-22)
- Failed rebuild retains last good snapshot; partial when any row skipped (D-11–D-12, D-17)

---

### Phase 6: Library & playlist assignment

**Goal:** As a self-host operator, I want to add shows to playlists from my Library and tune membership in a visual two-pane editor, **so that** playlist authoring feels like browsing my catalog—not filling out a search box.  
**Mode:** mvp  
**UI hint:** yes  

**Success criteria**

1. Nav reads **Library**; tiles expose add-to-playlist (⋯ + context menu / long-press)  
2. Series detail shows provider metadata (summary, genres, rating) plus primary add-to-playlist action  
3. Playlist create/edit uses **In playlist | Available** tile panes with name search; row settings via sheet  
4. Quick-create playlist from Library with inline name + Advanced form link  
5. ADM-01/ADM-02 (global WheelOfFish) **cancelled** — no admin-only global playlist  

Requirements: PLT-03 (membership UX completion), WEB-01 (Library assignment slice)

**Supersedes:** Former Phase 6 “Admin WheelOfFish” scope (2026-05-25 decision)

**Wave 1**

- [x] 06-01-PLAN.md — Plex/Jellyfin metadata mapper extension + catalog sync round-trip (D-10, D-11)

**Wave 2**

- [x] 06-02-PLAN.md — Row append/remove/patch API endpoints (D-20, PLT-03)

**Wave 3** *(blocked on Wave 2)*

- [x] 06-03-PLAN.md — Library nav rename, tile ⋯ menu, AddToPlaylistMenu + quick create (D-03–D-09, D-19)

**Wave 4** *(blocked on Waves 2–3)*

- [x] 06-04-PLAN.md — Two-pane tile picker, RowSettingsSheet, remove SeriesPicker (D-13–D-18, D-21)

**Wave 5** *(blocked on Waves 1, 3)*

- [x] 06-05-PLAN.md — Series detail metadata hero, Add to playlist on detail, docs cleanup (D-01, D-02, D-09, D-10, D-12)

**Gap closure** *(UAT diagnosed 2026-05-26)*

**Plans:** 2 gap-closure plans

- [x] 06-06-PLAN.md — Encode seriesId in row DELETE/PATCH URLs (CR-01 blocker)
- [x] 06-07-PLAN.md — In-pane posters, Advanced… menu, row context menu, sticky Save/Cancel

---

### Phase 7: Provider playlist writeback

**Goal:** As a self-host operator, I want each rebuilt WheelOfFish playlist to appear as a native Plex or Jellyfin playlist I can play in my media client, **so that** nightly output is consumable without manual copy-paste from the SPA.  
**Mode:** mvp  
**Release gate:** **v0.1.0** — feature-complete MVP after this phase validates  

**Success criteria**

1. After successful or partial rebuild, orchestrator pushes episode ordering to a linked provider playlist (create-on-first-rebuild if missing)  
2. Plex path uses stable playlist update API; Jellyfin path uses native playlist/items API (ship Plex-first if parity costly — same pattern as Phase 6 metadata)  
3. Rebuild run records writeback status (success / skipped / failed + error); UI surfaces last writeback alongside rebuild status  
4. Writeback failure does not discard persisted snapshot; operator can retry via manual rebuild  
5. Episode IDs in snapshot map deterministically to provider-native episode keys already used by catalog sync  

**Out of scope (Phase 7):** M3U/JSON export fallback (follow-up if APIs insufficient), bi-directional sync from provider edits, multi-playlist fan-out to multiple servers  

Requirements: EXP-01 (new), INT-01 glue  

**Supersedes:** Former Phase 7 “UX polish” slot — polish deferred to Phase 8 per 2026-05-25 decision  

**Next:** `/gsd-execute-phase 7` (or execute plans 07-01 → 07-03)

**Wave 1**

- [x] 07-01-PLAN.md — Schema, Plex playlist client, writeback service, orchestrator hook (EXP-01)

**Wave 2** *(blocked on Wave 1)*

- [x] 07-02-PLAN.md — Jellyfin playlist parity + push_snapshot dispatch

**Wave 3** *(blocked on Waves 1–2)*

- [x] 07-03-PLAN.md — Rename/delete lifecycle, SPA WritebackStatus + open link, UAT/validation (EXP-01, WEB-01)

---

### Phase 8: UX polish & release readiness

**Goal:** Elevate slick factor, tighten empty/error states, performance budgets, screenshots for README.  
**Mode:** mvp  
**UI hint:** yes  
**Release target:** v0.2.0 (post feature-complete v0.1.0)  

**Success criteria**

1. Lighthouse / axe critical issues resolved baseline  
2. README quickstart validated on clean machine (<15 min excluding media server setup)  
3. DEMO GIF or loom script optional placeholder noted  
4. Jellyfin metadata parity spike (deferred from Phase 6 stubs) if not done in Phase 7  
5. Storybook / visual regression stub (D-20)  

Requirements: WEB-01 (completion), residual polish tying earlier gaps

---

### Phase 9: Series detail & watch state from playlists

**Goal:** Library, view-playlist, and edit-playlist flows expose the same series detail experience as Library (tile → detail). Edit playlist: **View series** on in-playlist context menu; **Available** pane keeps click-to-add, with series added in the current session surfaced at the top of **In playlist** for clarity. Series detail lists catalog episodes grouped by season with clear **watched / on-deck / unwatched** affordances and context actions to update watch state per episode, season, or entire series via Plex/Jellyfin where APIs support it. **Default season ordering:** specials (season 0 / “Specials”) appear **after** seasons 1…N (not before).

**Mode:** mvp  
**UI hint:** yes  
**Depends on:** Phase 8  

**Success criteria** *(draft — refine in PLAN)*  

1. View playlist: series tiles navigate to the same detail route/pattern as Library.  
2. Edit playlist: in-playlist tile context menu includes **View series**; available-tile click still appends row; session-new memberships visually prioritized in the In playlist pane.  
3. Detail view: episodes grouped by season with watched / next-on-deck / unwatched indicators; context menus for bulk watch edits at episode, season, and series scope when the active provider allows.  
4. Season list default sort: numbered seasons ascending, specials (S0) last.  

**Requirements:** WEB-01 (playlist authoring UX), INT-01/02 (provider watch writeback where feasible)  
**Plans:** 1/4 plans executed
Plans:
**Wave 1**

- [x] 09-01-PLAN.md — Add provider watch-state mutation contract and Plex/Jellyfin adapter implementations
- [ ] 09-03-PLAN.md — Add playlist edit parity actions (View series) and session-new row prioritization

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 09-02-PLAN.md — Expose owner-scoped catalog watch mutation endpoints with outcome/error envelopes

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 09-04-PLAN.md — Complete series detail grouped watch UI and provider-backed action reconciliation

---

## Requirement coverage matrix (sanity)

- INT-\* covered Phases **1–2** (+ Phase **9** watch-writeback glue TBD)  
- PLT-\* **4** primarily  
- SCH-\* **5**  
- PLT-03 UX completion **6**  
- WEB-\* **3 + 6 + 8 + 9** (polish + playlist detail/watch)  
- EXP-\* **7** (provider writeback — v0.1.0 gate)  
- DEP-\* **1**  

Everything mapped ✓ *(Phase 9 row added 2026-05-27 — matrix to be tightened after planning)*  

---

## Release milestones

| Tag | Gate | Contents |
|-----|------|----------|
| **v0.1.0** | Phase 7 complete + validation | Authoring, rebuild, Library UX, **native Plex/Jellyfin playlist writeback** |
| **v0.2.0** | Phase 8 complete | UX polish, accessibility, README/DEMO hardening |
| **v0.3.0** *(proposed)* | Phase 9 complete | Series detail from playlists + watch-state editing + season ordering |

---

*Roadmap authored: 2026-05-24*  
*Amended: 2026-05-25 — Phase 7 = provider writeback (v0.1.0); Phase 8 = polish*  
*Amended: 2026-05-27 — Phase 9 = series detail & watch from playlists (post v0.2.0)*  
*Maintenance:* update via `/gsd-transition` + `/gsd-plan-phase`*
