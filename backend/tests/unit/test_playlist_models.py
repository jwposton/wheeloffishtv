import pytest
from pydantic import ValidationError
from unit.fixtures.playlist_vectors import episode

from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    Playlist,
    PlaylistBuildResult,
    PlaylistSeriesRow,
    RowMode,
    SeriesRebuildInput,
)


def test_playlist_episode_count_minimum() -> None:
    with pytest.raises(ValidationError):
        Playlist(id="p1", name="Test", episode_count=0, rows=[])


def test_row_defaults_per_a4() -> None:
    row = PlaylistSeriesRow(series_id="series-1")
    assert row.mode == RowMode.ORDERED
    assert row.completion_policy == CompletionPolicy.REMOVE
    assert row.completion_event == CompletionEvent.SERIES_COMPLETE


def test_series_rebuild_input_shape() -> None:
    episodes = [episode("s1e1", 1, 1)]
    on_deck = episode("s1e2", 1, 2)
    inp = SeriesRebuildInput(series_id="series-1", episodes=episodes, on_deck=on_deck)
    assert inp.series_id == "series-1"
    assert len(inp.episodes) == 1
    assert inp.on_deck is not None


def test_playlist_build_result_fields() -> None:
    result = PlaylistBuildResult(
        episodes=[],
        row_outcomes=[],
        day_key="2026-05-25",
        slots_requested=5,
        slots_filled=3,
    )
    assert result.day_key == "2026-05-25"
    assert result.slots_requested == 5
    assert result.slots_filled == 3
