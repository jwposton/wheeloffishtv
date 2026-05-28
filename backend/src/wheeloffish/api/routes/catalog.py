import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import asc, desc, nullsfirst, nullslast
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.catalog import (
    LibraryScopeResponse,
    LibraryScopeUpdate,
    SeriesBrowseResponse,
    SessionCatalogRefreshResponse,
    SyncStatusEmbed,
    SyncStatusResponse,
    WatchStateMutationRequest,
    WatchStateMutationResponse,
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
from wheeloffish.core.connections import build_provider_for_user
from wheeloffish.core.media_artwork import (
    artwork_cache_path,
    download_and_cache_artwork,
    read_cached_artwork,
    resolve_series_artwork_fetch_path,
)
from wheeloffish.core.resume import ResumeService
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.connection import Connection
from wheeloffish.domain.dto import Episode, Library, ResumeCursor, Series
from wheeloffish.domain.ids import canonical_composite_id, parse_composite_id
from wheeloffish.integrations.base import MediaProvider, WatchMutationRequest
from wheeloffish.integrations.errors import ProviderError, ProviderNotFound, ProviderUnauthorized
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.plex.client import PlexProvider

router = APIRouter(tags=["catalog"])
session_router = APIRouter(prefix="/session", tags=["catalog-session"])


def _series_browse_order_by(
    sort: Literal["title", "added_at"],
    order: Literal["asc", "desc"],
) -> tuple:
    if sort == "added_at":
        if order == "desc":
            return (nullslast(desc(CachedSeries.library_added_at)), asc(CachedSeries.title))
        return (nullsfirst(asc(CachedSeries.library_added_at)), asc(CachedSeries.title))
    if order == "desc":
        return (desc(CachedSeries.title),)
    return (asc(CachedSeries.title),)


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


def _watch_state_error_response(
    *,
    scope: str,
    target_id: str,
    error_code: Literal["auth", "forbidden", "not_found", "provider_error"],
    message: str,
) -> WatchStateMutationResponse:
    return WatchStateMutationResponse(
        status="failed",
        scope=scope,
        updated_count=0,
        failed_count=1,
        failed_ids=[target_id],
        error_code=error_code,
        message=message,
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


def _cached_series_context(
    db: Session,
    series_id: str,
    app_user_id: str,
) -> tuple[str | None, str | None]:
    """Return cached ratingKey and library_native_id when sync stored them."""
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


async def _list_episodes(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> list[Episode]:
    try:
        return await provider.list_episodes(
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
    except TypeError:
        return await provider.list_episodes(series_id)


async def _get_on_deck_episode(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> Episode | None:
    try:
        return await provider.get_on_deck_episode(
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
    except TypeError:
        return await provider.get_on_deck_episode(series_id)


def _get_cached_series_in_scope(
    db: Session,
    connection_id: str,
    series_id: str,
    app_user_id: str,
) -> CachedSeries:
    canonical_id = canonical_composite_id(series_id)
    _validate_series_connection(canonical_id, connection_id)
    row = (
        db.query(CachedSeries)
        .filter(
            CachedSeries.id == canonical_id,
            CachedSeries.connection_id == connection_id,
            CachedSeries.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if row is None:
        _, _, native_id = parse_composite_id(canonical_id)
        row = (
            db.query(CachedSeries)
            .filter(
                CachedSeries.connection_id == connection_id,
                CachedSeries.app_user_id == app_user_id,
                CachedSeries.native_id == native_id,
            )
            .one_or_none()
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")

    in_scope_ids = {
        library.native_id
        for library in get_in_scope_libraries(db, connection_id, app_user_id)
    }
    if row.library_native_id not in in_scope_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    return row


async def _fetch_resume_data(
    provider: MediaProvider,
    series_id: str,
    *,
    rating_key: str | None,
    library_native_id: str | None,
) -> tuple[list[Episode], Episode | None]:
    episodes_coro = _list_episodes(
        provider,
        series_id,
        rating_key=rating_key,
        library_native_id=library_native_id,
    )
    on_deck_coro = _get_on_deck_episode(
        provider,
        series_id,
        rating_key=rating_key,
        library_native_id=library_native_id,
    )

    episodes_result, on_deck_result = await asyncio.gather(
        episodes_coro,
        on_deck_coro,
        return_exceptions=True,
    )

    episodes: list[Episode] = []
    on_deck: Episode | None = None

    if isinstance(episodes_result, BaseException):
        if not isinstance(on_deck_result, BaseException):
            on_deck = on_deck_result
        elif isinstance(episodes_result, ProviderError):
            raise episodes_result
        else:
            raise ProviderError(str(episodes_result)) from episodes_result
    else:
        episodes = episodes_result

    if isinstance(on_deck_result, BaseException):
        if not isinstance(on_deck_result, ProviderError):
            raise ProviderError(str(on_deck_result)) from on_deck_result
    else:
        on_deck = on_deck_result

    return episodes, on_deck


def _resume_cursor(
    series_id: str,
    episodes: list[Episode],
    on_deck: Episode | None,
) -> ResumeCursor:
    if not episodes and on_deck is not None:
        return ResumeCursor(
            series_id=series_id,
            episode_id=on_deck.id,
            season_index=on_deck.season_index,
            episode_index=on_deck.episode_index,
            percent_watched=on_deck.percent_watched,
            source="on_deck",
            series_complete=False,
            episode=on_deck,
        )
    return ResumeService().compute(series_id, episodes, on_deck)


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
    libraries = get_all_libraries(db, connection_id, app_user_id)
    return [cached_library_to_dto(row, connection.provider_type) for row in libraries]


@router.put(
    "/connections/{connection_id}/library-scope",
    response_model=LibraryScopeResponse,
)
def put_library_scope(
    connection_id: str,
    body: LibraryScopeUpdate,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> LibraryScopeResponse:
    _get_connection_or_404(db, connection_id)
    try:
        libraries = update_library_scope(
            db,
            connection_id,
            app_user_id,
            body.in_scope_library_native_ids,
        )
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
    sort: Literal["title", "added_at"] = Query("title"),
    order: Literal["asc", "desc"] | None = Query(None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> SeriesBrowseResponse:
    connection = _get_connection_or_404(db, connection_id)
    resolved_limit = limit or settings.WOF_CATALOG_PAGE_DEFAULT

    in_scope = get_in_scope_libraries(db, connection_id, app_user_id)
    in_scope_ids = [library.native_id for library in in_scope]

    query = db.query(CachedSeries).filter(
        CachedSeries.connection_id == connection_id,
        CachedSeries.app_user_id == app_user_id,
    )
    if in_scope_ids:
        query = query.filter(CachedSeries.library_native_id.in_(in_scope_ids))
    else:
        query = query.filter(False)  # noqa: E712

    if q:
        filtered = query.filter(CachedSeries.title.ilike(f"%{q}%"))
    else:
        filtered = query

    total = filtered.count()
    resolved_order: Literal["asc", "desc"] = (
        order if order is not None else ("desc" if sort == "added_at" else "asc")
    )
    rows = (
        filtered.order_by(*_series_browse_order_by(sort, resolved_order))
        .offset((page - 1) * resolved_limit)
        .limit(resolved_limit)
        .all()
    )
    sync = SyncStatusEmbed(**get_sync_status(db, connection_id, app_user_id))
    return SeriesBrowseResponse(
        items=[cached_series_to_dto(row, connection.provider_type) for row in rows],
        page=page,
        limit=resolved_limit,
        total=total,
        sync=sync,
    )


@router.get("/connections/{connection_id}/series/{series_id}", response_model=Series)
def get_connection_series_detail(
    connection_id: str,
    series_id: str,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> Series:
    connection = _get_connection_or_404(db, connection_id)
    row = _get_cached_series_in_scope(db, connection_id, series_id, app_user_id)
    return cached_series_to_dto(row, connection.provider_type)


@router.get("/connections/{connection_id}/series/{series_id}/artwork")
async def get_series_artwork(
    connection_id: str,
    series_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> Response:
    connection = _get_connection_or_404(db, connection_id)
    row = _get_cached_series_in_scope(db, connection_id, series_id, app_user_id)
    cache_path = artwork_cache_path(
        settings.WOF_ARTWORK_CACHE_DIR,
        app_user_id,
        connection_id,
        series_id,
    )
    cached = read_cached_artwork(
        cache_path,
        ttl_days=settings.WOF_ARTWORK_CACHE_TTL_DAYS,
    )
    if cached is not None:
        content, media_type = cached
        return Response(content=content, media_type=media_type)

    if (
        resolve_series_artwork_fetch_path(
            provider_type=connection.provider_type,  # type: ignore[arg-type]
            thumb_url=row.thumb_url,
            native_id=row.native_id,
        )
        is None
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork not available")

    provider = build_provider_for_user(
        db, vault, connection, app_user_id, settings=settings
    )
    if not isinstance(provider, (PlexProvider, JellyfinProvider)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "unsupported_provider",
                "message": "Artwork is not available for this server type",
            },
        )

    cached_now = await download_and_cache_artwork(
        provider,
        cache_dir=settings.WOF_ARTWORK_CACHE_DIR,
        app_user_id=app_user_id,
        connection_id=connection_id,
        series_id=series_id,
        thumb_url=row.thumb_url,
        provider_type=connection.provider_type,  # type: ignore[arg-type]
        native_id=row.native_id,
    )
    if not cached_now:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork not available")

    cached = read_cached_artwork(cache_path)
    if cached is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork not available")
    content, media_type = cached
    return Response(content=content, media_type=media_type)


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
    return SyncStatusResponse(**get_sync_status(db, connection_id, app_user_id))


@router.get("/connections/{connection_id}/sync/status", response_model=SyncStatusResponse)
def get_connection_sync_status(
    connection_id: str,
    db: Session = Depends(get_db),
    app_user_id: str = Depends(get_app_user_id),
) -> SyncStatusResponse:
    _get_connection_or_404(db, connection_id)
    return SyncStatusResponse(**get_sync_status(db, connection_id, app_user_id))


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
    _get_cached_series_in_scope(db, connection_id, series_id, app_user_id)
    rating_key, library_native_id = _cached_series_context(db, series_id, app_user_id)
    provider = build_provider_for_user(
        db, vault, connection, app_user_id, settings=settings
    )
    try:
        episodes = await _list_episodes(
            provider,
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
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
    _get_cached_series_in_scope(db, connection_id, series_id, app_user_id)
    rating_key, library_native_id = _cached_series_context(db, series_id, app_user_id)
    provider = build_provider_for_user(
        db, vault, connection, app_user_id, settings=settings
    )
    try:
        episodes, on_deck = await _fetch_resume_data(
            provider,
            series_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
    except ProviderError as err:
        raise _provider_error_to_http(err) from err
    cursor = _resume_cursor(series_id, episodes, on_deck)
    return ResumePreviewResponse.from_cursor(cursor)


@router.post(
    "/connections/{connection_id}/watch-state",
    response_model=WatchStateMutationResponse,
)
async def post_connection_watch_state(
    connection_id: str,
    body: WatchStateMutationRequest,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> WatchStateMutationResponse:
    connection = _get_connection_or_404(db, connection_id)
    try:
        target_connection_id, _, _ = parse_composite_id(body.target_id)
    except ValueError:
        return _watch_state_error_response(
            scope=body.scope,
            target_id=body.target_id,
            error_code="not_found",
            message="Mutation target id is invalid",
        )
    if target_connection_id != connection_id:
        return _watch_state_error_response(
            scope=body.scope,
            target_id=body.target_id,
            error_code="forbidden",
            message="Mutation target is outside this connection scope",
        )

    try:
        provider = build_provider_for_user(
            db, vault, connection, app_user_id, settings=settings
        )
    except HTTPException as err:
        if isinstance(err.detail, dict) and err.detail.get("code") == "unauthorized":
            return _watch_state_error_response(
                scope=body.scope,
                target_id=body.target_id,
                error_code="auth",
                message="Provider session is not authorized",
            )
        raise

    request = body.model_dump()
    try:
        await provider.mutate_watch_state(
            request=WatchMutationRequest.from_values(
                target_id=request["target_id"],
                scope=request["scope"],
                action=request["action"],
            )
        )
    except ProviderUnauthorized:
        return _watch_state_error_response(
            scope=body.scope,
            target_id=body.target_id,
            error_code="auth",
            message="Provider session is not authorized",
        )
    except ProviderNotFound:
        return _watch_state_error_response(
            scope=body.scope,
            target_id=body.target_id,
            error_code="not_found",
            message="Mutation target was not found by provider",
        )
    except ProviderError:
        return _watch_state_error_response(
            scope=body.scope,
            target_id=body.target_id,
            error_code="provider_error",
            message="Provider rejected watch mutation request",
        )

    return WatchStateMutationResponse(
        status="succeeded",
        scope=body.scope,
        updated_count=1,
        failed_count=0,
        failed_ids=[],
        error_code=None,
        message="Watch state updated",
    )
