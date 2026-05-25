from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.connections import build_provider_for_connection
from wheeloffish.core.media_artwork import (
    artwork_cache_path,
    download_and_cache_artwork,
    series_artwork_url,
)
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.cached_library import CachedLibrary
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.catalog_sync_state import CatalogSyncState
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.db.session import get_session_factory
from wheeloffish.domain.dto import Library, Series
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.plex.client import PlexProvider

logger = structlog.get_logger(__name__)

CHUNK_DELAY_SECONDS = 0.25
ARTWORK_BACKFILL_DELAY_SECONDS = 0.05


def _scoped_library_id_set(settings: Settings) -> set[str] | None:
    ids = {item.strip() for item in settings.WOF_SCOPED_LIBRARY_IDS.split(",") if item.strip()}
    return ids if ids else None


def _default_in_scope(native_id: str, settings: Settings) -> bool:
    scoped = _scoped_library_id_set(settings)
    if scoped is None:
        return True
    return native_id in scoped


def _get_or_create_sync_state(db: Session, connection_id: str) -> CatalogSyncState:
    state = (
        db.query(CatalogSyncState)
        .filter(CatalogSyncState.connection_id == connection_id)
        .one_or_none()
    )
    if state is None:
        state = CatalogSyncState(connection_id=connection_id, status="idle")
        db.add(state)
        db.flush()
    return state


def _upsert_series_row(db: Session, series: Series, synced_at: datetime) -> None:
    existing = (
        db.query(CachedSeries)
        .filter(
            CachedSeries.connection_id == series.connection_id,
            CachedSeries.native_id == series.native_id,
        )
        .one_or_none()
    )
    if existing is None:
        db.add(
            CachedSeries(
                id=series.id,
                connection_id=series.connection_id,
                library_native_id=series.library_native_id,
                native_id=series.native_id,
                title=series.title,
                title_sort=None,
                year=series.year,
                thumb_url=series.thumb_url,
                provider_metadata=series.provider_metadata,
                synced_at=synced_at,
            )
        )
        return

    existing.id = series.id
    existing.library_native_id = series.library_native_id
    existing.title = series.title
    existing.year = series.year
    existing.thumb_url = series.thumb_url
    existing.provider_metadata = series.provider_metadata
    existing.synced_at = synced_at


def cached_library_to_dto(cached: CachedLibrary, provider: str) -> Library:
    return Library(
        id=format_composite_id(cached.connection_id, provider, cached.native_id),
        title=cached.title,
        native_id=cached.native_id,
        connection_id=cached.connection_id,
        provider=provider,
        in_scope=cached.in_scope,
    )


def cached_series_to_dto(row: CachedSeries, provider: str) -> Series:
    return Series(
        id=row.id,
        title=row.title,
        native_id=row.native_id,
        library_native_id=row.library_native_id,
        connection_id=row.connection_id,
        provider=provider,
        year=row.year,
        thumb_url=series_artwork_url(row.connection_id, row.id),
        provider_metadata=row.provider_metadata,
    )


