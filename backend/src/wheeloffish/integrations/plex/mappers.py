from datetime import UTC, datetime
from typing import Any

import httpx

from wheeloffish.domain.dto import Episode, Library, Series
from wheeloffish.domain.ids import format_composite_id, parse_composite_id
from wheeloffish.integrations.errors import ProviderError, ProviderUnauthorized

PROVIDER = "plex"


def map_library(connection_id: str, section: dict[str, Any]) -> Library:
    native_id = str(section["key"])
    stable_id = str(section.get("uuid") or native_id)
    return Library(
        id=format_composite_id(connection_id, PROVIDER, stable_id),
        title=str(section["title"]),
        native_id=native_id,
        connection_id=connection_id,
        provider=PROVIDER,
    )


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _library_added_at_from_plex(metadata: dict[str, Any]) -> int | None:
    """Unix seconds when the show was added to this Plex library (PMS `addedAt`)."""
    raw = metadata.get("addedAt")
    if raw in (None, "", 0):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _genres_from_metadata(metadata: dict[str, Any]) -> list[str]:
    raw_genres = metadata.get("Genre", [])
    if not isinstance(raw_genres, list):
        return []
    return [
        tag
        for genre in raw_genres
        if isinstance(genre, dict)
        for tag in [genre.get("tag")]
        if isinstance(tag, str)
    ]


def map_series(
    connection_id: str,
    library_native_id: str,
    metadata: dict[str, Any],
) -> Series:
    guid = str(metadata["guid"])
    return Series(
        id=format_composite_id(connection_id, PROVIDER, guid),
        title=str(metadata["title"]),
        native_id=guid,
        library_native_id=library_native_id,
        connection_id=connection_id,
        provider=PROVIDER,
        year=metadata.get("year"),
        thumb_url=metadata.get("thumb"),
        library_added_at=_library_added_at_from_plex(metadata),
        provider_metadata={
            "ratingKey": metadata.get("ratingKey"),
            "summary": _str_or_none(metadata.get("summary")),
            "genres": _genres_from_metadata(metadata),
            "contentRating": _str_or_none(metadata.get("contentRating")),
            "studio": _str_or_none(metadata.get("studio")),
        },
    )


def map_episode(connection_id: str, metadata: dict[str, Any]) -> Episode:
    guid = str(metadata["guid"])
    duration_ms = int(metadata.get("duration") or 0)
    view_offset = int(metadata.get("viewOffset") or 0)
    view_count = int(metadata.get("viewCount") or 0)

    percent_watched = 0.0
    if duration_ms > 0:
        percent_watched = min(100.0, (view_offset / duration_ms) * 100)

    part_index = metadata.get("partIndex")
    multipart_group_id = metadata.get("multipartGroupId")
    if multipart_group_id is not None:
        multipart_group_id = str(multipart_group_id)

    last_viewed_at: datetime | None = None
    raw_last_viewed = metadata.get("lastViewedAt")
    if raw_last_viewed not in (None, 0):
        try:
            last_viewed_at = datetime.fromtimestamp(int(raw_last_viewed), tz=UTC)
        except (TypeError, ValueError):
            last_viewed_at = None

    return Episode(
        id=format_composite_id(connection_id, PROVIDER, guid),
        title=str(metadata["title"]),
        season_index=int(metadata.get("parentIndex") or 0),
        episode_index=int(metadata.get("index") or 0),
        duration_ms=duration_ms,
        percent_watched=percent_watched,
        provider_marked_played=view_count > 0,
        part_index=int(part_index) if part_index is not None else None,
        multipart_group_id=multipart_group_id,
        last_viewed_at=last_viewed_at,
    )


async def resolve_guid_to_rating_key(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    client_identifier: str,
    product_name: str,
    guid: str,
    *,
    library_native_id: str | None = None,
) -> str:
    headers = {
        "Accept": "application/json",
        "X-Plex-Token": token,
        "X-Plex-Client-Identifier": client_identifier,
        "X-Plex-Product": product_name,
    }
    base = base_url.rstrip("/")

    if library_native_id is not None:
        section_response = await client.get(
            f"{base}/library/sections/{library_native_id}/all",
            params={"guid": guid, "type": 2},
            headers=headers,
        )
        rating_key = _rating_key_from_guid_response(section_response)
        if rating_key is not None:
            return rating_key

    response = await client.get(
        f"{base}/library/all",
        params={"guid": guid},
        headers=headers,
    )
    rating_key = _rating_key_from_guid_response(response)
    if rating_key is None:
        raise ValueError(f"No metadata found for guid: {guid}")
    return rating_key


def _rating_key_from_guid_response(response: httpx.Response) -> str | None:
    if response.status_code == 401:
        raise ProviderUnauthorized()
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ProviderError(f"Plex API error: {response.status_code}")
    metadata = response.json().get("MediaContainer", {}).get("Metadata") or []
    if not metadata:
        return None
    return str(metadata[0]["ratingKey"])


def parse_series_guid(series_composite_id: str) -> tuple[str, str, str]:
    return parse_composite_id(series_composite_id)
