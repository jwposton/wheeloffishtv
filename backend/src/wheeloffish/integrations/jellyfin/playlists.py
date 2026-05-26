"""Jellyfin native playlist CRUD and item replace (Phase 07)."""
from __future__ import annotations

from wheeloffish.domain.ids import parse_composite_id
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.playlist_names import provider_playlist_display_name

PROVIDER = "jellyfin"


def episode_native_id(episode_composite_id: str) -> str:
    connection_id, provider_kind, native_id = parse_composite_id(episode_composite_id)
    if provider_kind != PROVIDER:
        raise ValueError(f"Expected jellyfin episode id, got provider {provider_kind!r}")
    if not native_id:
        raise ValueError("Empty jellyfin episode id")
    return native_id


async def list_playlist_entry_ids(
    provider: JellyfinProvider,
    playlist_id: str,
) -> list[str]:
    response = await provider._request(
        "GET",
        f"/Playlists/{playlist_id}/Items",
        params={"userId": provider.user_id},
    )
    items = response.json().get("Items") or []
    entry_ids: list[str] = []
    for item in items:
        playlist_item_id = item.get("PlaylistItemId") or item.get("Id")
        if playlist_item_id:
            entry_ids.append(str(playlist_item_id))
    return entry_ids


async def clear_playlist_items(provider: JellyfinProvider, playlist_id: str) -> None:
    entry_ids = await list_playlist_entry_ids(provider, playlist_id)
    if not entry_ids:
        return
    await provider._request(
        "DELETE",
        f"/Playlists/{playlist_id}/Items",
        params={"entryIds": ",".join(entry_ids)},
    )


async def add_playlist_items(
    provider: JellyfinProvider,
    playlist_id: str,
    media_item_ids: list[str],
) -> None:
    if not media_item_ids:
        return
    await provider._request(
        "POST",
        f"/Playlists/{playlist_id}/Items",
        params={
            "ids": ",".join(media_item_ids),
            "userId": provider.user_id,
        },
    )


async def replace_playlist_items(
    provider: JellyfinProvider,
    playlist_id: str,
    media_item_ids: list[str],
) -> None:
    await clear_playlist_items(provider, playlist_id)
    await add_playlist_items(provider, playlist_id, media_item_ids)


async def create_playlist(
    provider: JellyfinProvider,
    title: str,
    media_item_ids: list[str],
) -> str:
    if not media_item_ids:
        raise ValueError("Cannot create Jellyfin playlist with zero items")
    response = await provider._request(
        "POST",
        "/Playlists",
        params={
            "name": title,
            "ids": ",".join(media_item_ids),
            "userId": provider.user_id,
            "mediaType": "Video",
        },
    )
    data = response.json()
    playlist_id = data.get("Id")
    if not playlist_id:
        raise ValueError("Jellyfin create playlist response missing Id")
    return str(playlist_id)


async def rename_playlist(
    provider: JellyfinProvider,
    playlist_id: str,
    title: str,
) -> None:
    await provider._request(
        "POST",
        f"/Playlists/{playlist_id}",
        json={"Name": title},
    )


async def delete_playlist(provider: JellyfinProvider, playlist_id: str) -> None:
    await provider._request("DELETE", f"/Playlists/{playlist_id}")


__all__ = [
    "provider_playlist_display_name",
    "episode_native_id",
    "create_playlist",
    "clear_playlist_items",
    "add_playlist_items",
    "replace_playlist_items",
    "rename_playlist",
    "delete_playlist",
]
