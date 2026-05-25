from typing import Any

from wheeloffish.domain.dto import Episode, Library, Series
from wheeloffish.domain.ids import format_composite_id, parse_composite_id

PROVIDER = "jellyfin"
TICKS_PER_MS = 10_000


def _duration_ms(item: dict[str, Any]) -> int:
    runtime_ticks = item.get("RunTimeTicks")
    if runtime_ticks is None:
        return 0
    return int(runtime_ticks) // TICKS_PER_MS


def _percent_watched(item: dict[str, Any]) -> float:
    user_data = item.get("UserData") or {}
    if user_data.get("Played"):
        return 100.0

    played_percentage = user_data.get("PlayedPercentage")
    if played_percentage is not None:
        return min(100.0, float(played_percentage))

    runtime_ticks = item.get("RunTimeTicks") or 0
    position_ticks = user_data.get("PlaybackPositionTicks") or 0
    if runtime_ticks > 0:
        return min(100.0, (position_ticks / runtime_ticks) * 100)
    return 0.0


def map_library(connection_id: str, folder: dict[str, Any]) -> Library:
    native_id = str(folder["Id"])
    return Library(
        id=format_composite_id(connection_id, PROVIDER, native_id),
        title=str(folder["Name"]),
        native_id=native_id,
        connection_id=connection_id,
        provider=PROVIDER,
    )


def map_series(
    connection_id: str,
    library_native_id: str,
    item: dict[str, Any],
) -> Series:
    native_id = str(item["Id"])
    return Series(
        id=format_composite_id(connection_id, PROVIDER, native_id),
        title=str(item["Name"]),
        native_id=native_id,
        library_native_id=library_native_id,
        connection_id=connection_id,
        provider=PROVIDER,
        year=item.get("ProductionYear"),
        thumb_url=item.get("ImageTags", {}).get("Primary") if item.get("ImageTags") else None,
        provider_metadata={"Type": item.get("Type")},
    )


def map_episode(connection_id: str, item: dict[str, Any]) -> Episode:
    native_id = str(item["Id"])
    user_data = item.get("UserData") or {}

    part_index = item.get("PartIndex")
    multipart_group_id = item.get("MultipartGroupId")
    if multipart_group_id is not None:
        multipart_group_id = str(multipart_group_id)

    return Episode(
        id=format_composite_id(connection_id, PROVIDER, native_id),
        title=str(item["Name"]),
        season_index=int(item.get("ParentIndexNumber") or 0),
        episode_index=int(item.get("IndexNumber") or 0),
        duration_ms=_duration_ms(item),
        percent_watched=_percent_watched(item),
        provider_marked_played=bool(user_data.get("Played")),
        part_index=int(part_index) if part_index is not None else None,
        multipart_group_id=multipart_group_id,
    )


def parse_series_id(series_composite_id: str) -> tuple[str, str, str]:
    return parse_composite_id(series_composite_id)
