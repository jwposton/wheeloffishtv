"""Playlist CRUD + rebuild REST API (Phase 05 Plan 04).

Decision map: D-04/D-06/D-16/D-18/D-21/D-22 ownership, defaults, manual rebuild, history.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_current_user, get_db
from wheeloffish.api.schemas.playlists import (
    PlaylistCreateRequest,
    PlaylistDetailResponse,
    PlaylistListItem,
    PlaylistSeriesRowResponse,
    PlaylistUpdateRequest,
    RebuildRunSummary,
    SnapshotEpisode,
)
from wheeloffish.core.orchestrator import run_manual_rebuild
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.rebuild_run import RebuildRun

router = APIRouter(prefix="/playlists", tags=["playlists"])


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
    )


def _series_title_map(db: Session, app_user_id: str, series_ids: list[str]) -> dict[str, str]:
    """Resolve series_id → title from CachedSeries where available."""
    if not series_ids:
        return {}
    rows = (
        db.query(CachedSeries.id, CachedSeries.title)
        .filter(
            CachedSeries.id.in_(series_ids),
            CachedSeries.app_user_id == app_user_id,
        )
        .all()
    )
    return {r.id: r.title for r in rows}


def _playlist_to_detail(
    db: Session,
    playlist: PlaylistOrm,
    app_user_id: str,
) -> PlaylistDetailResponse:
    row_series_ids = [r.series_id for r in playlist.rows]
    title_map = _series_title_map(db, app_user_id, row_series_ids)

    rows_out = [
        PlaylistSeriesRowResponse(
            series_id=r.series_id,
            mode=r.mode,
            completion_policy=r.completion_policy,
            completion_event=r.completion_event,
            series_title=title_map.get(r.series_id),
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

    # Most recent run (any status) for last_rebuild field (D-21)
    latest_run = _latest_run(db, playlist.id)
    last_rebuild = _rebuild_run_to_summary(latest_run) if latest_run else None

    # Last 3 runs (D-16)
    recent_runs_orm = (
        db.query(RebuildRun)
        .filter(RebuildRun.playlist_id == playlist.id)
        .order_by(RebuildRun.started_at.desc())
        .limit(3)
        .all()
    )
    recent_runs = [_rebuild_run_to_summary(r) for r in recent_runs_orm]

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
    )


@router.get("", response_model=list[PlaylistListItem])
def list_playlists(
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[PlaylistListItem]:
    """List all playlists owned by the current user (D-18)."""
    playlists = (
        db.query(PlaylistOrm)
        .filter(PlaylistOrm.app_user_id == user.id)
        .order_by(PlaylistOrm.created_at.desc())
        .all()
    )
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
def update_playlist(
    playlist_id: str,
    body: PlaylistUpdateRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PlaylistDetailResponse:
    """Update playlist config and/or rows (ownership-gated, D-18)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)

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
    return _playlist_to_detail(db, playlist, user.id)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(
    playlist_id: str,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> None:
    """Delete a playlist and cascade (ownership-gated, D-18)."""
    playlist = _get_owned_playlist(db, playlist_id, user.id)
    db.delete(playlist)
    db.commit()


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
