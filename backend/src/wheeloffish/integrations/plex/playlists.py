"""Plex native playlist CRUD and item replace (Phase 07)."""
from __future__ import annotations

from wheeloffish.domain.ids import parse_composite_id
from wheeloffish.integrations.errors import ProviderNotFound
from wheeloffish.integrations.playlist_names import provider_playlist_display_name
from wheeloffish.integrations.plex.client import PlexProvider
from wheeloffish.integrations.plex.mappers import resolve_guid_to_rating_key

PROVIDER = "plex"


def _items_uri(machine_id: str, rating_keys: list[str]) -> str:
    """Plex playlist item URI (matches python-plexapi Playlist._create / addItems)."""
    keys = ",".join(rating_keys)
    return f"server://{machine_id}/com.plexapp.plugins.library/library/metadata/{keys}"


async def get_machine_identifier(provider: PlexProvider) -> str:
    response = await provider._request("GET", "/identity")
    machine_id = response.json().get("MediaContainer", {}).get("machineIdentifier")
    if not machine_id:
        raise ValueError("Plex identity response missing machineIdentifier")
    return str(machine_id)


async def resolve_episode_rating_key(
    provider: PlexProvider,
    episode_composite_id: str,
) -> str:
    connection_id, provider_kind, native_id = parse_composite_id(episode_composite_id)
    if provider_kind != PROVIDER:
        raise ValueError(f"Expected plex episode id, got provider {provider_kind!r}")
    if connection_id != provider.connection_id:
        raise ValueError("Episode connection_id does not match provider")
    if native_id.isdigit():
        return native_id
    async with provider._client() as client:
        return await resolve_guid_to_rating_key(
            client,
            provider.base_url,
            provider.token,
            provider.client_identifier,
            provider.product_name,
            native_id,
        )


async def list_playlist_item_keys(provider: PlexProvider, playlist_rating_key: str) -> list[str]:
    response = await provider._request("GET", f"/playlists/{playlist_rating_key}/items")
    metadata = response.json().get("MediaContainer", {}).get("Metadata") or []
    return [str(item["ratingKey"]) for item in metadata if item.get("ratingKey") is not None]


async def playlist_exists(provider: PlexProvider, playlist_rating_key: str) -> bool:
    try:
        await provider._request("GET", f"/playlists/{playlist_rating_key}")
        return True
    except ProviderNotFound:
        return False


async def clear_playlist_items(provider: PlexProvider, playlist_rating_key: str) -> None:
    await provider._request("DELETE", f"/playlists/{playlist_rating_key}/items")


async def add_playlist_items(
    provider: PlexProvider,
    playlist_rating_key: str,
    episode_rating_keys: list[str],
) -> None:
    if not episode_rating_keys:
        return
    machine_id = await get_machine_identifier(provider)
    uri = _items_uri(machine_id, episode_rating_keys)
    await provider._request(
        "PUT",
        f"/playlists/{playlist_rating_key}/items",
        params={"uri": uri},
    )


async def replace_playlist_items(
    provider: PlexProvider,
    playlist_rating_key: str,
    episode_rating_keys: list[str],
) -> None:
    await clear_playlist_items(provider, playlist_rating_key)
    await add_playlist_items(provider, playlist_rating_key, episode_rating_keys)


async def create_video_playlist(
    provider: PlexProvider,
    title: str,
    episode_rating_keys: list[str],
) -> str:
    if not episode_rating_keys:
        raise ValueError("Cannot create Plex playlist with zero items")
    machine_id = await get_machine_identifier(provider)
    uri = _items_uri(machine_id, episode_rating_keys)
    response = await provider._request(
        "POST",
        "/playlists",
        params={
            "type": "video",
            "title": title,
            "smart": "0",
            "uri": uri,
        },
    )
    metadata = response.json().get("MediaContainer", {}).get("Metadata") or []
    if not metadata:
        raise ValueError("Plex create playlist response missing Metadata")
    return str(metadata[0]["ratingKey"])


async def rename_playlist(
    provider: PlexProvider,
    playlist_rating_key: str,
    title: str,
) -> None:
    await provider._request(
        "PUT",
        f"/playlists/{playlist_rating_key}",
        params={"title": title},
    )


async def delete_playlist(provider: PlexProvider, playlist_rating_key: str) -> None:
    await provider._request("DELETE", f"/playlists/{playlist_rating_key}")


__all__ = [
    "provider_playlist_display_name",
    "get_machine_identifier",
    "resolve_episode_rating_key",
    "playlist_exists",
    "create_video_playlist",
    "clear_playlist_items",
    "add_playlist_items",
    "replace_playlist_items",
    "rename_playlist",
    "delete_playlist",
]
