"""Compare installed version against the latest GitHub release."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from wheeloffish import __version__

GITHUB_REPO = "jwposton/wheeloffishtv"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_TTL_SECONDS = 3600


@dataclass(frozen=True)
class VersionInfo:
    version: str
    latest_version: str | None
    update_available: bool
    release_url: str | None


@dataclass
class _ReleaseCache:
    fetched_at: float
    latest_version: str | None
    release_url: str | None


_release_cache: _ReleaseCache | None = None


def reset_release_cache() -> None:
    global _release_cache
    _release_cache = None


def _parse_version(value: str) -> tuple[int, ...]:
    normalized = value.strip().removeprefix("v")
    parts: list[int] = []
    for segment in normalized.split(".")[:4]:
        digits = ""
        for char in segment:
            if char.isdigit():
                digits += char
            else:
                break
        if digits:
            parts.append(int(digits))
    return tuple(parts)


def is_newer_version(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def _fetch_latest_release() -> tuple[str | None, str | None]:
    try:
        response = httpx.get(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None, None

    tag_name = payload.get("tag_name")
    html_url = payload.get("html_url")
    if not isinstance(tag_name, str) or not tag_name:
        return None, None
    release_url = html_url if isinstance(html_url, str) else None
    return tag_name.removeprefix("v"), release_url


def _cached_latest_release() -> tuple[str | None, str | None]:
    global _release_cache
    now = time.monotonic()
    if _release_cache is not None and now - _release_cache.fetched_at < CACHE_TTL_SECONDS:
        return _release_cache.latest_version, _release_cache.release_url

    latest_version, release_url = _fetch_latest_release()
    _release_cache = _ReleaseCache(
        fetched_at=now,
        latest_version=latest_version,
        release_url=release_url,
    )
    return latest_version, release_url


def get_version_info() -> VersionInfo:
    latest_version, release_url = _cached_latest_release()
    update_available = bool(
        latest_version and is_newer_version(latest_version, __version__),
    )
    return VersionInfo(
        version=__version__,
        latest_version=latest_version,
        update_available=update_available,
        release_url=release_url if update_available else None,
    )
