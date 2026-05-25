"""Golden-vector tests for ordered serial picker (PLT-05, D-07, D-17)."""

from unit.fixtures.playlist_vectors import episode, multipart_group

from wheeloffish.core.playlist.ordered import next_block, start_index_for_row
from wheeloffish.core.resume import order_episodes
from wheeloffish.domain.dto import Episode


def _episodes_by_id(episodes: list[Episode]) -> dict[str, Episode]:
    return {ep.id: ep for ep in episodes}


def test_start_index_fresh_series_returns_zero() -> None:
    eps = [
        episode("s1e1", 1, 1),
        episode("s1e2", 1, 2),
        episode("s1e3", 1, 3),
    ]

    assert start_index_for_row("s", eps, None) == 0


def test_start_index_partial_resumes_at_partial_episode() -> None:
    eps = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=100, played=True),
        episode("s1e3", 1, 3, percent=50),
    ]
    ordered = order_episodes(eps)

    idx = start_index_for_row("s", eps, None)

    assert idx == next(i for i, ep in enumerate(ordered) if ep.id == "s1e3")


def test_start_index_uses_on_deck_when_user_skipped() -> None:
    eps = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=100, played=True),
        episode("s1e3", 1, 3, percent=100, played=True),
        episode("s1e4", 1, 4, percent=100, played=True),
        episode("s1e5", 1, 5),
        episode("s2e1", 2, 1),
    ]
    on_deck = episode("s2e1", 2, 1)
    ordered = order_episodes(eps)

    idx = start_index_for_row("s", eps, on_deck)

    assert idx == next(i for i, ep in enumerate(ordered) if ep.id == "s2e1")


def test_start_index_series_complete_returns_len_ordered() -> None:
    eps = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=96),
    ]
    ordered = order_episodes(eps)

    assert start_index_for_row("s", eps, None) == len(ordered)


def test_start_index_restart_flag_forces_zero_even_when_complete() -> None:
    eps = [
        episode("s1e1", 1, 1, percent=100, played=True),
        episode("s1e2", 1, 2, percent=96),
    ]

    assert start_index_for_row("s", eps, None, restart=True) == 0


def test_next_block_singleton_advances_by_one() -> None:
    eps = [episode("solo", 1, 1)]
    ordered = order_episodes(eps)
    by_id = _episodes_by_id(eps)

    block, new_index = next_block(ordered, by_id, 0)

    assert [ep.id for ep in block] == ["solo"]
    assert new_index == 1


def test_next_block_multipart_three_parts_returns_full_forward_block_d07() -> None:
    eps = [
        episode("s1e1", 1, 1),
        *multipart_group(
            "g-s1e2",
            [
                ("p1", 1, 2, 1),
                ("p2", 1, 2, 2),
                ("p3", 1, 2, 3),
            ],
        ),
    ]
    ordered = order_episodes(eps)
    by_id = _episodes_by_id(eps)
    anchor_idx = next(i for i, ep in enumerate(ordered) if ep.id == "p1")

    block, new_index = next_block(ordered, by_id, anchor_idx)

    assert [ep.id for ep in block] == ["p1", "p2", "p3"]
    assert new_index == anchor_idx + 3


def test_next_block_multipart_anchor_at_part_two_skips_part_one() -> None:
    eps = [
        episode("s1e1", 1, 1),
        *multipart_group(
            "g-s1e2",
            [
                ("p1", 1, 2, 1),
                ("p2", 1, 2, 2),
                ("p3", 1, 2, 3),
            ],
        ),
    ]
    ordered = order_episodes(eps)
    by_id = _episodes_by_id(eps)
    anchor_idx = next(i for i, ep in enumerate(ordered) if ep.id == "p2")

    block, new_index = next_block(ordered, by_id, anchor_idx)

    assert [ep.id for ep in block] == ["p2", "p3"]
    assert new_index == anchor_idx + 2


def test_next_block_returns_empty_at_end_of_ordered() -> None:
    eps = [episode("solo", 1, 1)]
    ordered = order_episodes(eps)
    by_id = _episodes_by_id(eps)

    block, new_index = next_block(ordered, by_id, len(ordered))

    assert block == []
    assert new_index == len(ordered)


def test_next_block_specials_traversed_after_finale() -> None:
    eps = [
        episode("s1e1", 1, 1),
        episode("s1e2", 1, 2),
        episode("special-s1", 0, 1, is_special=True, special_for_season=1),
        episode("s2e1", 2, 1),
    ]
    ordered = order_episodes(eps)
    by_id = _episodes_by_id(eps)
    special_idx = next(i for i, ep in enumerate(ordered) if ep.id == "special-s1")

    block, new_index = next_block(ordered, by_id, special_idx)

    assert [ep.id for ep in block] == ["special-s1"]
    assert new_index == special_idx + 1

    next_block_ids, after_special = next_block(ordered, by_id, new_index)

    assert [ep.id for ep in next_block_ids] == ["s2e1"]
    assert after_special == new_index + 1
