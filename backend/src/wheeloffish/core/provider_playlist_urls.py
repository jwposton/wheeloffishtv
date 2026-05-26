"""Build open-in-client URLs for linked provider playlists."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote, urlencode

import httpx

PLEX_WEB_APP_BASE = "https://app.plex.tv/desktop"


@lru_cache(maxsize=16)
def _plex_machine_identifier(base_url: str, verify_ssl: bool) -> str | None:
    """Resolve Plex server machineIdentifier via GET /identity (cached per base URL)."""
    url = f"{base_url.rstrip('/')}/identity"
    try:
        with httpx.Client(verify=verify_ssl, timeout=5.0) as client:
            response = client.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            machine_id = response.json().get("MediaContainer", {}).get("machineIdentifier")
            return str(machine_id) if machine_id else None
    except Exception:
        return None


def provider_playlist_open_url(
    *,
    base_url: str,
    provider_kind: str,
    provider_playlist_id: str,
    verify_ssl: bool = True,
    plex_machine_identifier: str | None = None,
) -> str | None:
    if not base_url or not provider_kind or not provider_playlist_id:
        return None
    root = base_url.rstrip("/")
    if provider_kind == "plex":
        machine_id = plex_machine_identifier or _plex_machine_identifier(root, verify_ssl)
        if not machine_id:
            return None
        playlist_key = f"/playlists/{provider_playlist_id}"
        query = urlencode({"key": playlist_key})
        return f"{PLEX_WEB_APP_BASE}#!/server/{machine_id}/playlist?{query}"
    if provider_kind == "jellyfin":
        return f"{root}/web/index.html#!/details?id={quote(provider_playlist_id, safe='')}"
    return None
