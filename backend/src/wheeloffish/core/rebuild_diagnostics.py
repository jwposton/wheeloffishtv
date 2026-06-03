"""Resolve rebuild/writeback warnings into operator-facing diagnostic rows (Phase 11)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from wheeloffish.api.schemas.playlists import (
    DiagnosticAction,
    DiagnosticIssueRow,
    RebuildDiagnostics,
)
from wheeloffish.db.models.rebuild_run import RebuildRun

logger = structlog.get_logger(__name__)

UNKNOWN_SHOW_LABEL = "Unknown show"
UNKNOWN_EPISODE_LABEL = "Unknown episode"

REASON_CATALOG: dict[str, dict[str, Any]] = {
    "fetch_failure": {
        "reason_text": "Could not load episodes for this show from your media server.",
        "remediation_hint": (
            "Check that the series still exists on the provider, "
            "then remove the row or retry rebuild."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
            {"type": "remove_row", "label": "Remove from playlist"},
        ],
    },
    "empty_snapshot": {
        "reason_text": "No unwatched episodes were available for this show.",
        "remediation_hint": (
            "Mark episodes unwatched on the provider, adjust completion policy, "
            "or remove the row."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
            {"type": "remove_row", "label": "Remove from playlist"},
        ],
    },
    "not_found": {
        "reason_text": "This show was not found on your media server.",
        "remediation_hint": (
            "Confirm the series exists on the provider or remove the row from the playlist."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
            {"type": "remove_row", "label": "Remove from playlist"},
        ],
    },
    "slot_unfilled": {
        "reason_text": "This show had no eligible episodes for its slot in this rebuild.",
        "remediation_hint": (
            "Mark episodes unwatched on the provider, adjust completion policy, "
            "or remove the row."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
            {"type": "remove_row", "label": "Remove from playlist"},
        ],
    },
    "rebuild_failed": {
        "reason_text": "",  # filled from run.error_message
        "remediation_hint": (
            "Review the error below, fix provider connectivity or playlist configuration, "
            "then rebuild."
        ),
        "action_templates": [
            {"type": "open_provider", "label": "Open provider playlist"},
        ],
    },
    "writeback_failed": {
        "reason_text": "Episode sync to the provider playlist failed.",
        "remediation_hint": (
            "Open the provider playlist and verify permissions, then retry writeback or rebuild."
        ),
        "action_templates": [
            {"type": "open_provider", "label": "Open provider playlist"},
        ],
    },
    "episode_not_found": {
        "reason_text": "An episode in the rebuild snapshot was not found on the provider.",
        "remediation_hint": (
            "Confirm the episode still exists on the provider or remove the show row "
            "if it was deleted."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
        ],
    },
    "missing_episode_id": {
        "reason_text": "A snapshot row is missing an episode identifier.",
        "remediation_hint": (
            "Rebuild the playlist; if the issue persists, remove and re-add the affected show."
        ),
        "action_templates": [],
    },
    "writeback_warning": {
        "reason_text": "Episode sync reported a warning that could not be classified.",
        "remediation_hint": (
            "Check server logs for details, verify the episode on the provider, "
            "then rebuild if needed."
        ),
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
        ],
    },
    "catalog_sync": {
        "reason_text": "This show was removed during catalog sync.",
        "remediation_hint": "Re-add the series from the library if you still want it in rotation.",
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
        ],
    },
    "operator": {
        "reason_text": "This show was removed by an operator action.",
        "remediation_hint": "Add the series back to the playlist if removal was unintentional.",
        "action_templates": [
            {"type": "open_series", "label": "Open show"},
        ],
    },
}


@dataclass(frozen=True)
class DiagnosticsContext:
    series_title_map: dict[str, str]
    episode_title_map: dict[str, str]
    provider_open_url: str | None = None


def _episode_title_map(run: RebuildRun, ctx: DiagnosticsContext) -> dict[str, str]:
    """Merge caller titles with this run's snapshot_json (Pitfall 2)."""
    merged = dict(ctx.episode_title_map)
    for entry in run.snapshot_json or []:
        if not isinstance(entry, dict):
            continue
        episode_id = entry.get("episode_id")
        title = entry.get("title")
        if episode_id and title:
            merged[episode_id] = title
    return merged


def _catalog_entry(reason_code: str) -> dict[str, Any]:
    if reason_code in REASON_CATALOG:
        return REASON_CATALOG[reason_code]
    logger.warning("rebuild_diagnostics_unknown_reason_code", reason_code=reason_code)
    return REASON_CATALOG["writeback_warning"]


def _normalize_writeback_reason(raw: str) -> str:
    lowered = raw.lower()
    if "404" in lowered or "not found" in lowered or "not_found" in lowered:
        return "episode_not_found"
    if "missing_episode_id" in lowered:
        return "missing_episode_id"
    if raw in REASON_CATALOG:
        return raw
    logger.info("rebuild_diagnostics_unknown_writeback_reason", raw_reason=raw)
    return "writeback_warning"


