# Phase 10: Safe catalog prune - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 10-Safe catalog prune
**Areas discussed:** Safety policy thresholds, Stale detection signal, Operator visibility & control, Audit trail shape

---

## Safety policy thresholds

| Option | Description | Selected |
|--------|-------------|----------|
| 2 syncs | Faster cleanup | |
| 3 syncs | Balanced default | ✓ (initial threshold) |
| 5 syncs | Very conservative | |
| Reset on failed sync | Counter to 0 for connection | ✓ |
| Pause only | Freeze counter | |
| First post-sync absence | Streak start signal | ✓ |
| End of catalog sync | Prune trigger | ✓ (extended) |
| Hybrid rebuild + sync | Nightly sync, rebuild evidence, 3/3 | ✓ |
| Session + nightly triggers | More sync cadence | (partial — nightly sync before rebuild) |

**User's choice:** 3 qualifying events; reset on unhealthy sync; streak starts post-sync absence; hybrid policy (option 1) — catalog sync before nightly rebuild; rebuild counts when provider reachable and show is gone; auto-prune at end of successful sync or rebuild.
**Notes:** User concerned about “3 logins” — clarified syncs ≠ logins. Rebuild already hits provider per show but did not count until hybrid decision.

---

## Stale detection signal

| Option | Description | Selected |
|--------|-------------|----------|
| Columns on playlist_series_rows | Persist counters/flags | ✓ |
| Separate table | Normalized state | |
| After first evidence | Internal stale at ≥1 | ✓ (backend only) |
| Same treatment scope vs deleted | One policy | ✓ |
| Clear on recovery | Reset counter immediately | ✓ |

**User's choice:** Columns on rows; internal stale at first evidence; same rules for scope vs removal; auto-clear on recovery.
**Notes:** Later overridden for **visibility** — user does not want operator to see/manage stale state (see Area 3).

---

## Operator visibility & control

| Option | Description | Selected |
|--------|-------------|----------|
| Stale badge on editor/detail | Visible stale UX | (rejected by user) |
| Same row actions only | No prune UI | ✓ |
| Leave rebuild banner as-is | No new copy | ✓ |
| Silent auto-prune | No toast | ✓ |

**User's choice:** “I don't want the user to know or manage this” — same options as any playlist row; no stale badges or prune actions; banner unchanged; silent removal.
**Notes:** PRUNE-01 interpreted as safe non-destructive behavior + existing rebuild warnings, not new labels.

---

## Audit trail shape

| Option | Description | Selected |
|--------|-------------|----------|
| playlist_prune_events table | DB audit | ✓ |
| Embed on playlist detail GET | recent_prune_events[] | ✓ |
| Material events only | auto_pruned, manual_removed, optional cleared | ✓ |
| Last 50 per playlist | Retention | ✓ |

**User's choice:** Dedicated events table; embed recent slice on playlist API; material events only; cap 50 per playlist.

---

## Claude's Discretion

- Schema field names, migration details, structlog mirroring, nightly job ordering implementation.

## Deferred Ideas

- Phase 11 diagnostics modal for human-readable prune/rebuild detail.
- Explicit catalog sync button on playlist pages.
- Toasts on auto-prune (rejected).
