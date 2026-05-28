# Requirements: Wheel of Fish TV

**Defined:** 2026-05-24  
**Core Value:** Pick N random TV slots across selected shows — but keep each ordered show aligned to true “resume / up-next”; disordered rows randomize feathers; users manage their own playlists via Library UX.

## v1 Requirements

### Integration (Plex / Jellyfin)

- [x] **INT-01**: Operator can register one configured **Plex** OR **Jellyfin** server (base URL + auth material) scoped to their account  
- [x] **INT-02**: System can enumerate **libraries** and **TV series** the user may attach to playlists (with paging/search to stay usable at scale)  
- [ ] **INT-03**: System maintains enough **episode + watch-position metadata** cache to compute “earliest unfinished / partial / next” reliably per series for **ordered** rows  
- [x] **EXP-01**: After each successful or partial rebuild, system **writes the emitted episode list** to a **native Plex or Jellyfin playlist** linked to the WheelOfFish playlist so users play output in their media client  

### Playlists & tuning

- [x] **PLT-01**: User can create **multiple named playlists**, each independently configured  
- [x] **PLT-02**: Each playlist declares **episode count `N`** to emit per rebuild cycle  
- [x] **PLT-03**: User adds/removes **TV series** to a playlist from enumerated library content  
- [x] **PLT-04**: Per **playlist × series** toggle: **`ordered`** (respect sequence from resume/next point) vs **`disordered`** (sample episodes ignoring sequence)  
- [x] **PLT-05**: For **ordered** rows, emitted episodes proceed **serially forward** beginning at the inferred **resume / up-next** position (handles partially watched installments)  
- [x] **PLT-06**: When a configurable **“completion event”** occurs (default: no remaining unseen episodes at series/season granularity — finalized in PLAN), user policy per playlist+series: **`remove`** (drop from future refreshes until re-added), **`restart`** (season/series rewind per rule), or **`disordered`** (keep series eligible with random feathers)  

### Scheduling & multipart

- [x] **SCH-01**: All playlists regenerate automatically on a **daily** schedule windows (timezone aware; specifics in PLAN phase)  
- [x] **SCH-02**: Detect **multipart/multi-part arcs** during selection; whenever any part qualifies for an **ordered** row, sibling parts must appear **adjacent**, in continuity order **within that refresh’s output**

### Administration

- ~~**ADM-01**~~ **Cancelled (2026-05-25):** Global WheelOfFish playlist — user creates own playlists instead  
- ~~**ADM-02**~~ **Cancelled (2026-05-25):** Admin-only WheelOfFish mutation — scope removed with ADM-01  

### Presentation (Web UI)

- [x] **WEB-01**: SPA covers **authentication**, connection setup, playlist CRUD, show membership, tuning flags (`ordered`/`disordered`, completion policies), **manual “rebuild now”**, surfaced job status/logs for last refresh, and **provider writeback status** once EXP-01 ships  

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
| First-class in-app playback | Consume via Plex/Jellyfin clients; WheelOfFish authors + exports playlists (EXP-01) |
| Licensed content scraping outside configured servers | Compliance & scope |
| Hosted multi-tenant SaaS billing | Explicit self-host persona |
| Global WheelOfFish admin playlist (ADM-01/02) | Cancelled 2026-05-25 — users manage their own playlists via Library UX (Phase 6) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase 1 | Complete |
| INT-02 | Phase 2 | Complete |
| INT-03 | Phase 2 | Pending |
| PLT-01 | Phase 4 | Complete |
| PLT-02 | Phase 4 | Complete |
| PLT-03 | Phase 4 | Complete |
| PLT-04 | Phase 4 | Complete |
| PLT-05 | Phase 4 | Complete |
| PLT-06 | Phase 4 | Complete |
| SCH-01 | Phase 5 | Complete |
| SCH-02 | Phase 5 | Complete |
| ADM-01 | — | Cancelled (2026-05-25) |
| ADM-02 | — | Cancelled (2026-05-25) |
| PLT-03 UX | Phase 6 | Complete (Library assignment + two-pane editor) |
| EXP-01 | Phase 7 | Complete (Plex + Jellyfin writeback) |
| WEB-01 | Phase 3 (+ Phase 8 polish tie-in) | Complete (writeback status UI pending EXP-01) |
| DEP-01 | Phase 1 | Pending |

**Coverage:**

- v1 requirements: **16** total  
- Mapped to phases: **16**  
- Unmapped: **0** ✓  

> **Note:** `WEB-01` deliberately spans SPA work starting once APIs exist — Phase 8 focuses on slick polish/accessibility/visual QA while Phase 3 delivers foundational screens. EXP-01 writeback status UI completes the functional WEB-01 slice in Phase 7.

---

*Requirements defined: 2026-05-24*  
*Last updated: 2026-05-25 after roadmap amendment (EXP-01 added; Phase 7 writeback = v0.1.0 gate)*
