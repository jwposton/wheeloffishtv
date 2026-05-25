from unit.fixtures.playlist_vectors import episode, fresh_series

from wheeloffish.core.playlist.completion import (
    apply_policy,
    evaluate_completion,
    resolve_row_policy,
)
from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    Playlist,
    PlaylistSeriesRow,
    RowMode,
)


def test_evaluate_completion_series_complete_when_all_played() -> None:
    episodes = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=96),
    ]
    row = PlaylistSeriesRow(series_id="series-1")

    result = evaluate_completion(row, episodes, on_deck=None)

    assert result == CompletionEvent.SERIES_COMPLETE


def test_evaluate_completion_none_for_fresh_series() -> None:
    episodes = fresh_series("s1", 1, 3)
    row = PlaylistSeriesRow(series_id="s1")

    result = evaluate_completion(row, episodes, on_deck=None)

    assert result is None


def test_evaluate_completion_does_not_fire_on_season_finish_d11() -> None:
    episodes = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=100, played=True),
        episode("s2e1", 2, 1),
    ]
    row = PlaylistSeriesRow(series_id="series-1")

    result = evaluate_completion(row, episodes, on_deck=None)

    assert result is None


def test_apply_policy_passthrough_when_event_none() -> None:
    row = PlaylistSeriesRow(series_id="s1", mode=RowMode.ORDERED)

    outcome = apply_policy(row, None)

    assert outcome.series_id == "s1"
    assert outcome.effective_mode == RowMode.ORDERED
    assert outcome.excluded is False
    assert outcome.policy_applied is None


def test_apply_policy_remove_excludes_row_d12() -> None:
    row = PlaylistSeriesRow(
        series_id="s1",
        mode=RowMode.ORDERED,
        completion_policy=CompletionPolicy.REMOVE,
    )

    outcome = apply_policy(row, CompletionEvent.SERIES_COMPLETE)

    assert outcome.excluded is True
    assert outcome.effective_mode == RowMode.ORDERED
    assert outcome.policy_applied == CompletionPolicy.REMOVE


def test_apply_policy_restart_flips_to_ordered_even_for_disordered_row() -> None:
    row = PlaylistSeriesRow(
        series_id="s1",
        mode=RowMode.DISORDERED,
        completion_policy=CompletionPolicy.RESTART,
    )

    outcome = apply_policy(row, CompletionEvent.SERIES_COMPLETE)

    assert outcome.excluded is False
    assert outcome.effective_mode == RowMode.ORDERED
    assert outcome.policy_applied == CompletionPolicy.RESTART


def test_apply_policy_disordered_changes_effective_mode() -> None:
    row = PlaylistSeriesRow(
        series_id="s1",
        mode=RowMode.ORDERED,
        completion_policy=CompletionPolicy.DISORDERED,
    )

    outcome = apply_policy(row, CompletionEvent.SERIES_COMPLETE)

    assert outcome.excluded is False
    assert outcome.effective_mode == RowMode.DISORDERED
    assert outcome.policy_applied == CompletionPolicy.DISORDERED


def test_resolve_row_policy_row_wins_over_playlist_default_d14() -> None:
    row = PlaylistSeriesRow(series_id="s1", completion_policy=CompletionPolicy.REMOVE)
    playlist = Playlist(
        id="pl1",
        name="Test",
        episode_count=20,
        default_completion_policy=CompletionPolicy.RESTART,
        rows=[row],
    )

    assert resolve_row_policy(playlist, row) == CompletionPolicy.REMOVE


def test_resolve_row_policy_returns_row_disordered_when_explicit() -> None:
    row = PlaylistSeriesRow(series_id="s1", completion_policy=CompletionPolicy.DISORDERED)
    playlist = Playlist(
        id="pl1",
        name="Test",
        episode_count=20,
        default_completion_policy=CompletionPolicy.RESTART,
        rows=[row],
    )

    assert resolve_row_policy(playlist, row) == CompletionPolicy.DISORDERED
