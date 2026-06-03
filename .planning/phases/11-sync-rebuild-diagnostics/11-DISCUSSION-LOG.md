# Phase 11: Sync & rebuild diagnostics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 11-Sync & rebuild diagnostics
**Areas discussed:** trigger placement, inline vs modal, modal architecture, run history, remediation hints, API shape

---

## Trigger placement

| Option | Description | Selected |
|--------|-------------|----------|
| RebuildBanner only | One button on detail when rebuild/writeback partial/failed | ✓ |
| Detail + list cards | Also on playlist grid cards | |
| Two triggers | Separate rebuild vs sync buttons | |
| You decide | Claude picks | |

**User's choice:** RebuildBanner only (confirmed after clarifying no modal exists today)
**Notes:** Panel-level single link; visible on any rebuild or writeback warning/error; link-style button.

---

## Inline detail vs modal

| Option | Description | Selected |
|--------|-------------|----------|
| Move to modal | Remove inline lists; badge + summary in banner | ✓ |
| Keep both | Inline lists + richer modal | |
| Split by type | Show issues modal-only; episodes inline | |
| You decide | | |

**User's choice:** Move all granular detail to modal
**Notes:** Summary line only in banner; list cards unchanged; failed rebuild error_message also modal-only (badge in banner).

---

## Modal information architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Single scroll, sections | Rebuild → Shows → Episodes → Prune | ✓ |
| Tabs | Per-category tabs | |
| Severity-first | Errors then warnings | |
| You decide | | |

**User's choice:** Single scroll; hide empty sections; label + reason + hint rows; empty state in modal when no data.

---

## Run history scope

| Option | Description | Selected |
|--------|-------------|----------|
| Latest run only | Modal reflects last_rebuild | ✓ |
| Run picker | Switch among last 3 runs | |
| Latest + expand | Previous runs collapsed | |
| You decide | | |

**User's choice:** Latest run only; prune events playlist-scoped; defer run picker
**Notes:** User explicitly does not expect to need historical runs in UI — logs sufficient.

---

## Remediation hints & labels

| Option | Description | Selected |
|--------|-------------|----------|
| Backend resolves | API returns label, reason, hint | ✓ |
| Frontend maps | Client-side reason code map | |
| Hybrid | Backend labels, frontend hints | |
| You decide | | |

**User's choice:** Backend resolves; known codes only; hints + action buttons; label + subdued ID fallback

---

## API shape

| Option | Description | Selected |
|--------|-------------|----------|
| Embed on detail GET | diagnostics on last_rebuild | ✓ |
| Dedicated endpoint | Fetch on modal open | |
| Raw JSON passthrough | row_outcomes_json as-is | |
| You decide | | |

**User's choice:** Embed sectioned diagnostics on last_rebuild; API declares actions[] per row; recent_runs stay summary-only

---

## Claude's Discretion

Modal component sizing, exact hint copy, prune row mapping, remove-row confirm wiring from modal actions.

## Deferred Ideas

- Run picker / historical run comparison in UI
- Diagnostics trigger on playlist list cards
- Dedicated diagnostics endpoint