def _build_actions(
    templates: list[dict[str, str]],
    *,
    series_id: str | None,
    episode_id: str | None,
    provider_open_url: str | None,
) -> list[DiagnosticAction]:
    actions: list[DiagnosticAction] = []
    for template in templates:
        action_type = template["type"]
        if action_type == "open_provider":
            if not provider_open_url:
                continue
            actions.append(
                DiagnosticAction(
                    type="open_provider",
                    label=template["label"],
                    url=provider_open_url,
                )
            )
        elif action_type == "open_series":
            if not series_id:
                continue
            actions.append(
                DiagnosticAction(
                    type="open_series",
                    label=template["label"],
                    series_id=series_id,
                    episode_id=episode_id,
                )
            )
        elif action_type == "remove_row":
            if not series_id:
                continue
            actions.append(
                DiagnosticAction(
                    type="remove_row",
                    label=template["label"],
                    series_id=series_id,
                )
            )
    return actions


def _resolve_show_issue(warning: dict, ctx: DiagnosticsContext) -> DiagnosticIssueRow:
    series_id = warning.get("series_id")
    raw_reason = warning.get("reason", "fetch_failure")
    reason_code = raw_reason if raw_reason in REASON_CATALOG else "fetch_failure"
    entry = _catalog_entry(reason_code)
    label = (
        ctx.series_title_map.get(series_id, UNKNOWN_SHOW_LABEL)
        if series_id
        else UNKNOWN_SHOW_LABEL
    )
    return DiagnosticIssueRow(
        label=label,
        reason_code=reason_code,
        reason_text=entry["reason_text"],
        remediation_hint=entry["remediation_hint"],
        series_id=series_id,
        actions=_build_actions(
            entry["action_templates"],
            series_id=series_id,
            episode_id=None,
            provider_open_url=ctx.provider_open_url,
        ),
    )


def _resolve_episode_issue(
    warning: dict,
    ctx: DiagnosticsContext,
    episode_titles: dict[str, str],
) -> DiagnosticIssueRow:
    episode_id = warning.get("episode_id")
    raw_reason = warning.get("reason", "")
    reason_code = _normalize_writeback_reason(str(raw_reason))
    entry = _catalog_entry(reason_code)
    series_id = warning.get("series_id")
    label = (
        episode_titles.get(episode_id, UNKNOWN_EPISODE_LABEL)
        if episode_id
        else UNKNOWN_EPISODE_LABEL
    )
    return DiagnosticIssueRow(
        label=label,
        reason_code=reason_code,
        reason_text=entry["reason_text"],
        remediation_hint=entry["remediation_hint"],
        series_id=series_id,
        episode_id=episode_id,
        actions=_build_actions(
            entry["action_templates"],
            series_id=series_id,
            episode_id=episode_id,
            provider_open_url=ctx.provider_open_url,
        ),
    )


def _resolve_rebuild_error(run: RebuildRun, ctx: DiagnosticsContext) -> DiagnosticIssueRow:
    entry = _catalog_entry("rebuild_failed")
    message = run.error_message or entry["reason_text"]
    return DiagnosticIssueRow(
        label="Rebuild failed",
        reason_code="rebuild_failed",
        reason_text=message,
        remediation_hint=entry["remediation_hint"],
        actions=_build_actions(
            entry["action_templates"],
            series_id=None,
            episode_id=None,
            provider_open_url=ctx.provider_open_url,
        ),
    )


def build_rebuild_diagnostics(
    run: RebuildRun,
    ctx: DiagnosticsContext,
) -> RebuildDiagnostics:
    """Pure resolver: raw run JSON → operator-facing diagnostic rows."""
    episode_titles = _episode_title_map(run, ctx)

    show_issues: list[DiagnosticIssueRow] = []
    for warning in (run.row_outcomes_json or {}).get("fetch_warnings", []):
        if isinstance(warning, dict):
            show_issues.append(_resolve_show_issue(warning, ctx))

    episode_issues: list[DiagnosticIssueRow] = []
    for warning in run.writeback_warnings or []:
        if not isinstance(warning, dict):
            continue
        if not warning.get("episode_id"):
            continue
        episode_issues.append(
            _resolve_episode_issue(warning, ctx, episode_titles)
        )

    if (
        run.writeback_status == "failed"
        and not episode_issues
        and run.writeback_error
    ):
        entry = _catalog_entry("writeback_failed")
        episode_issues.append(
            DiagnosticIssueRow(
                label="Provider sync failed",
                reason_code="writeback_failed",
                reason_text=str(run.writeback_error),
                remediation_hint=entry["remediation_hint"],
                actions=_build_actions(
                    entry["action_templates"],
                    series_id=None,
                    episode_id=None,
                    provider_open_url=ctx.provider_open_url,
                ),
            )
        )

    rebuild_error: DiagnosticIssueRow | None = None
    if run.status == "failed":
        rebuild_error = _resolve_rebuild_error(run, ctx)

    return RebuildDiagnostics(
        rebuild_error=rebuild_error,
        show_issues=show_issues,
        episode_issues=episode_issues,
    )
