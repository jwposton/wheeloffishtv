"""Completion event detection and policy resolution (PLT-06, D-11, D-12, D-14, D-15)."""

from wheeloffish.core.resume import ResumeService
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    Playlist,
    PlaylistSeriesRow,
    RowBuildOutcome,
    RowMode,
)

__all__ = ["evaluate_completion", "apply_policy", "resolve_row_policy"]


def evaluate_completion(
    row: PlaylistSeriesRow,
    episodes: list[Episode],
    on_deck: Episode | None,
) -> CompletionEvent | None:
    """Return SERIES_COMPLETE when ResumeService marks the series finished."""
    cursor = ResumeService().compute(row.series_id, episodes, on_deck)
    if cursor.series_complete:
        return CompletionEvent.SERIES_COMPLETE
    # D-11: SEASON_COMPLETE deferred to v2
    return None


def apply_policy(
    row: PlaylistSeriesRow,
    completion_event: CompletionEvent | None,
) -> RowBuildOutcome:
    """Map a completion event to a row build outcome for the nightly builder."""
    if completion_event is None:
        return RowBuildOutcome(
            series_id=row.series_id,
            effective_mode=row.mode,
            excluded=False,
            policy_applied=None,
        )

    if completion_event == CompletionEvent.SERIES_COMPLETE:
        match row.completion_policy:
            case CompletionPolicy.REMOVE:
                return RowBuildOutcome(
                    series_id=row.series_id,
                    effective_mode=row.mode,
                    excluded=True,
                    policy_applied=CompletionPolicy.REMOVE,
                )
            case CompletionPolicy.RESTART:
                return RowBuildOutcome(
                    series_id=row.series_id,
                    effective_mode=RowMode.ORDERED,
                    excluded=False,
                    policy_applied=CompletionPolicy.RESTART,
                )
            case CompletionPolicy.DISORDERED:
                return RowBuildOutcome(
                    series_id=row.series_id,
                    effective_mode=RowMode.DISORDERED,
                    excluded=False,
                    policy_applied=CompletionPolicy.DISORDERED,
                )

    return RowBuildOutcome(
        series_id=row.series_id,
        effective_mode=row.mode,
        excluded=False,
        policy_applied=None,
    )


def resolve_row_policy(playlist: Playlist, row: PlaylistSeriesRow) -> CompletionPolicy:
    """Per-row policy always wins over playlist default (D-14)."""
    return row.completion_policy
