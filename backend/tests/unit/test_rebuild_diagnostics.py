"""Unit tests for rebuild diagnostics resolver (Phase 11 Plan 02)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from wheeloffish.core.rebuild_diagnostics import (
    REASON_CATALOG,
    DiagnosticsContext,
    build_rebuild_diagnostics,
)
from wheeloffish.db.models.rebuild_run import RebuildRun

SERIES_ID = "c::plex::s1"
EPISODE_ID = "c::plex::e1"


def _ctx(
    *,
    series_titles: dict[str, str] | None = None,
    episode_titles: dict[str, str] | None = None,
    provider_open_url: str | None = None,
) -> DiagnosticsContext:
    return DiagnosticsContext(
        series_title_map=series_titles or {},
        episode_title_map=episode_titles or {},
        provider_open_url=provider_open_url,
    )


def _run(
    *,
    status: str = "partial",
    error_message: str | None = None,
    row_outcomes_json: dict | None = None,
    writeback_warnings: list[dict] | None = None,
    writeback_status: str | None = None,
    writeback_error: str | None = None,
    snapshot_json: list[dict] | None = None,
) -> RebuildRun:
    return RebuildRun(
        id=str(uuid.uuid4()),
        playlist_id=str(uuid.uuid4()),
        status=status,
        error_message=error_message,
        row_outcomes_json=row_outcomes_json,
        writeback_warnings=writeback_warnings,
        writeback_status=writeback_status,
        writeback_error=writeback_error,
        snapshot_json=snapshot_json,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
    )


def test_fetch_failure_maps_to_show_issue() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [{"series_id": SERIES_ID, "reason": "fetch_failure"}],
        },
    )
    ctx = _ctx(series_titles={SERIES_ID: "Test Show"})

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 1
    row = diagnostics.show_issues[0]
    assert row.reason_code == "fetch_failure"
    assert row.series_id == SERIES_ID
    assert row.label == "Test Show"
    catalog = REASON_CATALOG["fetch_failure"]
    assert row.reason_text == catalog["reason_text"]
    assert row.remediation_hint == catalog["remediation_hint"]


def test_unknown_series_label() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [{"series_id": SERIES_ID, "reason": "fetch_failure"}],
        },
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 1
    row = diagnostics.show_issues[0]
    assert row.label == "Unknown show"
    assert row.series_id == SERIES_ID


def test_show_issue_actions() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [{"series_id": SERIES_ID, "reason": "fetch_failure"}],
        },
    )
    ctx = _ctx(series_titles={SERIES_ID: "Test Show"})

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 1
    actions = diagnostics.show_issues[0].actions
    assert len(actions) > 0
    action_types = {a.type for a in actions}
    assert "open_series" in action_types
    assert "remove_row" in action_types


def test_empty_snapshot_and_not_found_codes() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [
                {"series_id": "c::plex::empty", "reason": "empty_snapshot"},
                {"series_id": "c::plex::missing", "reason": "not_found"},
            ],
        },
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 2
    by_code = {r.reason_code: r for r in diagnostics.show_issues}
    assert "empty_snapshot" in by_code
    assert "not_found" in by_code
    assert (
        by_code["empty_snapshot"].reason_text
        == REASON_CATALOG["empty_snapshot"]["reason_text"]
    )
    assert by_code["not_found"].reason_text == REASON_CATALOG["not_found"]["reason_text"]


def test_writeback_404_normalizes_to_episode_not_found() -> None:
    run = _run(
        writeback_warnings=[
            {"episode_id": EPISODE_ID, "reason": "not found (404)"},
        ],
    )
    ctx = _ctx(episode_titles={EPISODE_ID: "Test Episode"})

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    row = diagnostics.episode_issues[0]
    assert row.reason_code == "episode_not_found"
    assert row.episode_id == EPISODE_ID
    assert row.label == "Test Episode"
    catalog = REASON_CATALOG["episode_not_found"]
    assert row.reason_text == catalog["reason_text"]


def test_writeback_unknown_reason_falls_back_to_writeback_warning() -> None:
    run = _run(
        writeback_warnings=[
            {"episode_id": EPISODE_ID, "reason": "Connection reset by peer"},
        ],
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    row = diagnostics.episode_issues[0]
    assert row.reason_code == "writeback_warning"
    assert row.reason_text == REASON_CATALOG["writeback_warning"]["reason_text"]


def test_writeback_info_notice_excluded() -> None:
    run = _run(
        writeback_warnings=[
            {
                "episode_id": None,
                "reason": "The linked Plex playlist was missing; a new one was created.",
            },
            {"episode_id": EPISODE_ID, "reason": "not found (404)"},
        ],
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    assert diagnostics.episode_issues[0].episode_id == EPISODE_ID


def test_episode_label_from_run_snapshot() -> None:
    run = _run(
        writeback_warnings=[{"episode_id": EPISODE_ID, "reason": "sync failed"}],
        snapshot_json=[
            {
                "episode_id": EPISODE_ID,
                "title": "Snapshot Episode Title",
                "series_id": SERIES_ID,
                "slot_index": 0,
                "row_mode": "ordered",
            },
        ],
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    assert diagnostics.episode_issues[0].label == "Snapshot Episode Title"


def test_unknown_episode_label() -> None:
    run = _run(
        writeback_warnings=[{"episode_id": EPISODE_ID, "reason": "sync failed"}],
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    row = diagnostics.episode_issues[0]
    assert row.label == "Unknown episode"
    assert row.episode_id == EPISODE_ID


def test_failed_rebuild_populates_rebuild_error() -> None:
    run = _run(
        status="failed",
        error_message="Provider timeout during snapshot build",
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert diagnostics.rebuild_error is not None
    assert diagnostics.rebuild_error.reason_code == "rebuild_failed"
    assert "Provider timeout" in diagnostics.rebuild_error.reason_text


def test_failed_rebuild_without_error_message_uses_catalog_fallback() -> None:
    run = _run(status="failed", error_message=None)
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert diagnostics.rebuild_error is not None
    assert diagnostics.rebuild_error.reason_code == "rebuild_failed"
    assert diagnostics.rebuild_error.reason_text == REASON_CATALOG["rebuild_failed"]["reason_text"]


def test_writeback_failed_without_episode_warnings() -> None:
    run = _run(
        writeback_status="failed",
        writeback_error="Plex API timeout",
        writeback_warnings=[],
    )
    ctx = _ctx(provider_open_url="https://app.plex.tv/playlist/1")

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.episode_issues) == 1
    row = diagnostics.episode_issues[0]
    assert row.reason_code == "writeback_failed"
    assert row.label == "Provider sync failed"
    assert "Plex API timeout" in row.reason_text


def test_slot_unfilled_maps_to_show_issue() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [{"series_id": SERIES_ID, "reason": "slot_unfilled"}],
        },
    )
    ctx = _ctx(series_titles={SERIES_ID: "Short Series"})

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 1
    row = diagnostics.show_issues[0]
    assert row.reason_code == "slot_unfilled"
    assert row.reason_text == REASON_CATALOG["slot_unfilled"]["reason_text"]


def test_unknown_fetch_reason_uses_fetch_failure_catalog() -> None:
    run = _run(
        row_outcomes_json={
            "outcomes": [],
            "fetch_warnings": [{"series_id": SERIES_ID, "reason": "legacy_unknown_code"}],
        },
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert len(diagnostics.show_issues) == 1
    row = diagnostics.show_issues[0]
    assert row.reason_code == "fetch_failure"
    assert row.reason_text == REASON_CATALOG["fetch_failure"]["reason_text"]


def test_non_failed_run_has_no_rebuild_error() -> None:
    run = _run(status="partial", error_message="leftover message")
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert diagnostics.rebuild_error is None


def test_open_provider_action_only_when_url_set() -> None:
    run = _run(
        status="failed",
        error_message="Build failed",
    )
    ctx = _ctx(provider_open_url="https://app.plex.tv/playlist/123")

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert diagnostics.rebuild_error is not None
    action_types = {a.type for a in diagnostics.rebuild_error.actions}
    assert "open_provider" in action_types
    provider_actions = [
        a for a in diagnostics.rebuild_error.actions if a.type == "open_provider"
    ]
    assert provider_actions[0].url == "https://app.plex.tv/playlist/123"
