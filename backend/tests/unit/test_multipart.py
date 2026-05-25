"""Golden-vector tests for multipart grouping and expansion (SCH-02, D-07, D-08)."""

from unit.fixtures.playlist_vectors import episode, multipart_group

from wheeloffish.core.playlist.multipart import (
    expand_multipart_forward,
    expand_multipart_full_block,
    group_by_multipart,
    sort_multipart_block,
)


def _episodes_by_id(episodes: list) -> dict[str, object]:
    return {ep.id: ep for ep in episodes}


def test_group_by_multipart_excludes_ungrouped() -> None:
    grouped_a = episode("ga1", 1, 1, multipart_group_id="group-a")
    grouped_b = episode("ga2", 1, 2, multipart_group_id="group-a")
    ungrouped = episode("solo", 1, 3)
    grouped_c = episode("gb1", 1, 4, multipart_group_id="group-b")

    result = group_by_multipart([grouped_a, grouped_b, ungrouped, grouped_c])

    assert set(result.keys()) == {"group-a", "group-b"}
    assert {ep.id for ep in result["group-a"]} == {"ga1", "ga2"}
    assert {ep.id for ep in result["group-b"]} == {"gb1"}


def test_sort_multipart_block_ascending_with_null_last() -> None:
    parts = [
        episode("p-null", 1, 1, part_index=None, multipart_group_id="g"),
        episode("p1", 1, 2, part_index=1, multipart_group_id="g"),
        episode("p2", 1, 3, part_index=2, multipart_group_id="g"),
    ]

    sorted_ids = [ep.id for ep in sort_multipart_block(parts)]

    assert sorted_ids == ["p1", "p2", "p-null"]


def test_sort_multipart_block_id_tiebreaker() -> None:
    parts = [
        episode("p-b", 1, 1, part_index=1, multipart_group_id="g"),
        episode("p-a", 1, 2, part_index=1, multipart_group_id="g"),
    ]

    sorted_ids = [ep.id for ep in sort_multipart_block(parts)]

    assert sorted_ids == ["p-a", "p-b"]


def test_expand_full_block_returns_all_parts_d08() -> None:
    group = multipart_group(
        "g",
        [("p1", 1, 1, 1), ("p2", 1, 1, 2), ("p3", 1, 1, 3)],
    )
    episodes_by_id = _episodes_by_id(group)
    anchor = episodes_by_id["p2"]

    block_ids = [ep.id for ep in expand_multipart_full_block(anchor, episodes_by_id)]

    assert block_ids == ["p1", "p2", "p3"]


def test_expand_forward_from_part_two_returns_p2_p3_d07() -> None:
    group = multipart_group(
        "g",
        [("p1", 1, 1, 1), ("p2", 1, 1, 2), ("p3", 1, 1, 3)],
    )
    episodes_by_id = _episodes_by_id(group)
    anchor = episodes_by_id["p2"]

    block_ids = [ep.id for ep in expand_multipart_forward(anchor, episodes_by_id)]

    assert block_ids == ["p2", "p3"]


def test_expand_forward_from_part_one_returns_full_block_d07() -> None:
    group = multipart_group(
        "g",
        [("p1", 1, 1, 1), ("p2", 1, 1, 2), ("p3", 1, 1, 3)],
    )
    episodes_by_id = _episodes_by_id(group)
    anchor = episodes_by_id["p1"]

    block_ids = [ep.id for ep in expand_multipart_forward(anchor, episodes_by_id)]

    assert block_ids == ["p1", "p2", "p3"]


def test_expand_forward_anchor_with_null_part_index_returns_full_block() -> None:
    group = multipart_group(
        "g",
        [("p1", 1, 1, 1), ("p2", 1, 1, 2), ("p3", 1, 1, 3)],
    )
    episodes_by_id = _episodes_by_id(group)
    anchor = episode("p-null", 1, 1, part_index=None, multipart_group_id="g")
    episodes_by_id[anchor.id] = anchor

    block_ids = [ep.id for ep in expand_multipart_forward(anchor, episodes_by_id)]

    assert block_ids == ["p1", "p2", "p3", "p-null"]


def test_expand_full_block_singleton_when_no_group_id() -> None:
    anchor = episode("solo", 1, 1)
    episodes_by_id = _episodes_by_id([anchor])

    block = expand_multipart_full_block(anchor, episodes_by_id)

    assert block == [anchor]


def test_expand_forward_singleton_when_no_group_id() -> None:
    anchor = episode("solo", 1, 1)
    episodes_by_id = _episodes_by_id([anchor])

    block = expand_multipart_forward(anchor, episodes_by_id)

    assert block == [anchor]


def test_expand_forward_anchor_beyond_group_returns_anchor_only() -> None:
    group = multipart_group(
        "g",
        [("p1", 1, 1, 1), ("p2", 1, 1, 2), ("p3", 1, 1, 3)],
    )
    episodes_by_id = _episodes_by_id(group)
    anchor = episode("p4", 1, 1, part_index=4, multipart_group_id="g")
    episodes_by_id[anchor.id] = anchor

    block_ids = [ep.id for ep in expand_multipart_forward(anchor, episodes_by_id)]

    assert block_ids == ["p4"]