def _get_user_media_link(db: Session, connection_id: str, app_user_id: str) -> UserMediaLink:
    link = (
        db.query(UserMediaLink)
        .filter(
            UserMediaLink.connection_id == connection_id,
            UserMediaLink.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if link is None:
        raise ValueError(f"No media link for connection {connection_id}")
    return link


def _build_provider(
    db: Session,
    vault: SecretsVault,
    connection: Connection,
    app_user_id: str,
    settings: Settings,
):
    link = _get_user_media_link(db, connection.id, app_user_id)
    token = vault.get_media_user_token(connection.id, app_user_id)
    if token is None:
        raise ValueError(f"No token for connection {connection.id}")
    return build_provider_for_connection(
        connection,
        token,
        settings=settings,
        provider_user_id=link.provider_user_id,
    )


async def ensure_libraries_cached(
    db: Session,
    vault: SecretsVault,
    connection_id: str,
    app_user_id: str,
    *,
    settings: Settings | None = None,
) -> list[CachedLibrary]:
    resolved_settings = settings or get_settings()
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise ValueError("Connection not found")

    cached = db.query(CachedLibrary).filter(CachedLibrary.connection_id == connection_id).all()
    if cached:
        return cached

    provider = _build_provider(db, vault, connection, app_user_id, resolved_settings)
    libraries = await provider.list_libraries()
    now = datetime.now(UTC)
    rows: list[CachedLibrary] = []
    for library in libraries:
        row = CachedLibrary(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            native_id=library.native_id,
            title=library.title,
            in_scope=_default_in_scope(library.native_id, resolved_settings),
            synced_at=now,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def get_in_scope_libraries(db: Session, connection_id: str) -> list[CachedLibrary]:
    return (
        db.query(CachedLibrary)
        .filter(CachedLibrary.connection_id == connection_id, CachedLibrary.in_scope.is_(True))
        .order_by(CachedLibrary.title)
        .all()
    )


def get_all_libraries(db: Session, connection_id: str) -> list[CachedLibrary]:
    return (
        db.query(CachedLibrary)
        .filter(CachedLibrary.connection_id == connection_id)
        .order_by(CachedLibrary.title)
        .all()
    )


def update_library_scope(
    db: Session,
    connection_id: str,
    in_scope_library_native_ids: list[str],
) -> list[CachedLibrary]:
    in_scope_set = set(in_scope_library_native_ids)
    libraries = db.query(CachedLibrary).filter(CachedLibrary.connection_id == connection_id).all()
    if not libraries:
        raise ValueError("No cached libraries for connection")

    now = datetime.now(UTC)
    for library in libraries:
        library.in_scope = library.native_id in in_scope_set
        library.synced_at = now
    db.commit()
    return get_in_scope_libraries(db, connection_id)


def get_sync_status(db: Session, connection_id: str) -> dict:
    state = (
        db.query(CatalogSyncState)
        .filter(CatalogSyncState.connection_id == connection_id)
        .one_or_none()
    )
    if state is None:
        return {
            "status": "idle",
            "progress_pct": None,
            "library_native_id": None,
            "error_message": None,
        }

    progress_pct: float | None = None
    if state.total_estimated and state.total_estimated > 0:
        progress_pct = min(100.0, round((state.page_cursor / state.total_estimated) * 100, 2))

    return {
        "status": state.status,
        "progress_pct": progress_pct,
        "library_native_id": state.library_native_id,
        "error_message": state.error_message,
    }


def trigger_sync(db: Session, connection_id: str, app_user_id: str) -> None:
    state = _get_or_create_sync_state(db, connection_id)
    now = datetime.now(UTC)
    state.status = "running"
    state.library_native_id = None
    state.page_cursor = 0
    state.total_estimated = None
    state.error_message = None
    state.started_at = now
    state.updated_at = now
    db.commit()

    asyncio.create_task(run_chunked_sync(connection_id, app_user_id))


async def run_chunked_sync(connection_id: str, app_user_id: str) -> None:
    settings = get_settings()
    session_factory = get_session_factory(settings)
    db = session_factory()
    vault = SecretsVault(db, settings)

    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
        if connection is None:
            raise ValueError("Connection not found")

        await ensure_libraries_cached(db, vault, connection_id, app_user_id, settings=settings)
        libraries = get_in_scope_libraries(db, connection_id)
        provider = _build_provider(db, vault, connection, app_user_id, settings)
        chunk_size = settings.WOF_CATALOG_SYNC_CHUNK_SIZE
        total_synced = 0
        total_estimated = 0

        state = _get_or_create_sync_state(db, connection_id)
        for library in libraries:
            page = 1
            while True:
                state.library_native_id = library.native_id
                state.updated_at = datetime.now(UTC)
                db.commit()

                page_result = await provider.list_series(
                    library.native_id,
                    page=page,
                    limit=chunk_size,
                    q=None,
                )
                synced_at = datetime.now(UTC)
                for series in page_result.items:
                    _upsert_series_row(db, series, synced_at)
                    total_synced += 1

                total_estimated = max(total_estimated, page_result.total)
                state.page_cursor = total_synced
                state.total_estimated = total_estimated
                state.updated_at = synced_at
                db.commit()

                if not page_result.items or len(page_result.items) < chunk_size:
                    break
                if page * chunk_size >= page_result.total:
                    break

                page += 1
                await asyncio.sleep(CHUNK_DELAY_SECONDS)

        artwork_cached = 0
        artwork_failed = 0
        if isinstance(provider, PlexProvider):
            artwork_cached, artwork_failed = await backfill_artwork_for_connection(
                db, provider, connection_id, settings
            )

        state = _get_or_create_sync_state(db, connection_id)
        state.status = "complete"
        state.page_cursor = total_synced
        state.total_estimated = total_estimated or total_synced
        state.error_message = None
        state.updated_at = datetime.now(UTC)
        db.commit()
        logger.info(
            "catalog_sync_complete",
            connection_id=connection_id,
            series_count=total_synced,
            artwork_cached=artwork_cached,
            artwork_failed=artwork_failed,
        )
    except (ProviderError, ValueError, Exception) as err:
        db.rollback()
        state = _get_or_create_sync_state(db, connection_id)
        state.status = "failed"
        state.error_message = str(err)
        state.updated_at = datetime.now(UTC)
        db.commit()
        logger.exception("catalog_sync_failed", connection_id=connection_id, error=str(err))
    finally:
        db.close()


def trigger_sync_for_user_links(db: Session, app_user_id: str) -> dict[str, dict]:
    links = db.query(UserMediaLink).filter(UserMediaLink.app_user_id == app_user_id).all()
    statuses: dict[str, dict] = {}
    for link in links:
        trigger_sync(db, link.connection_id, app_user_id)
        statuses[link.connection_id] = get_sync_status(db, link.connection_id)
    return statuses


async def backfill_artwork_for_connection(
    db: Session,
    provider: PlexProvider,
    connection_id: str,
    settings: Settings,
) -> tuple[int, int]:
    """Ensure every in-scope cached series has a local poster file."""
    in_scope = get_in_scope_libraries(db, connection_id)
    in_scope_ids = [library.native_id for library in in_scope]
    if not in_scope_ids:
        return 0, 0

    query = db.query(CachedSeries).filter(
        CachedSeries.connection_id == connection_id,
        CachedSeries.library_native_id.in_(in_scope_ids),
    )

    cached_count = 0
    failed_count = 0
    for row in query.all():
        cache_path = artwork_cache_path(settings.WOF_ARTWORK_CACHE_DIR, connection_id, row.id)
        if cache_path.is_file():
            cached_count += 1
            continue
        if not row.thumb_url:
            failed_count += 1
            continue
        ok = await download_and_cache_artwork(
            provider,
            cache_dir=settings.WOF_ARTWORK_CACHE_DIR,
            connection_id=connection_id,
            series_id=row.id,
            thumb_url=row.thumb_url,
        )
        if ok:
            cached_count += 1
        else:
            failed_count += 1
        await asyncio.sleep(ARTWORK_BACKFILL_DELAY_SECONDS)

    return cached_count, failed_count
