from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlparse

from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.plex.client import PlexProvider

logger = logging.getLogger(__name__)


def artwork_cache_path(
    cache_dir: str,
    app_user_id: str,
    connection_id: str,
    series_id: str,
) -> Path:
    """Deterministic on-disk path for a user's series poster."""
    digest = hashlib.sha256(series_id.encode()).hexdigest()[:32]
    return Path(cache_dir) / app_user_id / connection_id / f"{digest}.img"


def series_artwork_url(connection_id: str, series_id: str) -> str:
    """Same-origin URL for a cached series poster (lazy-filled on first request)."""
    return f"/api/v1/connections/{connection_id}/series/{quote(series_id, safe='')}/artwork"


def normalize_plex_artwork_path(thumb_url: str | None) -> str | None:
    """Extract a Plex /library/... path from sync metadata."""
    if not thumb_url:
        return None
    if thumb_url.startswith("/library/") and ".." not in thumb_url:
        return thumb_url
    if thumb_url.startswith(("http://", "https://")):
        path = urlparse(thumb_url).path
        if path.startswith("/library/") and ".." not in path:
            return path
    return None


def normalize_jellyfin_artwork_path(thumb_url: str | None, native_id: str) -> str | None:
    """Resolve Jellyfin image path for fetch (supports legacy tag-only ``thumb_url``)."""
    if ".." in native_id:
        return None
    if thumb_url and thumb_url.startswith("/Items/") and ".." not in thumb_url:
        head = thumb_url.split("?", 1)[0]
        if "/Images/" in head:
            return thumb_url
    # Legacy: we stored ImageTags.Primary (tag string) without a path
    if thumb_url and "/" not in thumb_url and native_id.strip():
        return f"/Items/{native_id}/Images/Primary?tag={quote(str(thumb_url), safe='')}"
    return None


def resolve_series_artwork_fetch_path(
    *,
    provider_type: Literal["plex", "jellyfin"],
    thumb_url: str | None,
    native_id: str,
) -> str | None:
    if provider_type == "plex":
        return normalize_plex_artwork_path(thumb_url)
    if provider_type == "jellyfin":
        return normalize_jellyfin_artwork_path(thumb_url, native_id)
    return None


def read_cached_artwork(
    cache_path: Path,
    *,
    ttl_days: int | None = None,
) -> tuple[bytes, str] | None:
    if not cache_path.is_file():
        return None
    if ttl_days is not None and ttl_days > 0:
        age_seconds = time.time() - cache_path.stat().st_mtime
        if age_seconds > ttl_days * 86400:
            return None
    content = cache_path.read_bytes()
    suffix = cache_path.suffix.lower()
    media_type = "image/jpeg" if suffix in {".img", ".jpg", ".jpeg"} else "application/octet-stream"
    return content, media_type


def write_cached_artwork(cache_path: Path, content: bytes) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)


async def download_and_cache_artwork(
    provider: PlexProvider | JellyfinProvider,
    *,
    cache_dir: str,
    app_user_id: str,
    connection_id: str,
    series_id: str,
    thumb_url: str | None,
    provider_type: Literal["plex", "jellyfin"],
    native_id: str,
) -> bool:
    """Fetch poster bytes from Plex or Jellyfin and persist locally. Returns True if cached."""
    fetch_path = resolve_series_artwork_fetch_path(
        provider_type=provider_type,
        thumb_url=thumb_url,
        native_id=native_id,
    )
    if fetch_path is None:
        return False

    cache_path = artwork_cache_path(cache_dir, app_user_id, connection_id, series_id)
    if cache_path.is_file():
        return True

    try:
        content, _media_type = await provider.fetch_artwork(fetch_path)
    except ProviderError as err:
        logger.warning(
            "artwork_download_failed code=%s connection_id=%s series_id=%s",
            err.code,
            connection_id,
            series_id,
        )
        return False

    write_cached_artwork(cache_path, content)
    return True
