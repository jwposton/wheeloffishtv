# Roadmap — Wheel of Fish TV

**Milestone:** v1 self-host MVP  
**Mode default:** MVP vertical slices (per-phase **Mode:** mvp)

---

## Overview

Build a dockerized FastAPI/Python service backing a SPA that nightly rebuilds user-defined mixed-order TV playlists wired to Plex or Jellyfin watch state plus the global WheelOfFish admin playlist.

| Phase | Name | Goal | Req coverage |
|-------|------|------|---------------|
| 1 | 5/5 | Complete    | 2026-05-25 |
| 2 | Media ingestion & catalogs | Robust connectors enumerate libraries/episodes/watch progress cache | INT-01, INT-02, INT-03 |
| 3 | Minimal operator shell SPA | Thin vertical slice wired to Phase 2 APIs (connections + browse-only) launching React stack | WEB-01 (partial bootstrap) |
| 4 | Playlist mathematics | Core generators: ordered/disordered rows, multipart adjacency rules, completion policies | PLT-02…PLT-06 |
| 5 | Orchestration jobs | Persistence for playlists outputs, transactional rebuild, SCH daily trigger + SCH multipart enforcement | SCH-01, SCH-02, PLT/INT glue |
| 6 | Admin WheelOfFish | Global playlist + RBAC surfaced in UI/API | ADM-01, ADM-02 |
| 7 | UX polish pass | Motion, dark mode, dashboards of last rebuild, QA | WEB-01 completion |

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
**Goal:** Frontend bootstrapped, auth gate, wizard to paste server credentials, browsable show list read-only.  
**Mode:** mvp  
**UI hint:** yes  

**Success criteria**

1. User can sign in (local account — exact scheme in PLAN) and save first server config without CLI  
2. Series browser meets accessibility baseline keyboard nav  
3. Storybook/visual regression optional stub created for slick component tokens  

Requirements: WEB-01 (foundation)

---

### Phase 4: Playlist mathematics
**Goal:** Deterministic nightly builder respecting ordered vs disordered, completion policies, multipart adjacency proofs via property tests where feasible.  
**Mode:** mvp  

**Success criteria**

1. Golden-vector tests illustrate ordered traversal + disordered stochastic seed stability per day-key  
2. Multipart arcs never split incorrectly in ordered contexts  
3. Completion policies enumerated + covered by tests  

Requirements: PLT-01 … PLT-06

---

### Phase 5: Orchestration & scheduling
**Goal:** Persist results, enqueue daily jobs, resilient retries, observability.  
**Mode:** mvp  

**Success criteria**

1. Scheduler triggers deterministic rebuild respecting timezone config  
2. API returns last rebuilt snapshot + timestamps + failures surfaced to UI badges  
3. Failure isolation: one unhealthy playlist/server doesn’t deadlock others  

Requirements: SCH-01, SCH-02 (+ cross-cutting glue)

---

### Phase 6: Admin WheelOfFish
**Goal:** Specialized global playlist surfaced only to admins, always disordered semantics.  
**Mode:** mvp  

**Success criteria**

1. WheelOfFish visible & editable exclusively for admin cohort  
2. Non-admins consume output if entitled but cannot mutate definition  
3. Auditable change log minimal (who/when mutated membership)  

Requirements: ADM-01, ADM-02

---

### Phase 7: UX polish & release readiness
**Goal:** Elevate slick factor, tighten empty/error states, performance budgets, screenshots for README.  
**Mode:** mvp  
**UI hint:** yes  

**Success criteria**

1. Lighthouse / axe critical issues resolved baseline  
2. README quickstart validated on clean machine (<15 min excluding media server setup)  
3. DEMO GIF or loom script optional placeholder noted  

Requirements: WEB-01 (completion), residual polish tying earlier gaps

---

## Requirement coverage matrix (sanity)

- INT-\* covered Phases **1–2**  
- PLT-\* **4** primarily  
- SCH-\* **5**  
- ADM-\* **6**  
- WEB-\* **3 + 7**  
- DEP-\* **1**  

Everything mapped ✓  

---

*Roadmap authored: 2026-05-24*  
*Maintenance:* update via `/gsd-transition` + `/gsd-plan-phase`*
