"""RED resolver contract tests for rebuild diagnostics (Phase 11 Plan 01).

These tests pin `build_rebuild_diagnostics` behavior before Plan 02 implements
`wheeloffish.core.rebuild_diagnostics`. Collection/import failure is expected until GREEN.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from wheeloffish.core.rebuild_diagnostics import (
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
) -> RebuildRun:
    return RebuildRun(
        id=str(uuid.uuid4()),
        playlist_id=str(uuid.uuid4()),
        status=status,
        error_message=error_message,
        row_outcomes_json=row_outcomes_json,
        writeback_warnings=writeback_warnings,
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


def test_failed_rebuild_populates_rebuild_error() -> None:
    run = _run(
        status="failed",
        error_message="Provider timeout during snapshot build",
    )
    ctx = _ctx()

    diagnostics = build_rebuild_diagnostics(run, ctx)

    assert diagnostics.rebuild_error is not None
    assert diagnostics.rebuild_error.reason_code == "rebuild_failed"
