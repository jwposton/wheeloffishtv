from wheeloffish.core.resume import compute_resume, order_episodes
from wheeloffish.domain.dto import Episode


def _episode(
    episode_id: str,
    season: int,
    index: int,
    *,
    percent: float = 0.0,
    played: bool = False,
    is_special: bool = False,
    special_for_season: int | None = None,
) -> Episode:
    return Episode(
        id=episode_id,
        title=f"S{season}E{index}",
        season_index=season,
        episode_index=index,
        duration_ms=3_600_000,
        percent_watched=percent,
        provider_marked_played=played,
        is_special=is_special,
        special_for_season=special_for_season,
    )


def test_fresh_series_resumes_at_first_episode() -> None:
    episodes = [
        _episode("s1e1", 1, 1),
        _episode("s1e2", 1, 2),
        _episode("s1e3", 1, 3),
    ]
    cursor = compute_resume(episodes, on_deck=None, series_id="series-1")

    assert cursor.series_complete is False
    assert cursor.source == "earliest_unfinished"
    assert cursor.episode_id == "s1e1"
    assert cursor.season_index == 1
    assert cursor.episode_index == 1


def test_partial_episode_resumes_at_partial() -> None:
    episodes = [
        _episode("s1e1", 1, 1, percent=100, played=True),
        _episode("s1e2", 1, 2, percent=100, played=True),
        _episode("s1e3", 1, 3, percent=50),
    ]
    cursor = compute_resume(episodes, on_deck=None, series_id="series-1")

    assert cursor.episode_id == "s1e3"
    assert cursor.source == "earliest_unfinished"


def test_on_deck_ahead_when_user_skipped() -> None:
    episodes = [
        _episode("s1e1", 1, 1, percent=100, played=True),
        _episode("s1e2", 1, 2, percent=100, played=True),
        _episode("s1e3", 1, 3, percent=100, played=True),
        _episode("s1e4", 1, 4, percent=100, played=True),
        _episode("s1e5", 1, 5),
        _episode("s2e1", 2, 1),
    ]
    on_deck = _episode("s2e1", 2, 1)
    cursor = compute_resume(episodes, on_deck=on_deck, series_id="series-1")

    assert cursor.source == "on_deck"
    assert cursor.episode_id == "s2e1"


def test_all_complete_marks_series_complete() -> None:
    episodes = [
        _episode("s1e1", 1, 1, percent=100, played=True),
        _episode("s1e2", 1, 2, percent=96),
    ]
    cursor = compute_resume(episodes, on_deck=None, series_id="series-1")

    assert cursor.series_complete is True
    assert cursor.episode_id is None


def test_specials_ordered_after_season_finale() -> None:
    episodes = [
        _episode("s1e1", 1, 1),
        _episode("s1e2", 1, 2),
        _episode("s00e1", 0, 1, is_special=True, special_for_season=1),
        _episode("s2e1", 2, 1),
    ]
    ordered = order_episodes(episodes)
    ids = [ep.id for ep in ordered]

    assert ids.index("s1e2") < ids.index("s00e1")
    assert ids.index("s00e1") < ids.index("s2e1")


def test_earliest_unfinished_when_on_deck_behind() -> None:
    episodes = [
        _episode("s1e1", 1, 1, percent=100, played=True),
        _episode("s1e2", 1, 2, percent=50),
        _episode("s1e3", 1, 3),
    ]
    on_deck = _episode("s1e2", 1, 2, percent=50)
    cursor = compute_resume(episodes, on_deck=on_deck, series_id="series-1")

    assert cursor.source == "earliest_unfinished"
    assert cursor.episode_id == "s1e2"
