# Requirements: Wheel of Fish TV

**Defined:** 2026-05-24  
**Core Value:** Pick N random TV slots across selected shows — but keep each ordered show aligned to true “resume / up-next”; disordered rows randomize feathers; optional household WheelOfFish mode.

## v1 Requirements

### Integration (Plex / Jellyfin)

- [ ] **INT-01**: Operator can register one configured **Plex** OR **Jellyfin** server (base URL + auth material) scoped to their account  
- [ ] **INT-02**: System can enumerate **libraries** and **TV series** the user may attach to playlists (with paging/search to stay usable at scale)  
- [ ] **INT-03**: System maintains enough **episode + watch-position metadata** cache to compute “earliest unfinished / partial / next” reliably per series for **ordered** rows  

### Playlists & tuning

- [ ] **PLT-01**: User can create **multiple named playlists**, each independently configured  
- [ ] **PLT-02**: Each playlist declares **episode count `N`** to emit per rebuild cycle  
- [ ] **PLT-03**: User adds/removes **TV series** to a playlist from enumerated library content  
- [ ] **PLT-04**: Per **playlist × series** toggle: **`ordered`** (respect sequence from resume/next point) vs **`disordered`** (sample episodes ignoring sequence)  
- [ ] **PLT-05**: For **ordered** rows, emitted episodes proceed **serially forward** beginning at the inferred **resume / up-next** position (handles partially watched installments)  
- [ ] **PLT-06**: When a configurable **“completion event”** occurs (default: no remaining unseen episodes at series/season granularity — finalized in PLAN), user policy per playlist+series: **`remove`** (drop from future refreshes until re-added), **`restart`** (season/series rewind per rule), or **`disordered`** (keep series eligible with random feathers)  

### Scheduling & multipart

- [ ] **SCH-01**: All playlists regenerate automatically on a **daily** schedule windows (timezone aware; specifics in PLAN phase)  
- [ ] **SCH-02**: Detect **multipart/multi-part arcs** during selection; whenever any part qualifies for an **ordered** row, sibling parts must appear **adjacent**, in continuity order **within that refresh’s output**

### Administration

- [ ] **ADM-01**: **WheelOfFish** exists as a predefined **global** playlist (name fixed) assembling **random disordered episodes** from an admin-declared universe of libraries/shows usable by household accounts per policy finalized in PLAN  
- [ ] **ADM-02**: Only designated **admin principals** mutate WheelOfFish membership & parameters (role model finalized in PLAN)  

### Presentation (Web UI)

- [ ] **WEB-01**: SPA covers **authentication**, connection setup, playlist CRUD, show membership, tuning flags (`ordered`/`disordered`, completion policies), **manual “rebuild now”** (optional shortcut), and surfaced job status/logs for last refresh  

### Packaging

- [ ] **DEP-01**: Repository ships **Docker** artifacts (`Dockerfile`(s) + `compose.yml`) runnable with sane defaults documented in README  

## v2 Requirements

Deferred (not in roadmap v1):

- Automatic **near-real-time** watch sync vs nightly-only fidelity  
- **Multi-server fan-in** merging disparate Plex + Jellyfin homes into one UX row  
- **Mobile native** wrappers / PWA enhancements beyond responsive web  
- **Play history analytics** dashboards  

## Out of Scope

| Feature | Reason |
|---------|--------|
| First-class in-app playback | Consume via Plex/Jellyfin clients; MVP targets playlist authoring / export contract |
| Licensed content scraping outside configured servers | Compliance & scope |
| Hosted multi-tenant SaaS billing | Explicit self-host persona |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase 1 | Pending |
| INT-02 | Phase 2 | Pending |
| INT-03 | Phase 2 | Pending |
| PLT-01 | Phase 4 | Pending |
| PLT-02 | Phase 4 | Pending |
| PLT-03 | Phase 4 | Pending |
| PLT-04 | Phase 4 | Pending |
| PLT-05 | Phase 4 | Pending |
| PLT-06 | Phase 4 | Pending |
| SCH-01 | Phase 5 | Pending |
| SCH-02 | Phase 5 | Pending |
| ADM-01 | Phase 6 | Pending |
| ADM-02 | Phase 6 | Pending |
| WEB-01 | Phase 3 (+ Phase 7 polish tie-in) | Pending |
| DEP-01 | Phase 1 | Pending |

**Coverage:**

- v1 requirements: **15** total  
- Mapped to phases: **15**  
- Unmapped: **0** ✓  

> **Note:** `WEB-01` deliberately spans SPA work starting once APIs exist — Phase 7 focuses on slick polish/accessibility/visual QA while Phase 3 delivers foundational screens.

---

*Requirements defined: 2026-05-24*  
*Last updated: 2026-05-24 after initialization*
