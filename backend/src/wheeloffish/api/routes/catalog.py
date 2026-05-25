from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault, require_admin
from wheeloffish.api.schemas.catalog import (
    LibraryScopeResponse,
    LibraryScopeUpdate,
    SeriesBrowseResponse,
    SessionCatalogRefreshResponse,
    SyncStatusEmbed,
    SyncStatusResponse,
)
from wheeloffish.core.catalog_sync import (
    cached_library_to_dto,
    cached_series_to_dto,
    ensure_libraries_cached,
    get_in_scope_libraries,
    get_sync_status,
    trigger_sync,
    trigger_sync_for_user_links,
    update_library_scope,
)
from wheeloffish.core.config import Settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.connection import Connection
from wheeloffish.domain.dto import Library

router = APIRouter(tags=["catalog"])
admin_router = APIRouter(prefix="/admin", tags=["catalog-admin"])
session_router = APIRouter(prefix="/session", tags=["catalog-session"])


def _get_connection_or_404(db: Session, connection_id: str) -> Connection:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return connection


@router.get("/connections/{connection_id}/libraries", response_model=list[Library])
async def get_connection_libraries(
    connection_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> list[Library]:
    connection = _get_connection_or_404(db, connection_id)
    await ensure_libraries_cached(
        db, vault, connection_id, app_user_id, settings=settings
    )
    libraries = get_in_scope_libraries(db, connection_id)
    return [cached_library_to_dto(row, connection.provider_type) for row in libraries]


@admin_router.put(
    "/connections/{connection_id}/library-scope",
    response_model=LibraryScopeResponse,
)
def put_library_scope(
    connection_id: str,
    body: LibraryScopeUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
) -> LibraryScopeResponse:
    _get_connection_or_404(db, connection_id)
    try:
        libraries = update_library_scope(db, connection_id, body.in_scope_library_native_ids)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "no_libraries", "message": str(err)},
        ) from err

    connection = _get_connection_or_404(db, connection_id)
    return LibraryScopeResponse(
        libraries=[cached_library_to_dto(row, connection.provider_type) for row in libraries]
    )


@router.get("/connections/{connection_id}/series", response_model=SeriesBrowseResponse)
def get_connection_series(
    connection_id: str,
    page: int = Query(1, ge=1),
    limit: int | None = Query(None, ge=1, le=200),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> SeriesBrowseResponse:
    connection = _get_connection_or_404(db, connection_id)
    resolved_limit = limit or settings.WOF_CATALOG_PAGE_DEFAULT

    in_scope = get_in_scope_libraries(db, connection_id)
    in_scope_ids = [library.native_id for library in in_scope]

    query = db.query(CachedSeries).filter(CachedSeries.connection_id == connection_id)
    if in_scope_ids:
        query = query.filter(CachedSeries.library_native_id.in_(in_scope_ids))
    else:
        query = query.filter(False)  # noqa: E712

    if q:
        query = query.filter(CachedSeries.title.ilike(f"%{q}%"))

    total = query.count()
    rows = (
        query.order_by(CachedSeries.title)
        .offset((page - 1) * resolved_limit)
        .limit(resolved_limit)
        .all()
    )
    sync = SyncStatusEmbed(**get_sync_status(db, connection_id))
    return SeriesBrowseResponse(
        items=[cached_series_to_dto(row, connection.provider_type) for row in rows],
        page=page,
        limit=resolved_limit,
        total=total,
        sync=sync,
    )


@router.post(
    "/connections/{connection_id}/sync",
    response_model=SyncStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_connection_sync(
    connection_id: str,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> SyncStatusResponse:
    _get_connection_or_404(db, connection_id)
    trigger_sync(db, connection_id, app_user_id)
    return SyncStatusResponse(**get_sync_status(db, connection_id))


@router.get("/connections/{connection_id}/sync/status", response_model=SyncStatusResponse)
def get_connection_sync_status(
    connection_id: str,
    db: Session = Depends(get_db),
) -> SyncStatusResponse:
    _get_connection_or_404(db, connection_id)
    return SyncStatusResponse(**get_sync_status(db, connection_id))


@session_router.post(
    "/catalog-refresh",
    response_model=SessionCatalogRefreshResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_session_catalog_refresh(
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> SessionCatalogRefreshResponse:
    statuses = trigger_sync_for_user_links(db, app_user_id)
    sync_embed = {
        connection_id: SyncStatusEmbed(**status)
        for connection_id, status in statuses.items()
    }
    return SessionCatalogRefreshResponse(sync=sync_embed)
