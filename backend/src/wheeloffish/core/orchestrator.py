"""Playlist rebuild orchestrator — live fetch + builder wiring (Phase 05 Plan 03).

Decision map: D-06/D-08/D-11–D-17 (isolation, batch, snapshot, prune, status).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from wheeloffish.core.config import get_settings
from wheeloffish.core.connections import build_provider_for_user
from wheeloffish.core.playlist.builder import PlaylistBuilder
from wheeloffish.core.playlist.cadence import is_due, now_in_tz
from wheeloffish.core.playlist.mappers import orm_to_playlist
from wheeloffish.core.catalog_prune import (
    execute_auto_prune,
    record_rebuild_row_absence,
)
from wheeloffish.core.playlist.rebuild_inputs import (
    FetchResult,
    check_provider_reachable,
    fetch_rebuild_inputs_for_row,
)
from wheeloffish.core.provider_writeback import (
    WritebackResult,
    apply_writeback_result,
    push_snapshot,
)
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.db.session import get_session_factory
from wheeloffish.domain.ids import parse_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput

logger = structlog.get_logger("wheeloffish.orchestrator")


def prune_rebuild_history(db: Session, playlist_id: str, keep: int = 3) -> None:
    """Delete rebuild runs beyond the `keep` most recent with snapshot_json (D-16)."""
    runs_with_snapshot = (
        db.query(RebuildRun)
        .filter(
            RebuildRun.playlist_id == playlist_id,
            RebuildRun.snapshot_json.isnot(None),
        )
        .order_by(RebuildRun.finished_at.desc())
        .all()
    )
    if len(runs_with_snapshot) > keep:
        for run in runs_with_snapshot[keep:]:
            db.delete(run)
        db.flush()


async def rebuild_playlist(db: Session, playlist_id: str, *, trigger: str) -> RebuildRun:
    """Full rebuild pipeline for a single playlist (D-06, D-08, D-15, D-17).

    - Fetches live episode data per row (D-11 isolation)
    - Calls PlaylistBuilder.build() as the sole generation path
    - Persists snapshot on success/partial; error_message only on failure (D-17)
    - Prunes rebuild history to keep=3 snapshots (D-16)
    """
    settings = get_settings()
    vault = SecretsVault(db, settings)

    playlist_orm = (
        db.query(PlaylistOrm)
        .filter(PlaylistOrm.id == playlist_id)
        .one_or_none()
    )
    if playlist_orm is None:
        raise ValueError(f"Playlist {playlist_id!r} not found")

    run = RebuildRun(
        playlist_id=playlist_id,
        status="running",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()

    log = logger.bind(playlist_id=playlist_id, trigger=trigger, run_id=run.id)
    log.info("rebuild_started")

    app_user_id = playlist_orm.app_user_id

    connection_id: str | None = None
    if playlist_orm.rows:
        try:
            connection_id, _, _ = parse_composite_id(playlist_orm.rows[0].series_id)
        except ValueError:
            pass

    if connection_id is None:
        run.status = "failed"
        run.error_message = "Playlist has no rows or series IDs are malformed"
        run.finished_at = datetime.now(UTC)
        db.commit()
        return run

    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        run.status = "failed"
        run.error_message = f"Connection {connection_id!r} not found"
        run.finished_at = datetime.now(UTC)
        db.commit()
        return run

    try:
        provider = build_provider_for_user(db, vault, connection, app_user_id, settings=settings)
    except Exception as exc:
        run.status = "failed"
        run.error_message = f"Provider unavailable: {exc}"
        run.finished_at = datetime.now(UTC)
        db.commit()
        return run

    reachable = await check_provider_reachable(provider)
    domain_playlist = orm_to_playlist(playlist_orm)
    orm_rows_by_series = {r.series_id: r for r in playlist_orm.rows}
    valid_inputs: list[SeriesRebuildInput] = []
    fetch_warnings: list[dict] = []

    for row in domain_playlist.rows:
        result = await fetch_rebuild_inputs_for_row(
            db, app_user_id, connection_id, row.series_id, provider
        )
        orm_row = orm_rows_by_series[row.series_id]

        if result.reason == "fetch_failure":
            fetch_warnings.append({"series_id": row.series_id, "reason": "fetch_failure"})
            log.warning("row_fetch_failed", series_id=row.series_id)
        elif result.reason == "not_found":
            fetch_warnings.append({"series_id": row.series_id, "reason": "not_found"})
            log.warning("row_not_found", series_id=row.series_id)
            if reachable:
                record_rebuild_row_absence(db, orm_row)
        elif result.reason == "empty_snapshot":
            fetch_warnings.append({"series_id": row.series_id, "reason": "empty_snapshot"})
            log.warning("row_empty_snapshot", series_id=row.series_id)
            if reachable:
                record_rebuild_row_absence(db, orm_row)
        elif result.reason == "ok" and result.input is not None:
            valid_inputs.append(result.input)
            if orm_row.absence_count > 0:
                orm_row.absence_count = 0
                orm_row.first_absence_at = None
                orm_row.last_absence_at = None
                orm_row.last_evidence_source = None
        else:
            fetch_warnings.append({"series_id": row.series_id, "reason": "fetch_failure"})
            log.warning("row_fetch_unexpected", series_id=row.series_id, reason=result.reason)

    any_row_skipped = bool(fetch_warnings)
    all_rows_failed = any_row_skipped and not valid_inputs

    if all_rows_failed:
        run.status = "failed"
        run.error_message = "All series fetches failed — no episodes available"
        run.finished_at = datetime.now(UTC)
        db.commit()
        log.error("rebuild_all_rows_failed")
        return run

    rebuild_seed = str(uuid.uuid4())
    result = PlaylistBuilder.build(domain_playlist, valid_inputs, rebuild_seed=rebuild_seed)

    # D-12: all rows excluded by builder → failed (without wiping snapshot — D-17)
    all_excluded = all(o.excluded for o in result.row_outcomes)
    if all_excluded or not result.episodes:
        run.status = "failed"
        run.error_message = "No episodes in rebuild output — all rows excluded"
        run.finished_at = datetime.now(UTC)
        db.commit()
        log.warning("rebuild_zero_episodes")
        return run

    snapshot = [
        {
            "episode_id": be.episode.id,
            "title": be.episode.title,
            "series_id": be.series_id,
            "slot_index": be.slot_index,
            "row_mode": be.row_mode.value,
        }
        for be in result.episodes
    ]

    fetch_warning_by_series = {w["series_id"]: w["reason"] for w in fetch_warnings}
    row_outcomes = []
    for o in result.row_outcomes:
        outcome = o.model_dump(mode="json")
        if o.series_id in fetch_warning_by_series:
            outcome["fetch_warning"] = fetch_warning_by_series[o.series_id]
        row_outcomes.append(outcome)

    # D-15: persist snapshot + outcomes; D-17: only on success/partial
    run.status = "partial" if any_row_skipped else "succeeded"
    run.rebuild_seed = rebuild_seed
    run.snapshot_json = snapshot
    run.row_outcomes_json = {"outcomes": row_outcomes, "fetch_warnings": fetch_warnings}
    run.slots_requested = result.slots_requested
    run.slots_filled = result.slots_filled
    run.finished_at = datetime.now(UTC)
    db.commit()

    try:
        writeback_result = await push_snapshot(
            db, playlist_orm, run, snapshot, provider
        )
        db.refresh(run)
        apply_writeback_result(run, writeback_result)
    except Exception as exc:
        log.warning("writeback_failed", error=str(exc))
        db.refresh(run)
        apply_writeback_result(
            run,
            WritebackResult(status="failed", error=str(exc)),
        )
    db.commit()

    prune_rebuild_history(db, playlist_id, keep=3)
    db.commit()

    if run.status in ("succeeded", "partial"):
        try:
            execute_auto_prune(
                db,
                app_user_id=app_user_id,
                trigger="rebuild",
                playlist_id=playlist_id,
            )
            db.commit()
        except Exception as exc:
            log.warning("auto_prune_failed", error=str(exc))

    log.info("rebuild_complete", status=run.status, slots_filled=run.slots_filled)
    return run


async def run_nightly_batch(db: Session, settings) -> None:
    """Inner nightly rebuild logic — testable without session creation."""
    vault = SecretsVault(db, settings)
    now_local = now_in_tz(settings.install_tz())

    first_connection = db.query(Connection).order_by(Connection.created_at).first()
    if first_connection is None:
        logger.info("nightly_no_connections")
        return

    first_link = (
        db.query(UserMediaLink)
        .filter(UserMediaLink.connection_id == first_connection.id)
        .first()
    )
    if first_link is not None:
        try:
            probe_provider = build_provider_for_user(
                db, vault, first_connection, first_link.app_user_id, settings=settings
            )
            reachable = await check_provider_reachable(probe_provider)
        except Exception:
            reachable = False

        if not reachable:
            logger.error("nightly_provider_unreachable", connection_id=first_connection.id)
            due_playlists = [p for p in db.query(PlaylistOrm).all() if is_due(p, now_local)]
            for p in due_playlists:
                run = RebuildRun(
                    playlist_id=p.id,
                    status="failed",
                    error_message="Provider unreachable — nightly batch aborted",
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                )
                db.add(run)
            db.commit()
            return

    all_playlists = db.query(PlaylistOrm).all()
    due_playlists = [p for p in all_playlists if is_due(p, now_local)]
    logger.info("nightly_rebuild_start", due_count=len(due_playlists))

    for p in due_playlists:
        try:
            await rebuild_playlist(db, p.id, trigger="nightly")
        except Exception as exc:
            logger.error("nightly_rebuild_error", playlist_id=p.id, error=str(exc))


async def run_nightly_rebuilds() -> None:
    """Trigger nightly playlist rebuild for all due playlists (D-08, D-13).

    Called by APScheduler; creates its own DB session.
    """
    settings = get_settings()
    session_factory = get_session_factory(settings)
    db = session_factory()
    try:
        await run_nightly_batch(db, settings)
    finally:
        db.close()


async def run_manual_rebuild(db: Session, playlist_id: str, app_user_id: str) -> RebuildRun:
    """Trigger a manual rebuild; validates ownership (D-06, D-22)."""
    playlist_orm = (
        db.query(PlaylistOrm)
        .filter(PlaylistOrm.id == playlist_id, PlaylistOrm.app_user_id == app_user_id)
        .one_or_none()
    )
    if playlist_orm is None:
        raise ValueError(f"Playlist {playlist_id!r} not found or not owned by user")
    return await rebuild_playlist(db, playlist_id, trigger="manual")


def recover_interrupted_rebuilds(db: Session) -> None:
    """Reset any 'running' rebuild runs to failed on startup (from 05-02 plan)."""
    interrupted = (
        db.query(RebuildRun)
        .filter(RebuildRun.status == "running")
        .all()
    )
    if not interrupted:
        return
    now = datetime.now(UTC)
    for run in interrupted:
        run.status = "failed"
        run.error_message = "Interrupted by server restart"
        run.finished_at = now
    db.commit()
    logger.info("recovered_interrupted_rebuilds", count=len(interrupted))
