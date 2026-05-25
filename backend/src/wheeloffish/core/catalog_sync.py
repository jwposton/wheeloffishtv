from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import or_
from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.connections import build_provider_for_connection, build_plex_provider_for_user
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
from wheeloffish.integrations.errors import ProviderError, ProviderUnauthorized
from wheeloffish.integrations.plex.client import PlexProvider

logger = structlog.get_logger(__name__)

ARTWORK_PREFETCH_DELAY_SECONDS = 0
SYNC_RUNNING_STALE_SECONDS = 180
PLEX_REQUEST_TIMEOUT_SECONDS = 60.0


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _sync_is_stale(state: CatalogSyncState, now: datetime) -> bool:
    if state.status != "running":
        return False
    if state.updated_at is None:
        return True
    updated_at = _as_utc(state.updated_at)
    return (now - updated_at).total_seconds() > SYNC_RUNNING_STALE_SECONDS


def _mark_sync_stale_failed(
    db: Session,
    state: CatalogSyncState,
    now: datetime,
) -> None:
    state.status = "failed"
    state.error_message = "Sync stalled — try again"
    state.updated_at = now
    db.commit()


def _scoped_library_id_set(settings: Settings) -> set[str] | None:
    ids = {item.strip() for item in settings.WOF_SCOPED_LIBRARY_IDS.split(",") if item.strip()}
    return ids if ids else None


def get_install_allowlist(connection: Connection, settings: Settings) -> set[str] | None:
    """Install-level library allowlist. None means not configured yet."""
    if connection.library_allowlist_native_ids is not None:
        return set(connection.library_allowlist_native_ids)
    return _scoped_library_id_set(settings)


def install_libraries_configured(connection: Connection, settings: Settings) -> bool:
    """True once admin (or env) has defined the install library allowlist."""
    if connection.library_allowlist_native_ids is not None:
        return True
    return _scoped_library_id_set(settings) is not None


def _library_in_scope(
    native_id: str,
    connection: Connection,
    settings: Settings,
) -> bool:
    allowlist = get_install_allowlist(connection, settings)
    if allowlist is None:
        return False
    return native_id in allowlist


def _apply_allowlist_to_connection_libraries(
    db: Session,
    connection: Connection,
    settings: Settings,
) -> None:
    allowlist = get_install_allowlist(connection, settings)
    if allowlist is None:
        return
    libraries = (
        db.query(CachedLibrary).filter(CachedLibrary.connection_id == connection.id).all()
    )
    now = datetime.now(UTC)
    for library in libraries:
        library.in_scope = library.native_id in allowlist
        library.synced_at = now


