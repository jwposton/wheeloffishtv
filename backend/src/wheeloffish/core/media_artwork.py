from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from urllib.parse import quote, urlparse

from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.plex.client import PlexProvider

logger = logging.getLogger(__name__)


def artwork_cache_path(cache_dir: str, connection_id: str, series_id: str) -> Path:
    """Deterministic on-disk path for a series poster."""
    digest = hashlib.sha256(series_id.encode()).hexdigest()[:32]
    return Path(cache_dir) / connection_id / f"{digest}.img"


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


def read_cached_artwork(cache_path: Path) -> tuple[bytes, str] | None:
    if not cache_path.is_file():
        return None
    content = cache_path.read_bytes()
    suffix = cache_path.suffix.lower()
    media_type = "image/jpeg" if suffix in {".img", ".jpg", ".jpeg"} else "application/octet-stream"
    return content, media_type


def write_cached_artwork(cache_path: Path, content: bytes) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)


async def download_and_cache_artwork(
    provider: PlexProvider,
    *,
    cache_dir: str,
    connection_id: str,
    series_id: str,
    thumb_url: str | None,
) -> bool:
    """Fetch poster bytes from Plex and persist locally. Returns True if cached."""
    thumb_path = normalize_plex_artwork_path(thumb_url)
    if thumb_path is None:
        return False

    cache_path = artwork_cache_path(cache_dir, connection_id, series_id)
    if cache_path.is_file():
        return True

    try:
        content, _media_type = await provider.fetch_artwork(thumb_path)
    except ProviderError:
        logger.warning(
            "artwork_download_failed",
            extra={"connection_id": connection_id, "series_id": series_id},
        )
        return False

    write_cached_artwork(cache_path, content)
    return True
