"""Golden-vector tests for disordered picker (PLT-04, D-03..D-09)."""

import random
from datetime import UTC, datetime, timedelta

from unit.fixtures.playlist_vectors import episode, multipart_group

from wheeloffish.core.playlist.disordered import (
    compute_eligible_pool,
    pick_disordered_block,
)
from wheeloffish.domain.dto import Episode


def _by_id(episodes: list[Episode]) -> dict[str, Episode]:
    return {ep.id: ep for ep in episodes}


def test_compute_eligible_pool_excludes_15_most_recent_d03() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    episodes = [
        episode(f"ep-{i:02d}", 1, i, last_viewed_at=base + timedelta(hours=i))
        for i in range(1, 21)
    ]

    pool = compute_eligible_pool(episodes)

    assert len(pool) == 5
    assert {ep.id for ep in pool} == {f"ep-{i:02d}" for i in range(1, 6)}


def test_compute_eligible_pool_keeps_unwatched_when_under_15_total_d05() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    episodes = [
        episode(f"ep-{i:02d}", 1, i, last_viewed_at=base + timedelta(hours=i))
        for i in range(1, 11)
    ]

    pool = compute_eligible_pool(episodes)

    assert len(pool) == 10
    assert {ep.id for ep in pool} == {f"ep-{i:02d}" for i in range(1, 11)}


def test_compute_eligible_pool_keeps_unwatched_episodes() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    watched = [
        episode(f"w-{i:02d}", 1, i, last_viewed_at=base + timedelta(hours=i))
        for i in range(1, 21)
    ]
    unwatched = [episode(f"u-{i:02d}", 1, 100 + i) for i in range(1, 11)]
    episodes = watched + unwatched

    pool = compute_eligible_pool(episodes)

    assert len(pool) == 15
    assert all(ep.id.startswith("u-") for ep in pool if ep.last_viewed_at is None)
    assert len([ep for ep in pool if ep.last_viewed_at is None]) == 10


def test_compute_eligible_pool_tie_breaks_by_id_ascending() -> None:
    same_time = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    episodes = [
        episode(f"ep-{i:02d}", 1, i, last_viewed_at=same_time)
        for i in range(1, 17)
    ]

    pool = compute_eligible_pool(episodes)

    assert len(pool) == 1
    assert pool[0].id == "ep-16"


def test_pick_disordered_block_uses_seeded_rng_for_stability() -> None:
    pool = [
        episode("a", 1, 1),
        episode("b", 1, 2),
        episode("c", 1, 3),
    ]
    by_id = _by_id(pool)

    first = pick_disordered_block(pool, by_id, set(), random.Random(42))
    second = pick_disordered_block(pool, by_id, set(), random.Random(42))

    assert first is not None
    assert second is not None
    assert first[0].id == second[0].id


def test_pick_disordered_block_excludes_already_emitted_d04() -> None:
    pool = [
        episode("a", 1, 1),
        episode("b", 1, 2),
        episode("c", 1, 3),
    ]
    by_id = _by_id(pool)
    first_pick = pick_disordered_block(pool, by_id, set(), random.Random(42))
    assert first_pick is not None

    second_pick = pick_disordered_block(
        pool,
        by_id,
        {first_pick[0].id},
        random.Random(42),
    )

    assert second_pick is not None
    assert second_pick[0].id != first_pick[0].id


def test_pick_disordered_block_returns_full_multipart_block_d08() -> None:
    parts = multipart_group(
        "grp-1",
        [
            ("part1", 1, 1, 1),
            ("part2", 1, 1, 2),
            ("part3", 1, 1, 3),
        ],
    )
    extras = [episode("solo", 1, 2)]
    all_eps = parts + extras
    by_id = _by_id(all_eps)
    eligible = [by_id["part2"]]

    block = pick_disordered_block(eligible, by_id, set(), random.Random(42))

    assert block is not None
    assert [ep.id for ep in block] == ["part1", "part2", "part3"]


def test_pick_disordered_block_full_block_includes_excluded_parts_d09() -> None:
    now = datetime(2026, 5, 1, tzinfo=UTC)
    parts = [
        episode("part1", 1, 1, part_index=1, multipart_group_id="grp-1", last_viewed_at=now),
        episode("part2", 1, 1, part_index=2, multipart_group_id="grp-1"),
        episode("part3", 1, 1, part_index=3, multipart_group_id="grp-1"),
    ]
    by_id = _by_id(parts)
    eligible = compute_eligible_pool(parts)

    assert "part1" not in {ep.id for ep in eligible}

    block = pick_disordered_block(eligible, by_id, set(), random.Random(42))

    assert block is not None
    assert [ep.id for ep in block] == ["part1", "part2", "part3"]


def test_pick_disordered_block_singleton_when_no_multipart_group() -> None:
    pool = [episode("solo", 1, 1)]
    by_id = _by_id(pool)

    block = pick_disordered_block(pool, by_id, set(), random.Random(7))

    assert block == [pool[0]]


def test_pick_disordered_block_returns_none_when_no_candidates() -> None:
    pool = [episode("solo", 1, 1)]
    by_id = _by_id(pool)

    result = pick_disordered_block(pool, by_id, {"solo"}, random.Random(1))

    assert result is None


def test_pick_disordered_block_falls_back_to_full_pool_d05() -> None:
    pool = [episode("a", 1, 1), episode("b", 1, 2)]
    by_id = _by_id(pool)
    eligible: list[Episode] = []

    block = pick_disordered_block(eligible, by_id, set(), random.Random(42))

    assert block is not None
    assert block[0].id in {"a", "b"}
