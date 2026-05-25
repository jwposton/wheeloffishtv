from wheeloffish.core.resume import WatchState, classify_watch
from wheeloffish.domain.dto import Episode


def _episode(**overrides) -> Episode:
    defaults = {
        "id": "ep-1",
        "title": "Test Episode",
        "season_index": 1,
        "episode_index": 1,
        "duration_ms": 3_600_000,
        "percent_watched": 0.0,
        "provider_marked_played": False,
    }
    defaults.update(overrides)
    return Episode(**defaults)


def test_four_percent_is_unwatched() -> None:
    assert classify_watch(_episode(percent_watched=4)) == WatchState.UNWATCHED


def test_fifty_percent_is_partial() -> None:
    assert classify_watch(_episode(percent_watched=50)) == WatchState.PARTIAL


def test_ninety_six_percent_is_complete() -> None:
    assert classify_watch(_episode(percent_watched=96)) == WatchState.COMPLETE


def test_provider_marked_played_overrides_low_percent() -> None:
    assert (
        classify_watch(_episode(percent_watched=2, provider_marked_played=True))
        == WatchState.COMPLETE
    )


def test_provider_marked_played_overrides_partial_percent() -> None:
    assert (
        classify_watch(_episode(percent_watched=50, provider_marked_played=True))
        == WatchState.COMPLETE
    )
