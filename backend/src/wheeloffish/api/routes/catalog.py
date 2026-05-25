from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_current_user, get_db, get_settings_dep, get_vault, require_admin
from wheeloffish.api.schemas.catalog import (
    LibraryScopeResponse,
    LibraryScopeUpdate,
    SeriesBrowseResponse,
    SessionCatalogRefreshResponse,
    SyncStatusEmbed,
    SyncStatusResponse,
)
from wheeloffish.api.schemas.resume import (
    EpisodeResponse,
    EpisodesListResponse,
    ResumePreviewResponse,
)
from wheeloffish.core.catalog_sync import (
    cached_library_to_dto,
    cached_series_to_dto,
    ensure_libraries_cached,
    get_all_libraries,
    get_in_scope_libraries,
    get_sync_status,
    trigger_sync,
    trigger_sync_for_user_links,
    update_library_scope,
)
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import build_provider_for_connection
from wheeloffish.core.resume import ResumeService
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.dto import Library
from wheeloffish.domain.ids import parse_composite_id
from wheeloffish.integrations.base import MediaProvider
from wheeloffish.integrations.errors import ProviderError

router = APIRouter(tags=["catalog"])
admin_router = APIRouter(prefix="/admin", tags=["catalog-admin"])
session_router = APIRouter(prefix="/session", tags=["catalog-session"])


def _get_connection_or_404(db: Session, connection_id: str) -> Connection:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return connection


def _provider_error_to_http(err: ProviderError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": err.code, "message": str(err) or err.code},
    )


def _validate_series_connection(series_id: str, connection_id: str) -> None:
    try:
        parsed_connection_id, _, _ = parse_composite_id(series_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_series_id", "message": str(err)},
        ) from err
    if parsed_connection_id != connection_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_series_id",
                "message": "Series does not belong to connection",
            },
        )


def _build_provider_for_user(
    db: Session,
    vault: SecretsVault,
    connection: Connection,
    app_user_id: str,
    settings: Settings,
) -> MediaProvider:
    link = (
        db.query(UserMediaLink)
        .filter(
            UserMediaLink.connection_id == connection.id,
            UserMediaLink.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unauthorized", "message": "No token for user"},
        )
    token = vault.get_media_user_token(connection.id, app_user_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unauthorized", "message": "No token for user"},
        )
    return build_provider_for_connection(
        connection,
        token,
        settings=settings,
        provider_user_id=link.provider_user_id,
    )


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


@admin_router.get(
    "/connections/{connection_id}/libraries",
    response_model=list[Library],
)
async def get_admin_connection_libraries(
    connection_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
    _: None = Depends(require_admin),
) -> list[Library]:
    connection = _get_connection_or_404(db, connection_id)
    await ensure_libraries_cached(
        db, vault, connection_id, app_user_id, settings=settings
    )
    libraries = get_all_libraries(db, connection_id)
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
    _: None = Depends(get_current_user),
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
    _: None = Depends(get_current_user),
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


@router.get(
    "/connections/{connection_id}/series/{series_id}/episodes",
    response_model=EpisodesListResponse,
)
async def get_series_episodes(
    connection_id: str,
    series_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> EpisodesListResponse:
    connection = _get_connection_or_404(db, connection_id)
    _validate_series_connection(series_id, connection_id)
    provider = _build_provider_for_user(db, vault, connection, app_user_id, settings)
    try:
        episodes = await provider.list_episodes(series_id)
    except ProviderError as err:
        raise _provider_error_to_http(err) from err
    return EpisodesListResponse(
        episodes=[EpisodeResponse.from_dto(episode) for episode in episodes]
    )


@router.get(
    "/connections/{connection_id}/series/{series_id}/resume",
    response_model=ResumePreviewResponse,
)
async def get_series_resume(
    connection_id: str,
    series_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> ResumePreviewResponse:
    connection = _get_connection_or_404(db, connection_id)
    _validate_series_connection(series_id, connection_id)
    provider = _build_provider_for_user(db, vault, connection, app_user_id, settings)
    try:
        episodes = await provider.list_episodes(series_id)
        on_deck = await provider.get_on_deck_episode(series_id)
    except ProviderError as err:
        raise _provider_error_to_http(err) from err
    cursor = ResumeService().compute(series_id, episodes, on_deck)
    return ResumePreviewResponse.from_cursor(cursor)
