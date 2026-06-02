# Retrospective — Wheel of Fish TV

Living document updated at each milestone close.

---

## Milestone: v0.1.0 — feature-complete MVP (provider writeback)

**Shipped:** 2026-06-02  
**Phases:** 9 | **Plans:** 51 | **Tasks:** 88

### What Was Built

- End-to-end self-hosted TV playlist roulette: Plex/Jellyfin auth → catalog sync → playlist authoring → nightly rebuild → provider writeback
- Deterministic playlist builder with ordered/disordered rows, completion policies, and multipart adjacency
- Library-centric UX, two-pane editor, series detail with watch-state mutations
- Docker Compose deployment with CI and structured logging

### What Worked

- MVP vertical slices kept each phase shippable and testable
- Golden-vector property tests for playlist mathematics caught edge cases early
- Gap-closure plans (Phase 6, 9) efficiently closed UAT findings without re-planning whole phases

### What Was Inefficient

- REQUIREMENTS.md traceability lagged behind shipped work (INT-03, DEP-01 left Pending despite delivery)
- Human UAT/verification items accumulated across phases 5–6 without a single close-out session
- STATE.md body drifted from frontmatter during rapid Phase 7–9 execution

### Patterns Established

- Composite provider IDs + ResumeService as single resume semantics source
- Owner-scoped API with 404 (not 403) for cross-user resource access
- `{name} [WoF]` provider playlist naming and clear+replace writeback

### Key Lessons

- Ship writeback as the v0.1.0 gate — polish can follow without blocking self-host usability
- Backlog file (BL-*) is essential for post-release scope that doesn't belong in the active roadmap
- Milestone close should reconcile REQUIREMENTS traceability before archive

### Known Deferred at Close

7 items acknowledged — see STATE.md **Deferred Items**. Backlog BL-03–BL-06 scheduled for v0.2.0 planning.

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Human UAT debt at close |
|-----------|--------|-------|-------------------------|
| v0.1.0 | 9 | 51 | 7 acknowledged items |
