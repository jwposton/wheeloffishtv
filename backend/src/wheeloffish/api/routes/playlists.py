"""Playlist CRUD + rebuild REST API (Phase 05 Plan 04).

Decision map: D-04/D-06/D-16/D-18/D-21/D-22 ownership, defaults, manual rebuild, history.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_current_user, get_db
from wheeloffish.api.schemas.playlists import (
    AppendRowRequest,
    PatchRowRequest,
    PlaylistCreateRequest,
    PlaylistDetailResponse,
    PlaylistListItem,
    PlaylistSeriesRowResponse,
    PlaylistUpdateRequest,
    PruneEventResponse,
    RebuildRunSummary,
    SnapshotEpisode,
)
from wheeloffish.core.catalog_prune import write_prune_event
from wheeloffish.core.rebuild_diagnostics import (
    DiagnosticsContext,
    build_rebuild_diagnostics,
)
from wheeloffish.core.config import get_settings
from wheeloffish.core.connections import build_provider_for_user
from wheeloffish.core.media_artwork import series_artwork_url
from wheeloffish.core.orchestrator import run_manual_rebuild
from wheeloffish.core.provider_playlist_urls import provider_playlist_open_url
from wheeloffish.core.provider_writeback import delete_linked, rename_linked
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_prune_event import PlaylistPruneEvent
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.domain.ids import parse_composite_id

router = APIRouter(prefix="/playlists", tags=["playlists"])


def _connection_for_playlist(db: Session, playlist: PlaylistOrm) -> Connection | None:
    if not playlist.rows:
        return None
    try:
        connection_id, _, _ = parse_composite_id(playlist.rows[0].series_id)
    except ValueError:
        return None
    return db.query(Connection).filter(Connection.id == connection_id).one_or_none()


def _playlist_open_url(db: Session, playlist: PlaylistOrm) -> str | None:
    if not playlist.provider_playlist_id or not playlist.provider_kind:
        return None
    connection = _connection_for_playlist(db, playlist)
    if connection is None:
        return None
    return provider_playlist_open_url(
        base_url=connection.base_url,
        provider_kind=playlist.provider_kind,
        provider_playlist_id=playlist.provider_playlist_id,
        verify_ssl=connection.verify_ssl,
    )


async def _with_provider_for_playlist(
    db: Session,
    playlist: PlaylistOrm,
    app_user_id: str,
):
    connection = _connection_for_playlist(db, playlist)
    if connection is None:
        return None
    settings = get_settings()
    vault = SecretsVault(db, settings)
    return build_provider_for_user(db, vault, connection, app_user_id, settings=settings)


def _get_owned_playlist(db: Session, playlist_id: str, app_user_id: str) -> PlaylistOrm:
    """Return the playlist if found and owned by app_user_id, else raise 404 (D-18)."""
    playlist = (
        db.query(PlaylistOrm)
        .filter(
            PlaylistOrm.id == playlist_id,
            PlaylistOrm.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return playlist


def _latest_run(db: Session, playlist_id: str) -> RebuildRun | None:
    return (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist_id)
        .order_by(RebuildRun.started_at.desc())
        .first()
    )


def _rebuild_run_to_summary(run: RebuildRun) -> RebuildRunSummary:
    return RebuildRunSummary(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_message=run.error_message,
        slots_filled=run.slots_filled,
        slots_requested=run.slots_requested,
        writeback_status=run.writeback_status,
        writeback_error=run.writeback_error,
        writeback_warnings=run.writeback_warnings,
        writeback_at=run.writeback_at,
    )


def _series_row_metadata_map(
    db: Session,
    app_user_id: str,
    series_ids: list[str],
) -> dict[str, tuple[str | None, str | None]]:
    """Resolve series_id → (title, thumb_url) from owner-scoped CachedSeries."""
    if not series_ids:
        return {}
    rows = (
        db.query(CachedSeries.id, CachedSeries.title, CachedSeries.connection_id)
        .filter(
            CachedSeries.id.in_(series_ids),
            CachedSeries.app_user_id == app_user_id,
        )
        .all()
    )
    return {
        r.id: (r.title, series_artwork_url(r.connection_id, r.id))
        for r in rows
    }


def _series_title_map(db: Session, app_user_id: str, series_ids: list[str]) -> dict[str, str]:
    """Resolve series_id → title from CachedSeries where available."""
    return {
        series_id: title
        for series_id, (title, _thumb) in _series_row_metadata_map(
            db, app_user_id, series_ids
        ).items()
    }


def _playlist_to_detail(
    db: Session,
    playlist: PlaylistOrm,
    app_user_id: str,
) -> PlaylistDetailResponse:
    row_series_ids = [r.series_id for r in playlist.rows]
    metadata_map = _series_row_metadata_map(db, app_user_id, row_series_ids)

    rows_out = [
        PlaylistSeriesRowResponse(
            series_id=r.series_id,
            mode=r.mode,
            completion_policy=r.completion_policy,
            completion_event=r.completion_event,
            series_title=metadata_map.get(r.series_id, (None, None))[0],
            thumb_url=metadata_map.get(r.series_id, (None, None))[1],
        )
        for r in playlist.rows
    ]

    # Latest succeeded/partial run for snapshot (D-16)
    latest_good_run = (
        db.query(RebuildRun)
        .filter(
            RebuildRun.playlist_id == playlist.id,
            RebuildRun.status.in_(["succeeded", "partial"]),
            RebuildRun.snapshot_json.isnot(None),
        )
        .order_by(RebuildRun.finished_at.desc())
        .first()
    )

    snapshot_out: list[SnapshotEpisode] = []
    if latest_good_run and latest_good_run.snapshot_json:
        snapshot_series_ids = list({e["series_id"] for e in latest_good_run.snapshot_json})
        snap_title_map = _series_title_map(db, app_user_id, snapshot_series_ids)
        snapshot_out = [
            SnapshotEpisode(
                episode_id=e["episode_id"],
                title=e["title"],
                series_id=e["series_id"],
                series_title=snap_title_map.get(e["series_id"]),
                slot_index=e["slot_index"],
                row_mode=e["row_mode"],
            )
            for e in latest_good_run.snapshot_json
        ]

    provider_open_url = _playlist_open_url(db, playlist)

    # Most recent run (any status) for last_rebuild field (D-21)
    latest_run = _latest_run(db, playlist.id)
    last_rebuild = _rebuild_run_to_summary(latest_run) if latest_run else None
    if latest_run is not None:
        diag_series_ids = list(row_series_ids)
        for warning in (latest_run.row_outcomes_json or {}).get("fetch_warnings", []):
            if isinstance(warning, dict):
                sid = warning.get("series_id")
                if sid and sid not in diag_series_ids:
                    diag_series_ids.append(sid)
        episode_title_map: dict[str, str] = {}
        for entry in latest_run.snapshot_json or []:
            if isinstance(entry, dict):
                episode_id = entry.get("episode_id")
                title = entry.get("title")
                if episode_id and title:
                    episode_title_map[episode_id] = title
        for ep in snapshot_out:
            if ep.title and ep.episode_id not in episode_title_map:
                episode_title_map[ep.episode_id] = ep.title
        ctx = DiagnosticsContext(
            series_title_map=_series_title_map(db, app_user_id, diag_series_ids),
            episode_title_map=episode_title_map,
            provider_open_url=provider_open_url,
        )
        last_rebuild.diagnostics = build_rebuild_diagnostics(latest_run, ctx)

    # Last 3 runs (D-16)
    recent_runs_orm = (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist.id)
        .order_by(RebuildRun.started_at.desc())
        .limit(3)
        .all()
    )
    recent_runs = [_rebuild_run_to_summary(r) for r in recent_runs_orm]

    prune_events_orm = (
        db.query(PlaylistPruneEvent)
        .filter(PlaylistPruneEvent.playlist_id == playlist.id)
        .order_by(PlaylistPruneEvent.timestamp.desc())
        .limit(20)
        .all()
    )
    recent_prune_events = [
        PruneEventResponse(
            id=e.id,
            series_id=e.series_id,
            event_type=e.event_type,
            reason=e.reason,
            event_metadata=e.event_metadata,
            timestamp=e.timestamp,
        )
        for e in prune_events_orm
    ]

    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        episode_count=playlist.episode_count,
        slot_allocation=playlist.slot_allocation,
        default_completion_policy=playlist.default_completion_policy,
        refresh_cadence=playlist.refresh_cadence,
        refresh_day_of_week=playlist.refresh_day_of_week,
        rows=rows_out,
        current_snapshot=snapshot_out,
        last_rebuild=last_rebuild,
        recent_runs=recent_runs,
        recent_prune_events=recent_prune_events,
        provider_playlist_id=playlist.provider_playlist_id,
        provider_kind=playlist.provider_kind,
        provider_playlist_open_url=provider_open_url,
    )


@router.get("", response_model=list[PlaylistListItem])
def list_playlists(
    series_id: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[PlaylistListItem]:
    """List all playlists owned by the current user (D-18).

    When ``series_id`` is provided, return only playlists that include that series row.
    """
    query = db.query(PlaylistOrm).filter(PlaylistOrm.app_user_id == user.id)
    if series_id is not None:
        query = query.join(PlaylistSeriesRowOrm).filter(
            PlaylistSeriesRowOrm.series_id == series_id,
        )
    playlists = query.order_by(PlaylistOrm.created_at.desc()).distinct().all()
    result = []
    for pl in playlists:
        latest = _latest_run(db, pl.id)
        result.append(
            PlaylistListItem(
                id=pl.id,
                name=pl.name,
                refresh_cadence=pl.refresh_cadence,
                refresh_day_of_week=pl.refresh_day_of_week,
                last_rebuild_status=latest.status if latest else None,
                last_rebuild_at=latest.finished_at if latest else None,
                last_writeback_status=latest.writeback_status if latest else None,
                provider_playlist_id=pl.provider_playlist_id,
                provider_kind=pl.provider_kind,
                provider_playlist_open_url=_playlist_open_url(db, pl),
            )
        )
    return result


@router.post("", response_model=PlaylistDetailResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(
    body: PlaylistCreateRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Create a new playlist with rows. Defaults refresh_cadence=daily, episode_count=20 (D-04)."""
    playlist_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    playlist = PlaylistOrm(
        id=playlist_id,
        app_user_id=user.id,
        name=body.name,
        episode_count=body.episode_count,
        slot_allocation=body.slot_allocation.value,
        default_completion_policy=body.default_completion_policy.value,
        refresh_cadence=body.refresh_cadence,
        refresh_day_of_week=body.refresh_day_of_week,
        created_at=now,
        updated_at=now,
    )
    db.add(playlist)
    db.flush()

    for i, row_req in enumerate(body.rows):
        row = PlaylistSeriesRowOrm(
            id=str(uuid.uuid4()),
            playlist_id=playlist_id,
            series_id=row_req.series_id,
            mode=row_req.mode.value,
            completion_policy=row_req.completion_policy.value,
            completion_event=row_req.completion_event.value,
            sort_order=i,
        )
        db.add(row)

    db.commit()
    db.refresh(playlist)
    return _playlist_to_detail(db, playlist, user.id)


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
def get_playlist(
    playlist_id: str,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Get playlist detail with snapshot and recent runs (D-16, D-18)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    return _playlist_to_detail(db, playlist, user.id)


@router.put("/{playlist_id}", response_model=PlaylistDetailResponse)
async def update_playlist(
    playlist_id: str,
    body: PlaylistUpdateRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Update playlist config and/or rows (ownership-gated, D-18)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    previous_name = playlist.name

    if body.name is not None:
        playlist.name = body.name
    if body.episode_count is not None:
        playlist.episode_count = body.episode_count
    if body.slot_allocation is not None:
        playlist.slot_allocation = body.slot_allocation.value
    if body.default_completion_policy is not None:
        playlist.default_completion_policy = body.default_completion_policy.value
    if body.refresh_cadence is not None:
        playlist.refresh_cadence = body.refresh_cadence
    if body.refresh_day_of_week is not None or body.refresh_cadence == "daily":
        playlist.refresh_day_of_week = body.refresh_day_of_week

    if body.rows is not None:
        for existing_row in list(playlist.rows):
            db.delete(existing_row)
        db.flush()

        for i, row_req in enumerate(body.rows):
            row = PlaylistSeriesRowOrm(
                id=str(uuid.uuid4()),
                playlist_id=playlist_id,
                series_id=row_req.series_id,
                mode=row_req.mode.value,
                completion_policy=row_req.completion_policy.value,
                completion_event=row_req.completion_event.value,
                sort_order=i,
            )
            db.add(row)

    playlist.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(playlist)

    if (
        body.name is not None
        and body.name != previous_name
        and playlist.provider_playlist_id
    ):
        provider = await _with_provider_for_playlist(db, playlist, user.id)
        if provider is not None:
            await rename_linked(playlist, provider, db)

    return _playlist_to_detail(db, playlist, user.id)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> None:
    """Delete a playlist and cascade (ownership-gated, D-18)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    if playlist.provider_playlist_id:
        provider = await _with_provider_for_playlist(db, playlist, user.id)
        if provider is not None:
            await delete_linked(playlist, provider)
    db.delete(playlist)
    db.commit()


def _require_cached_series(db: Session, series_id: str, app_user_id: str) -> None:
    """Ensure series_id exists in the user's cached catalog before playlist mutation."""
    exists = (
        db.query(CachedSeries.id)
        .filter(
            CachedSeries.id == series_id,
            CachedSeries.app_user_id == app_user_id,
        )
        .one_or_none()
    )
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Series not found in catalog",
        )


def _get_playlist_row(
    db: Session,
    playlist_id: str,
    series_id: str,
) -> PlaylistSeriesRowOrm:
    row = (
        db.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == playlist_id,
            PlaylistSeriesRowOrm.series_id == series_id,
        )
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")
    return row


@router.post("/{playlist_id}/rows", response_model=PlaylistDetailResponse)
def append_playlist_row(
    playlist_id: str,
    body: AppendRowRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Append one series row without full PUT replacement (D-20)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    _require_cached_series(db, body.series_id, user.id)

    existing = (
        db.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == playlist_id,
            PlaylistSeriesRowOrm.series_id == body.series_id,
        )
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Row already exists")

    max_sort = max((r.sort_order for r in playlist.rows), default=-1)
    row = PlaylistSeriesRowOrm(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id,
        series_id=body.series_id,
        mode=body.mode.value,
        completion_policy=body.completion_policy.value,
        completion_event=body.completion_event.value,
        sort_order=max_sort + 1,
    )
    db.add(row)
    playlist.updated_at = datetime.now(UTC)
    try:
        db.commit()
        db.refresh(playlist)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Row already exists",
        ) from None
    return _playlist_to_detail(db, playlist, user.id)


@router.delete("/{playlist_id}/rows/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_playlist_row(
    playlist_id: str,
    series_id: str,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> None:
    """Remove one series row without full PUT replacement (D-20)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    row = _get_playlist_row(db, playlist_id, series_id)
    removed_series_id = row.series_id
    db.delete(row)
    write_prune_event(
        db,
        playlist_id,
        removed_series_id,
        event_type="manual_removed",
        reason="operator",
    )
    playlist.updated_at = datetime.now(UTC)
    db.commit()


@router.patch("/{playlist_id}/rows/{series_id}", response_model=PlaylistDetailResponse)
def patch_playlist_row(
    playlist_id: str,
    series_id: str,
    body: PatchRowRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Update mode/completion fields on one row (D-16 backend support)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    row = _get_playlist_row(db, playlist_id, series_id)

    if body.mode is not None:
        row.mode = body.mode.value
    if body.completion_policy is not None:
        row.completion_policy = body.completion_policy.value
    if body.completion_event is not None:
        row.completion_event = body.completion_event.value

    playlist.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(playlist)
    return _playlist_to_detail(db, playlist, user.id)


@router.post("/{playlist_id}/rebuild", response_model=RebuildRunSummary)
async def rebuild_playlist(
    playlist_id: str,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> RebuildRunSummary:
    """Trigger immediate manual rebuild for owner only (D-06, D-22)."""
    _get_owned_playlist(db, playlist_id, user.id)

    # 409 if already running (D-22)
    running = (
        db.query(RebuildRun)
        .filter(
            RebuildRun.playlist_id == playlist_id,
            RebuildRun.status == "running",
        )
        .first()
    )
    if running is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "rebuild_in_progress"},
        )

    try:
        run = await run_manual_rebuild(db, playlist_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _rebuild_run_to_summary(run)