def _get_or_create_sync_state(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> CatalogSyncState:
    state = (
        db.query(CatalogSyncState)
        .filter(
            CatalogSyncState.connection_id == connection_id,
            CatalogSyncState.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if state is None:
        state = CatalogSyncState(
            connection_id=connection_id,
            app_user_id=app_user_id,
            status="idle",
        )
        db.add(state)
        db.flush()
    return state


def _upsert_series_page(
    db: Session,
    items: list[Series],
    app_user_id: str,
    synced_at: datetime,
) -> None:
    """Upsert a page of series with one lookup query instead of per-row."""
    if not items:
        return

    # Plex may return the same show twice in one page (or under multiple guids).
    deduped: dict[str, Series] = {}
    for series in items:
        deduped[series.id] = series
    unique_items = list(deduped.values())

    connection_id = unique_items[0].connection_id
    native_ids = [series.native_id for series in unique_items]
    series_ids = [series.id for series in unique_items]
    existing_rows = (
        db.query(CachedSeries)
        .filter(
            CachedSeries.app_user_id == app_user_id,
            CachedSeries.connection_id == connection_id,
            or_(
                CachedSeries.native_id.in_(native_ids),
                CachedSeries.id.in_(series_ids),
            ),
        )
        .all()
    )
    by_native_id = {row.native_id: row for row in existing_rows}
    by_id = {row.id: row for row in existing_rows}
    pending_by_id: dict[str, CachedSeries] = {}

    for series in unique_items:
        existing = (
            by_native_id.get(series.native_id)
            or by_id.get(series.id)
            or pending_by_id.get(series.id)
        )
        if existing is None:
            row = CachedSeries(
                id=series.id,
                app_user_id=app_user_id,
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
            db.add(row)
            pending_by_id[series.id] = row
            by_native_id[series.native_id] = row
            by_id[series.id] = row
            continue

        existing.id = series.id
        existing.native_id = series.native_id
        existing.library_native_id = series.library_native_id
        existing.title = series.title
        existing.year = series.year
        existing.thumb_url = series.thumb_url
        existing.provider_metadata = series.provider_metadata
        existing.synced_at = synced_at
        by_native_id[series.native_id] = existing
        by_id[series.id] = existing


def _upsert_series_row(
    db: Session,
    series: Series,
    app_user_id: str,
    synced_at: datetime,
) -> None:
    _upsert_series_page(db, [series], app_user_id, synced_at)


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
    if connection.provider_type == "plex":
        credentials = vault.get_plex_user_credentials(connection.id, app_user_id)
        if credentials is None:
            raise ValueError(
                "Missing Plex credentials — log out and reconnect your Plex account"
            )
        return build_plex_provider_for_user(
            connection,
            credentials,
            settings=settings,
            provider_user_id=link.provider_user_id,
        )

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

    provider = _build_provider(db, vault, connection, app_user_id, resolved_settings)
    libraries = await provider.list_libraries()
    now = datetime.now(UTC)

    existing = (
        db.query(CachedLibrary)
        .filter(
            CachedLibrary.connection_id == connection_id,
            CachedLibrary.app_user_id == app_user_id,
        )
        .all()
    )
    by_native_id = {row.native_id: row for row in existing}
    seen_native_ids: set[str] = set()
    rows: list[CachedLibrary] = []

    for library in libraries:
        seen_native_ids.add(library.native_id)
        in_scope = _library_in_scope(library.native_id, connection, resolved_settings)
        row = by_native_id.get(library.native_id)
        if row is None:
            row = CachedLibrary(
                id=str(uuid.uuid4()),
                app_user_id=app_user_id,
                connection_id=connection_id,
                native_id=library.native_id,
                title=library.title,
                in_scope=in_scope,
                synced_at=now,
            )
            db.add(row)
        else:
            row.title = library.title
            row.in_scope = in_scope
            row.synced_at = now
        rows.append(row)

    for native_id, row in by_native_id.items():
        if native_id not in seen_native_ids:
            db.delete(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def get_in_scope_libraries(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> list[CachedLibrary]:
    return (
        db.query(CachedLibrary)
        .filter(
            CachedLibrary.connection_id == connection_id,
            CachedLibrary.app_user_id == app_user_id,
            CachedLibrary.in_scope.is_(True),
        )
        .order_by(CachedLibrary.title)
        .all()
    )


def get_all_libraries(
    db: Session,
    connection_id: str,
    app_user_id: str,
) -> list[CachedLibrary]:
    return (
        db.query(CachedLibrary)
        .filter(
            CachedLibrary.connection_id == connection_id,
            CachedLibrary.app_user_id == app_user_id,
        )
        .order_by(CachedLibrary.title)
        .all()
    )


def update_library_scope(
    db: Session,
    connection_id: str,
    app_user_id: str,
    in_scope_library_native_ids: list[str],
) -> list[CachedLibrary]:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise ValueError("Connection not found")

    admin_libraries = get_all_libraries(db, connection_id, app_user_id)
    if not admin_libraries:
        raise ValueError("No cached libraries for connection")

    connection.library_allowlist_native_ids = list(in_scope_library_native_ids)
    _apply_allowlist_to_connection_libraries(db, connection, get_settings())
    db.commit()
    return get_all_libraries(db, connection_id, app_user_id)


def get_sync_status(db: Session, connection_id: str, app_user_id: str) -> dict:
    state = (
        db.query(CatalogSyncState)
        .filter(
            CatalogSyncState.connection_id == connection_id,
            CatalogSyncState.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if state is None:
        return {
            "status": "idle",
            "progress_pct": None,
            "library_native_id": None,
            "error_message": None,
        }

    now = datetime.now(UTC)
    if _sync_is_stale(state, now):
        _mark_sync_stale_failed(db, state, now)
        return {
            "status": "failed",
            "progress_pct": None,
            "library_native_id": state.library_native_id,
            "error_message": state.error_message,
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
    state = _get_or_create_sync_state(db, connection_id, app_user_id)
    now = datetime.now(UTC)
    if state.status == "running" and not _sync_is_stale(state, now):
        return
    if state.status == "running" and _sync_is_stale(state, now):
        logger.warning(
            "catalog_sync_stale_restarting",
            connection_id=connection_id,
            app_user_id=app_user_id,
        )
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
        libraries = get_in_scope_libraries(db, connection_id, app_user_id)
        provider = _build_provider(db, vault, connection, app_user_id, settings)

        sync_started_at = datetime.now(UTC)
        chunk_size = settings.WOF_CATALOG_SYNC_CHUNK_SIZE
        total_synced = 0
        total_estimated = 0

        for library in libraries:
            page = 1
            while True:
                try:
                    page_result = await provider.list_series(
                        library.native_id,
                        page=page,
                        limit=chunk_size,
                        q=None,
                    )
                except ProviderUnauthorized:
                    logger.info(
                        "catalog_sync_library_skipped",
                        connection_id=connection_id,
                        app_user_id=app_user_id,
                        library_native_id=library.native_id,
                        reason="unauthorized",
                    )
                    break
                synced_at = datetime.now(UTC)
                _upsert_series_page(db, page_result.items, app_user_id, synced_at)
                total_synced += len(page_result.items)

                total_estimated = max(total_estimated, page_result.total)
                state = _get_or_create_sync_state(db, connection_id, app_user_id)
                state.library_native_id = library.native_id
                state.page_cursor = total_synced
                state.total_estimated = total_estimated
                state.updated_at = synced_at
                db.commit()
                logger.info(
                    "catalog_sync_page",
                    connection_id=connection_id,
                    app_user_id=app_user_id,
                    library_native_id=library.native_id,
                    page=page,
                    page_items=len(page_result.items),
                    total_synced=total_synced,
                    total_estimated=total_estimated,
                )

                if not page_result.items or len(page_result.items) < chunk_size:
                    break
                if page * chunk_size >= page_result.total:
                    break

                page += 1

        state = _get_or_create_sync_state(db, connection_id, app_user_id)
        state.status = "complete"
        state.page_cursor = total_synced
        state.total_estimated = total_estimated or total_synced
        state.error_message = None
        state.updated_at = datetime.now(UTC)
        db.commit()

        db.query(CachedSeries).filter(
            CachedSeries.connection_id == connection_id,
            CachedSeries.app_user_id == app_user_id,
            CachedSeries.synced_at < sync_started_at,
        ).delete()
        db.commit()

        logger.info(
            "catalog_sync_complete",
            connection_id=connection_id,
            app_user_id=app_user_id,
            series_count=total_synced,
        )

        if isinstance(provider, PlexProvider):
            asyncio.create_task(
                prefetch_user_artwork(connection_id, app_user_id),
            )
    except ProviderUnauthorized as err:
        db.rollback()
        vault.clear_plex_user_credentials(connection_id, app_user_id, commit=False)
        state = _get_or_create_sync_state(db, connection_id, app_user_id)
        state.status = "failed"
        state.error_message = (
            "Plex session invalid — log out and sign in with Plex again"
        )
        state.updated_at = datetime.now(UTC)
        db.commit()
        logger.exception(
            "catalog_sync_failed",
            connection_id=connection_id,
            app_user_id=app_user_id,
            error=str(err),
        )
    except (ProviderError, ValueError, Exception) as err:
        db.rollback()
        state = _get_or_create_sync_state(db, connection_id, app_user_id)
        state.status = "failed"
        state.error_message = str(err)
        state.updated_at = datetime.now(UTC)
        db.commit()
        logger.exception(
            "catalog_sync_failed",
            connection_id=connection_id,
            app_user_id=app_user_id,
            error=str(err),
        )
    finally:
        db.close()


def trigger_sync_for_user_links(db: Session, app_user_id: str) -> dict[str, dict]:
    links = db.query(UserMediaLink).filter(UserMediaLink.app_user_id == app_user_id).all()
    statuses: dict[str, dict] = {}
    for link in links:
        trigger_sync(db, link.connection_id, app_user_id)
        statuses[link.connection_id] = get_sync_status(db, link.connection_id, app_user_id)
    return statuses


async def prefetch_user_artwork(connection_id: str, app_user_id: str) -> None:
    """Background poster download after catalog metadata sync (non-blocking)."""
    settings = get_settings()
    session_factory = get_session_factory(settings)
    db = session_factory()
    vault = SecretsVault(db, settings)

    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
        if connection is None:
            return

        provider = _build_provider(db, vault, connection, app_user_id, settings)
        if not isinstance(provider, PlexProvider):
            return

        rows = (
            db.query(CachedSeries)
            .filter(
                CachedSeries.connection_id == connection_id,
                CachedSeries.app_user_id == app_user_id,
            )
            .all()
        )
        cached_count = 0
        failed_count = 0
        for row in rows:
            if not row.thumb_url:
                failed_count += 1
                continue
            cache_path = artwork_cache_path(
                settings.WOF_ARTWORK_CACHE_DIR,
                app_user_id,
                connection_id,
                row.id,
            )
            if cache_path.is_file():
                cached_count += 1
                continue
            ok = await download_and_cache_artwork(
                provider,
                cache_dir=settings.WOF_ARTWORK_CACHE_DIR,
                app_user_id=app_user_id,
                connection_id=connection_id,
                series_id=row.id,
                thumb_url=row.thumb_url,
            )
            if ok:
                cached_count += 1
            else:
                failed_count += 1
            await asyncio.sleep(ARTWORK_PREFETCH_DELAY_SECONDS)

        logger.info(
            "artwork_prefetch_complete",
            connection_id=connection_id,
            app_user_id=app_user_id,
            artwork_cached=cached_count,
            artwork_failed=failed_count,
        )
    except Exception as err:
        logger.warning(
            "artwork_prefetch_aborted",
            connection_id=connection_id,
            app_user_id=app_user_id,
            error=str(err),
        )
    finally:
        db.close()
