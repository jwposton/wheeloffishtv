---
phase: 09
slug: series-detail-watch-state-from-playlists-library-view-edit-p
status: draft
updated: 2026-05-28
---

# Phase 09 Validation Strategy

## Validation Architecture

Phase 09 validation covers parity across Library/view-playlist/edit-playlist entry points plus provider-backed watch-state mutation correctness for Plex and Jellyfin.

## Requirement Mapping

| Requirement | Validation Focus | Evidence Type |
|-------------|------------------|---------------|
| WEB-01 | Series detail parity + playlist edit/view UX flows | Vitest component/page tests + manual UAT |
| INT-01 | Provider mutation integration behavior | Backend unit + integration tests |
| INT-02 | Scoped catalog/watch-state correctness | API contract tests + UAT |

## Mandatory UAT Checks

- T-09-01: Plex season-level bulk watch/unwatch behavior confirmed against real server
- T-09-02: Plex GUID-to-ratingKey mutation round-trip confirmed
- T-09-03: Jellyfin season bulk mark played/unplayed confirmed
- T-09-04: Jellyfin series bulk mark played/unplayed confirmed

## Automation Baseline

- Backend: provider adapter and API mutation tests
- Frontend: series detail grouping/status/action tests and playlist edit parity tests
- Full run gate: backend + frontend suites pass before phase verification
