"""End-to-end golden-vector tests for PlaylistBuilder (PLT-01–06, SCH-02)."""

from unit.fixtures.playlist_vectors import episode, fresh_series, multipart_group, playlist_single_row

from wheeloffish.core.playlist import PlaylistBuilder
from wheeloffish.domain.playlist import (
    CompletionPolicy,
    Playlist,
    PlaylistSeriesRow,
    RowMode,
    SeriesRebuildInput,
    SlotAllocation,
)


def test_build_single_ordered_row_serial_from_resume() -> None:
    episodes = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=50),
        episode("s1e3", 1, 3),
        episode("s1e4", 1, 4),
    ]
    playlist = playlist_single_row("p1", "series-a", episode_count=3)
    inputs = [SeriesRebuildInput(series_id="series-a", episodes=episodes, on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="ordered-resume")

    assert result.slots_filled == 3
    assert [be.episode.id for be in result.episodes] == ["s1e2", "s1e3", "s1e4"]
    assert all(be.row_mode == RowMode.ORDERED for be in result.episodes)


def test_build_disordered_row_differs_by_seed() -> None:
    episodes = fresh_series("d", 1, 8)
    playlist = playlist_single_row(
        "p-dis",
        "series-d",
        episode_count=3,
        mode=RowMode.DISORDERED,
    )
    inputs = [SeriesRebuildInput(series_id="series-d", episodes=episodes, on_deck=None)]

    result_a = PlaylistBuilder.build(playlist, inputs, rebuild_seed="seed-alpha")
    result_b = PlaylistBuilder.build(playlist, inputs, rebuild_seed="seed-beta")

    ids_a = [be.episode.id for be in result_a.episodes]
    ids_b = [be.episode.id for be in result_b.episodes]
    assert ids_a != ids_b


def test_build_same_seed_is_deterministic() -> None:
    episodes = fresh_series("det", 1, 6)
    playlist = playlist_single_row(
        "p-det",
        "series-det",
        episode_count=4,
        mode=RowMode.DISORDERED,
    )
    inputs = [SeriesRebuildInput(series_id="series-det", episodes=episodes, on_deck=None)]

    result_first = PlaylistBuilder.build(playlist, inputs, rebuild_seed="test-seed-42")
    result_second = PlaylistBuilder.build(playlist, inputs, rebuild_seed="test-seed-42")

    ids_first = [be.episode.id for be in result_first.episodes]
    ids_second = [be.episode.id for be in result_second.episodes]
    assert ids_first == ids_second
    assert result_first.slots_filled == result_second.slots_filled


def test_build_remove_policy_excludes_completed_row() -> None:
    episodes = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=96),
    ]
    row = PlaylistSeriesRow(
        series_id="done-series",
        mode=RowMode.ORDERED,
        completion_policy=CompletionPolicy.REMOVE,
    )
    playlist = Playlist(id="p-rm", name="Remove test", episode_count=3, rows=[row])
    inputs = [SeriesRebuildInput(series_id="done-series", episodes=episodes, on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="remove-v1")

    assert result.row_outcomes[0].excluded is True
    assert result.episodes == []
    assert result.slots_filled == 0


def test_build_multipart_ordered_block_contiguous() -> None:
    episodes = [
        episode("s1e1", 1, 1, percent=100, played=True),
        *multipart_group(
            "g-mp",
            [
                ("p1", 1, 2, 1),
                ("p2", 1, 2, 2),
                ("p3", 1, 2, 3),
            ],
        ),
    ]
    playlist = playlist_single_row("p-mp", "mp-series", episode_count=2)
    inputs = [SeriesRebuildInput(series_id="mp-series", episodes=episodes, on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="mp-v1")

    first_slot_ids = [be.episode.id for be in result.episodes if be.slot_index == 0]
    assert first_slot_ids == ["p1", "p2", "p3"]


def test_build_slots_filled_less_than_requested_when_exhausted() -> None:
    episodes = [
        episode("s1e1", 1, 1),
        episode("s1e2", 1, 2),
    ]
    playlist = playlist_single_row("p-ex", "short-series", episode_count=5)
    inputs = [SeriesRebuildInput(series_id="short-series", episodes=episodes, on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="exhaust-v1")

    assert result.slots_requested == 5
    assert result.slots_filled == 2
    assert len(result.episodes) == 2


def test_build_mixed_playlist_respects_row_modes() -> None:
    ordered_eps = fresh_series("ord", 1, 4)
    disordered_eps = fresh_series("dis", 1, 6)
    playlist = Playlist(
        id="p-mix",
        name="Mixed",
        episode_count=4,
        slot_allocation=SlotAllocation.ROUND_ROBIN,
        rows=[
            PlaylistSeriesRow(series_id="series-ord", mode=RowMode.ORDERED),
            PlaylistSeriesRow(series_id="series-dis", mode=RowMode.DISORDERED),
        ],
    )
    inputs = [
        SeriesRebuildInput(series_id="series-ord", episodes=ordered_eps, on_deck=None),
        SeriesRebuildInput(series_id="series-dis", episodes=disordered_eps, on_deck=None),
    ]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="mixed-v1")

    series_in_output = {be.series_id for be in result.episodes}
    assert series_in_output == {"series-ord", "series-dis"}
    assert any(be.row_mode == RowMode.ORDERED for be in result.episodes)
    assert any(be.row_mode == RowMode.DISORDERED for be in result.episodes)


def test_build_wild_vs_round_robin_allocation() -> None:
    eps_a = fresh_series("a", 1, 3)
    eps_b = fresh_series("b", 1, 3)
    playlist = Playlist(
        id="p-rr",
        name="Round robin",
        episode_count=4,
        slot_allocation=SlotAllocation.ROUND_ROBIN,
        rows=[
            PlaylistSeriesRow(series_id="series-b", mode=RowMode.ORDERED),
            PlaylistSeriesRow(series_id="series-a", mode=RowMode.ORDERED),
        ],
    )
    inputs = [
        SeriesRebuildInput(series_id="series-a", episodes=eps_a, on_deck=None),
        SeriesRebuildInput(series_id="series-b", episodes=eps_b, on_deck=None),
    ]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="rr-v1")

    by_slot: dict[int, str] = {}
    for be in result.episodes:
        if be.slot_index not in by_slot:
            by_slot[be.slot_index] = be.series_id
    assert [by_slot[i] for i in range(4)] == [
        "series-a",
        "series-b",
        "series-a",
        "series-b",
    ]


def test_build_output_length_may_exceed_slot_count_with_multipart() -> None:
    episodes = [
        *multipart_group(
            "g-only",
            [
                ("p1", 1, 1, 1),
                ("p2", 1, 1, 2),
                ("p3", 1, 1, 3),
            ],
        ),
    ]
    playlist = playlist_single_row("p-exp", "expand-series", episode_count=1)
    inputs = [SeriesRebuildInput(series_id="expand-series", episodes=episodes, on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="expand-v1")

    assert result.slots_filled == 1
    assert len(result.episodes) == 3


def test_build_default_episode_count_is_20() -> None:
    playlist = Playlist(
        id="p-def",
        name="Defaults",
        rows=[PlaylistSeriesRow(series_id="s1")],
    )
    inputs = [SeriesRebuildInput(series_id="s1", episodes=fresh_series("s1", 1, 25), on_deck=None)]

    result = PlaylistBuilder.build(playlist, inputs, rebuild_seed="default-v1")

    assert playlist.episode_count == 20
    assert result.slots_requested == 20
