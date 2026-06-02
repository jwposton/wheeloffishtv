"""Live episode fetch helper for nightly rebuild orchestrator (D-11, D-13, D-14).

Extracts provider calls from the HTTP layer so the scheduler can reuse them
without making in-process HTTP requests.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.ids import canonical_composite_id, parse_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput
from wheeloffish.integrations.base import MediaProvider
from wheeloffish.integrations.errors import ProviderError, ProviderNotFound

logger = structlog.get_logger("wheeloffish.rebuild_inputs")


@dataclass
class FetchResult:
    input: SeriesRebuildInput | None
    reason: str  # "ok" | "empty_snapshot" | "not_found" | "fetch_failure"


def _get_provider_context(
    db: Session,
    series_id: str,
    app_user_id: str,
) -> tuple[str | None, str | None]:
    """Return (rating_key, library_native_id) from cached series, or (None, None)."""
    canonical_id = canonical_composite_id(series_id)
    row = (
        db.query(CachedSeries)
        .filter(CachedSeries.id == canonical_id, CachedSeries.app_user_id == app_user_id)
        .one_or_none()
    )
    if row is None:
        _, _, native_id = parse_composite_id(canonical_id)
        row = (
            db.query(CachedSeries)
            .filter(
                CachedSeries.app_user_id == app_user_id,
                CachedSeries.native_id == native_id,
            )
            .one_or_none()
        )
    if row is None:
        return None, None
    rating_key: str | None = None
    if row.provider_metadata:
        cached_key = row.provider_metadata.get("ratingKey")
        if cached_key is not None:
            rating_key = str(cached_key)
    return rating_key, row.library_native_id


async def _fetch_episodes(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> list[Episode]:
    try:
        return await provider.list_episodes(  # type: ignore[call-arg]
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
    except TypeError:
        return await provider.list_episodes(series_id)


async def _fetch_on_deck(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> Episode | None:
    try:
        return await provider.get_on_deck_episode(  # type: ignore[attr-defined]
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
    except TypeError:
        return await provider.get_on_deck_episode(series_id)  # type: ignore[attr-defined]
    except ProviderError:
        return None


async def fetch_rebuild_inputs_for_row(
    db: Session,
    app_user_id: str,
    connection_id: str,  # noqa: ARG001 — reserved for future multi-connection support
    series_id: str,
    provider: MediaProvider,
) -> FetchResult:
    """Fetch episodes + on_deck for one playlist row.

    Returns FetchResult with reason taxonomy for orchestrator evidence (D-02).
    """
    rating_key, library_native_id = _get_provider_context(db, series_id, app_user_id)
    try:
        episodes_result, on_deck_result = await asyncio.gather(
            _fetch_episodes(
                provider, series_id, rating_key=rating_key, library_native_id=library_native_id
            ),
            _fetch_on_deck(
                provider, series_id, rating_key=rating_key, library_native_id=library_native_id
            ),
            return_exceptions=True,
        )
    except Exception as exc:
        logger.warning("fetch_rebuild_inputs_exception", series_id=series_id, error=str(exc))
        return FetchResult(None, "fetch_failure")

    if isinstance(episodes_result, ProviderNotFound):
        logger.warning(
            "fetch_episodes_not_found", series_id=series_id, error=str(episodes_result)
        )
        return FetchResult(None, "not_found")
    if isinstance(episodes_result, ProviderError):
        logger.warning(
            "fetch_episodes_provider_error", series_id=series_id, error=str(episodes_result)
        )
        return FetchResult(None, "fetch_failure")
    if isinstance(episodes_result, BaseException):
        logger.warning("fetch_episodes_failed", series_id=series_id, error=str(episodes_result))
        return FetchResult(None, "fetch_failure")

    episodes: list[Episode] = episodes_result
    on_deck: Episode | None = None if isinstance(on_deck_result, BaseException) else on_deck_result

    inp = SeriesRebuildInput(series_id=series_id, episodes=episodes, on_deck=on_deck)
    if not episodes:
        return FetchResult(inp, "empty_snapshot")
    return FetchResult(inp, "ok")


async def check_provider_reachable(provider: MediaProvider) -> bool:
    """Return True if provider responds to ping (D-13 single reachability check)."""
    try:
        await provider.ping()
        return True
    except Exception:
        return False
