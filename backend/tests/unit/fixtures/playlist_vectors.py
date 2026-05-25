from wheeloffish.domain.dto import Episode
from wheeloffish.domain.playlist import Playlist, PlaylistSeriesRow, RowMode


def episode(
    episode_id: str,
    season: int,
    index: int,
    *,
    percent: float = 0.0,
    played: bool = False,
    part_index: int | None = None,
    multipart_group_id: str | None = None,
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
        part_index=part_index,
        multipart_group_id=multipart_group_id,
        is_special=is_special,
        special_for_season=special_for_season,
    )


def multipart_group(
    group_id: str,
    parts: list[tuple[str, int, int, int | None]],
) -> list[Episode]:
    return [
        episode(
            episode_id,
            season,
            index,
            part_index=part_index,
            multipart_group_id=group_id,
        )
        for episode_id, season, index, part_index in parts
    ]


def fresh_series(series_id_prefix: str, season: int, count: int) -> list[Episode]:
    return [
        episode(f"{series_id_prefix}-s{season}e{i}", season, i)
        for i in range(1, count + 1)
    ]


def playlist_single_row(
    playlist_id: str,
    series_id: str,
    *,
    episode_count: int = 3,
    mode: RowMode = RowMode.ORDERED,
) -> Playlist:
    return Playlist(
        id=playlist_id,
        name=f"Playlist {playlist_id}",
        episode_count=episode_count,
        rows=[PlaylistSeriesRow(series_id=series_id, mode=mode)],
    )
