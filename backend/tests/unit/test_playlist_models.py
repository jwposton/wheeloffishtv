import pytest
from pydantic import ValidationError
from unit.fixtures.playlist_vectors import episode

from wheeloffish.core.playlist.mappers import orm_to_playlist
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    Playlist,
    PlaylistBuildResult,
    PlaylistSeriesRow,
    RowMode,
    SeriesRebuildInput,
    SlotAllocation,
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


def test_playlist_default_completion_policy_defaults_to_remove() -> None:
    playlist = Playlist(id="p1", name="Test", episode_count=5, rows=[])
    assert playlist.default_completion_policy == CompletionPolicy.REMOVE


def test_playlist_default_completion_policy_accepts_override() -> None:
    playlist = Playlist(
        id="p1",
        name="Test",
        episode_count=5,
        default_completion_policy=CompletionPolicy.DISORDERED,
        rows=[],
    )
    assert playlist.default_completion_policy == CompletionPolicy.DISORDERED


def test_playlist_episode_count_defaults_to_20() -> None:
    playlist = Playlist(id="p1", name="Test", rows=[])
    assert playlist.episode_count == 20
    assert Playlist.model_fields["episode_count"].default == 20


def test_playlist_slot_allocation_defaults_to_wild() -> None:
    playlist = Playlist(id="p1", name="Test", rows=[])
    assert playlist.slot_allocation == SlotAllocation.WILD
    assert Playlist.model_fields["slot_allocation"].default == SlotAllocation.WILD


def test_playlist_slot_allocation_accepts_balanced() -> None:
    playlist = Playlist(
        id="p1",
        name="Test",
        slot_allocation=SlotAllocation.BALANCED,
        rows=[],
    )
    assert playlist.slot_allocation == SlotAllocation.BALANCED


# --- ORM ↔ domain mapper tests ---


def _make_orm_playlist(
    id: str = "p1",
    name: str = "Test Playlist",
    episode_count: int = 20,
    slot_allocation: str = "wild",
    default_completion_policy: str = "remove",
    rows: list[PlaylistSeriesRowOrm] | None = None,
) -> PlaylistOrm:
    orm = PlaylistOrm(
        id=id,
        app_user_id="user-1",
        name=name,
        episode_count=episode_count,
        slot_allocation=slot_allocation,
        default_completion_policy=default_completion_policy,
        refresh_cadence="daily",
        refresh_day_of_week=None,
    )
    orm.rows = rows or []
    return orm


def _make_orm_row(
    series_id: str,
    mode: str = "ordered",
    completion_policy: str = "remove",
    completion_event: str = "series_complete",
    sort_order: int = 0,
) -> PlaylistSeriesRowOrm:
    return PlaylistSeriesRowOrm(
        id=f"row-{series_id}",
        playlist_id="p1",
        series_id=series_id,
        mode=mode,
        completion_policy=completion_policy,
        completion_event=completion_event,
        sort_order=sort_order,
    )


def test_orm_to_playlist_maps_rows_in_sort_order() -> None:
    rows = [
        _make_orm_row("series-b", sort_order=2),
        _make_orm_row("series-a", sort_order=1),
        _make_orm_row("series-c", sort_order=3),
    ]
    orm = _make_orm_playlist(rows=rows)
    result = orm_to_playlist(orm)
    assert [r.series_id for r in result.rows] == ["series-a", "series-b", "series-c"]


def test_orm_to_playlist_defaults_episode_count_20() -> None:
    orm = _make_orm_playlist(episode_count=20)
    result = orm_to_playlist(orm)
    assert result.episode_count == 20


def test_orm_to_playlist_maps_slot_allocation_enum() -> None:
    orm = _make_orm_playlist(slot_allocation="balanced")
    result = orm_to_playlist(orm)
    assert result.slot_allocation == SlotAllocation.BALANCED


def test_weekly_cadence_stores_day_of_week() -> None:
    orm = PlaylistOrm(
        id="p1",
        app_user_id="user-1",
        name="Weekly Show",
        episode_count=20,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="weekly",
        refresh_day_of_week=5,
    )
    orm.rows = []
    result = orm_to_playlist(orm)
    assert result.id == "p1"
