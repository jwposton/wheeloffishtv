"""Centralized prune-state mutations: evidence, reset, recovery, auto-prune, audit."""
from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.playlist import Playlist
from wheeloffish.db.models.playlist_prune_event import PlaylistPruneEvent
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow
from wheeloffish.domain.ids import parse_composite_id

logger = structlog.get_logger(__name__)

PRUNE_THRESHOLD = 3
MAX_AUDIT_EVENTS_PER_PLAYLIST = 50


def _now() -> datetime:
    return datetime.now(UTC)


def _connection_id_for_row(row: PlaylistSeriesRow) -> str | None:
    try:
        return parse_composite_id(row.series_id)[0]
    except ValueError:
        return None


def _cached_series_ids(
    db: Session, connection_id: str, app_user_id: str
) -> set[str]:
    rows = (
        db.query(CachedSeries.id)
        .filter(
            CachedSeries.connection_id == connection_id,
            CachedSeries.app_user_id == app_user_id,
        )
        .all()
    )
    return {row[0] for row in rows}


def _rows_for_connection(
    db: Session, connection_id: str, app_user_id: str
) -> list[PlaylistSeriesRow]:
    rows = (
        db.query(PlaylistSeriesRow)
        .join(Playlist, PlaylistSeriesRow.playlist_id == Playlist.id)
        .filter(Playlist.app_user_id == app_user_id)
        .all()
    )
    return [
        row
        for row in rows
        if _connection_id_for_row(row) == connection_id
    ]


def record_catalog_sync_absence(
    db: Session, connection_id: str, app_user_id: str
) -> int:
    """Increment absence for playlist rows whose series is absent from cache."""
    cached_ids = _cached_series_ids(db, connection_id, app_user_id)
    now = _now()
    incremented = 0

    for row in _rows_for_connection(db, connection_id, app_user_id):
        if row.series_id in cached_ids:
            continue
        row.absence_count += 1
        row.last_absence_at = now
        row.last_evidence_source = "catalog_sync"
        if row.first_absence_at is None:
            row.first_absence_at = now
        incremented += 1

    db.flush()
    return incremented


def record_rebuild_row_absence(
    db: Session, row: PlaylistSeriesRow, *, source: str = "rebuild"
) -> None:
    """Increment absence for a single row (rebuild evidence)."""
    now = _now()
    row.absence_count += 1
    row.last_absence_at = now
    row.last_evidence_source = source
    if row.first_absence_at is None:
        row.first_absence_at = now
    db.flush()


def clear_prune_state_for_recovered(
    db: Session, connection_id: str, app_user_id: str
) -> None:
    """Clear prune state for rows whose series is back in CachedSeries."""
    cached_ids = _cached_series_ids(db, connection_id, app_user_id)

    for row in _rows_for_connection(db, connection_id, app_user_id):
        if row.absence_count <= 0 or row.series_id not in cached_ids:
            continue
        row.absence_count = 0
        row.first_absence_at = None
        row.last_absence_at = None
        row.last_evidence_source = None

    db.flush()


def reset_absence_counters_for_connection(
    db: Session, connection_id: str, app_user_id: str
) -> None:
    """Reset all prune counters on a connection after failed/partial sync."""
    for row in _rows_for_connection(db, connection_id, app_user_id):
        row.absence_count = 0
        row.first_absence_at = None
        row.last_absence_at = None
        row.last_evidence_source = None

    db.flush()


def write_prune_event(
    db: Session,
    playlist_id: str,
    series_id: str,
    event_type: str,
    reason: str,
    metadata: dict | None = None,
) -> None:
    """Append a material prune audit event with per-playlist retention."""
    db.add(
        PlaylistPruneEvent(
            playlist_id=playlist_id,
            series_id=series_id,
            event_type=event_type,
            reason=reason,
            event_metadata=metadata,
            timestamp=_now(),
        )
    )
    db.flush()

    events = (
        db.query(PlaylistPruneEvent)
        .filter(PlaylistPruneEvent.playlist_id == playlist_id)
        .order_by(PlaylistPruneEvent.timestamp.desc())
        .all()
    )
    if len(events) > MAX_AUDIT_EVENTS_PER_PLAYLIST:
        for event in events[MAX_AUDIT_EVENTS_PER_PLAYLIST:]:
            db.delete(event)
        db.flush()

    logger.info(
        "prune_event",
        playlist_id=playlist_id,
        series_id=series_id,
        event_type=event_type,
        reason=reason,
    )


def execute_auto_prune(
    db: Session,
    *,
    app_user_id: str,
    trigger: str,
    playlist_id: str | None = None,
    connection_id: str | None = None,
) -> list[str]:
    """Delete rows at or above PRUNE_THRESHOLD; write auto_pruned audit events."""
    query = (
        db.query(PlaylistSeriesRow)
        .join(Playlist, PlaylistSeriesRow.playlist_id == Playlist.id)
        .filter(
            Playlist.app_user_id == app_user_id,
            PlaylistSeriesRow.absence_count >= PRUNE_THRESHOLD,
        )
    )
    if playlist_id is not None:
        query = query.filter(PlaylistSeriesRow.playlist_id == playlist_id)

    rows = query.all()
    if connection_id is not None and playlist_id is None:
        rows = [
            row
            for row in rows
            if _connection_id_for_row(row) == connection_id
        ]

    deleted: list[str] = []
    for row in rows:
        series_id = row.series_id
        pl_id = row.playlist_id
        absence_count = row.absence_count
        write_prune_event(
            db,
            pl_id,
            series_id,
            event_type="auto_pruned",
            reason=trigger,
            metadata={"absence_count": absence_count, "trigger": trigger},
        )
        db.delete(row)
        deleted.append(series_id)

    db.flush()
    return deleted
