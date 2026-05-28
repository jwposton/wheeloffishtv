"""Resume pointer computation (INT-03, D-10, D-12).

Reusable by Phase 4 playlist builder — pass live ``Episode`` lists and on-deck
from ``MediaProvider``; no episode persistence required.
"""

from enum import StrEnum

from wheeloffish.domain.dto import Episode, ResumeCursor


class WatchState(StrEnum):
    UNWATCHED = "unwatched"
    PARTIAL = "partial"
    COMPLETE = "complete"


def classify_watch(ep: Episode) -> WatchState:
    """Classify watch state per D-11 thresholds."""
    if ep.provider_marked_played:
        return WatchState.COMPLETE
    if ep.percent_watched >= 95:
        return WatchState.COMPLETE
    if ep.percent_watched >= 5:
        return WatchState.PARTIAL
    return WatchState.UNWATCHED


def order_episodes(episodes: list[Episode]) -> list[Episode]:
    """Order episodes with specials after each season finale (D-12)."""
    if not episodes:
        return []

    main_by_season: dict[int, list[Episode]] = {}
    specials_by_season: dict[int, list[Episode]] = {}

    for ep in episodes:
        if ep.is_special or ep.season_index == 0:
            target_season = ep.special_for_season if ep.special_for_season is not None else 0
            specials_by_season.setdefault(target_season, []).append(ep)
        else:
            main_by_season.setdefault(ep.season_index, []).append(ep)

    for season_eps in main_by_season.values():
        season_eps.sort(key=lambda e: e.episode_index)
    for season_eps in specials_by_season.values():
        season_eps.sort(key=lambda e: e.episode_index)

    ordered: list[Episode] = []
    for season in sorted(main_by_season):
        season_main = main_by_season[season]
        ordered.extend(season_main)
        if season in specials_by_season:
            ordered.extend(specials_by_season[season])

    orphan_specials = [
        season
        for season in specials_by_season
        if season not in main_by_season and season != 0
    ]
    for season in sorted(orphan_specials):
        ordered.extend(specials_by_season[season])

    if 0 in specials_by_season and 0 not in main_by_season:
        ordered.extend(specials_by_season[0])

    return ordered


def is_ahead_in_sequence(
    on_deck: Episode,
    earliest: Episode,
    ordered: list[Episode],
) -> bool:
    """Return True when on_deck is ahead of earliest with no unfinished gaps."""
    try:
        on_deck_idx = next(i for i, ep in enumerate(ordered) if ep.id == on_deck.id)
        earliest_idx = next(i for i, ep in enumerate(ordered) if ep.id == earliest.id)
    except StopIteration:
        return False

    if on_deck_idx <= earliest_idx:
        return False

    between = ordered[earliest_idx + 1 : on_deck_idx]
    return all(classify_watch(ep) == WatchState.COMPLETE for ep in between)


def _cursor_from_episode(
    episode: Episode,
    *,
    source: str,
    series_id: str | None = None,
) -> ResumeCursor:
    return ResumeCursor(
        series_id=series_id,
        episode_id=episode.id,
        season_index=episode.season_index,
        episode_index=episode.episode_index,
        percent_watched=episode.percent_watched,
        source=source,  # type: ignore[arg-type]
        series_complete=False,
        episode=episode,
    )


class ResumeService:
    """Domain service for hybrid resume pointer computation (D-10)."""

    def compute(
        self,
        series_id: str,
        episodes: list[Episode],
        on_deck: Episode | None,
    ) -> ResumeCursor:
        """Compute resume cursor using hybrid on-deck rule (D-10)."""
        ordered = order_episodes(episodes)
        earliest = next((e for e in ordered if classify_watch(e) != WatchState.COMPLETE), None)

        if earliest is None:
            return ResumeCursor(series_id=series_id, series_complete=True)

        if on_deck is not None and is_ahead_in_sequence(on_deck, earliest, ordered):
            return _cursor_from_episode(on_deck, source="on_deck", series_id=series_id)

        return _cursor_from_episode(earliest, source="earliest_unfinished", series_id=series_id)


def compute_resume(
    episodes: list[Episode],
    on_deck: Episode | None,
    *,
    series_id: str | None = None,
) -> ResumeCursor:
    """Compute resume cursor; convenience wrapper around :class:`ResumeService`."""
    return ResumeService().compute(series_id or "", episodes, on_deck)
