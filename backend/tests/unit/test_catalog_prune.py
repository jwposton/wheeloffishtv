"""Unit tests for catalog prune service (PRUNE-01/02/03)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from wheeloffish.core.catalog_prune import (
    MAX_AUDIT_EVENTS_PER_PLAYLIST,
    PRUNE_THRESHOLD,
    clear_prune_state_for_recovered,
    execute_auto_prune,
    record_catalog_sync_absence,
    reset_absence_counters_for_connection,
    write_prune_event,
)
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_prune_event import PlaylistPruneEvent
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.ids import format_composite_id

TEST_APP_USER_ID = "00000000-0000-4000-8000-000000000099"
TEST_CONNECTION_ID = "conn-aaaabbbb-1111-2222-3333-444455556666"
TEST_PROVIDER = "plex"


def _series_id(native_id: str) -> str:
    return format_composite_id(TEST_CONNECTION_ID, TEST_PROVIDER, native_id)


def _seed_app_user(db) -> AppUser:
    user = AppUser(
        id=TEST_APP_USER_ID,
        provider_user_id="plex-uid-test",
    )
    db.add(user)
    db.flush()
    return user


def _seed_connection(db) -> Connection:
    now = datetime.now(UTC)
    conn = Connection(
        id=TEST_CONNECTION_ID,
        provider_type=TEST_PROVIDER,
        display_name="Test Plex",
        base_url="https://plex.example.com",
        verify_ssl=True,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    db.add(conn)
    db.flush()
    return conn


def _seed_user_media_link(db) -> UserMediaLink:
    link = UserMediaLink(
        id=str(uuid.uuid4()),
        app_user_id=TEST_APP_USER_ID,
        connection_id=TEST_CONNECTION_ID,
        provider_user_id="plex-uid-test",
        linked_at=datetime.now(UTC),
    )
    db.add(link)
    db.flush()
    return link


def _seed_playlist(db, *, series_ids: list[str]) -> PlaylistOrm:
    playlist_id = str(uuid.uuid4())
    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=TEST_APP_USER_ID,
        name="Test Playlist",
        episode_count=4,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        refresh_day_of_week=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(pl)
    db.flush()
    for i, sid in enumerate(series_ids):
        row = PlaylistSeriesRowOrm(
            id=str(uuid.uuid4()),
            playlist_id=playlist_id,
            series_id=sid,
            mode="ordered",
            completion_policy="remove",
            completion_event="series_complete",
            sort_order=i,
        )
        db.add(row)
    db.flush()
    db.refresh(pl)
    return pl


def _row_for_series(db, playlist_id: str, series_id: str) -> PlaylistSeriesRowOrm:
    return (
        db.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == playlist_id,
            PlaylistSeriesRowOrm.series_id == series_id,
        )
        .one()
    )


def _seed_cached_series_for_user(
    db,
    series_id: str,
    *,
    app_user_id: str = TEST_APP_USER_ID,
) -> None:
    from wheeloffish.db.models.cached_series import CachedSeries
    from wheeloffish.domain.ids import parse_composite_id

    connection_id, _provider, native = parse_composite_id(series_id)
    db.add(
        CachedSeries(
            id=series_id,
            app_user_id=app_user_id,
            connection_id=connection_id,
            library_native_id="1",
            native_id=native,
            title="Cached Show",
            synced_at=datetime.now(UTC),
        )
    )
    db.flush()


def test_sub_threshold_no_prune(db_session):
    """Rows at absence_count 1 and 2 are not auto-pruned (PRUNE-01)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid_a = _series_id("show-a")
    sid_b = _series_id("show-b")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])

    row_a = _row_for_series(db_session, pl.id, sid_a)
    row_b = _row_for_series(db_session, pl.id, sid_b)
    row_a.absence_count = 1
    row_b.absence_count = 2
    db_session.flush()

    deleted = execute_auto_prune(
        db_session,
        app_user_id=TEST_APP_USER_ID,
        trigger="catalog_sync",
        playlist_id=pl.id,
    )

    assert deleted == []
    assert _row_for_series(db_session, pl.id, sid_a).absence_count == 1
    assert _row_for_series(db_session, pl.id, sid_b).absence_count == 2


def test_auto_prune_at_threshold(db_session):
    """Row at PRUNE_THRESHOLD is deleted with one auto_pruned audit event (PRUNE-02/03)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid = _series_id("gone-show")
    pl = _seed_playlist(db_session, series_ids=[sid])

    row = _row_for_series(db_session, pl.id, sid)
    row.absence_count = PRUNE_THRESHOLD
    db_session.flush()

    deleted = execute_auto_prune(
        db_session,
        app_user_id=TEST_APP_USER_ID,
        trigger="rebuild",
        playlist_id=pl.id,
    )

    assert deleted == [sid]
    assert (
        db_session.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == pl.id,
            PlaylistSeriesRowOrm.series_id == sid,
        )
        .count()
        == 0
    )
    events = (
        db_session.query(PlaylistPruneEvent)
        .filter(
            PlaylistPruneEvent.playlist_id == pl.id,
            PlaylistPruneEvent.series_id == sid,
            PlaylistPruneEvent.event_type == "auto_pruned",
        )
        .all()
    )
    assert len(events) == 1


def test_reset_on_failed_sync(db_session):
    """Failed sync resets all absence counters on the connection (D-04)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid_a = _series_id("show-a")
    sid_b = _series_id("show-b")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])

    row_a = _row_for_series(db_session, pl.id, sid_a)
    row_b = _row_for_series(db_session, pl.id, sid_b)
    row_a.absence_count = 2
    row_b.absence_count = 3
    db_session.flush()

    reset_absence_counters_for_connection(
        db_session, TEST_CONNECTION_ID, TEST_APP_USER_ID
    )

    assert _row_for_series(db_session, pl.id, sid_a).absence_count == 0
    assert _row_for_series(db_session, pl.id, sid_b).absence_count == 0


def test_clear_on_recovery(db_session):
    """Series back in cache clears prune state (D-11)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid = _series_id("recovered-show")
    pl = _seed_playlist(db_session, series_ids=[sid])
    _seed_cached_series_for_user(db_session, sid)

    row = _row_for_series(db_session, pl.id, sid)
    row.absence_count = 2
    row.first_absence_at = datetime.now(UTC)
    row.last_absence_at = datetime.now(UTC)
    row.last_evidence_source = "catalog_sync"
    db_session.flush()

    clear_prune_state_for_recovered(
        db_session, TEST_CONNECTION_ID, TEST_APP_USER_ID
    )

    refreshed = _row_for_series(db_session, pl.id, sid)
    assert refreshed.absence_count == 0
    assert refreshed.first_absence_at is None
    assert refreshed.last_absence_at is None
    assert refreshed.last_evidence_source is None


def test_audit_retention_50(db_session):
    """write_prune_event retains at most 50 events per playlist (D-18)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    pl = _seed_playlist(db_session, series_ids=[_series_id("audit-show")])

    for i in range(55):
        write_prune_event(
            db_session,
            pl.id,
            _series_id(f"series-{i}"),
            event_type="manual_removed",
            reason="operator",
            metadata={"index": i},
        )

    count = (
        db_session.query(PlaylistPruneEvent)
        .filter(PlaylistPruneEvent.playlist_id == pl.id)
        .count()
    )
    assert count == MAX_AUDIT_EVENTS_PER_PLAYLIST

    newest = (
        db_session.query(PlaylistPruneEvent)
        .filter(PlaylistPruneEvent.playlist_id == pl.id)
        .order_by(PlaylistPruneEvent.timestamp.desc())
        .first()
    )
    assert newest is not None
    assert newest.event_metadata == {"index": 54}


def test_record_catalog_sync_absence(db_session):
    """Absent series increments; cached series untouched (D-02/D-03)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid_absent = _series_id("absent-show")
    sid_cached = _series_id("cached-show")
    pl = _seed_playlist(db_session, series_ids=[sid_absent, sid_cached])
    _seed_cached_series_for_user(db_session, sid_cached)

    n1 = record_catalog_sync_absence(
        db_session, TEST_CONNECTION_ID, TEST_APP_USER_ID
    )
    assert n1 == 1

    absent_row = _row_for_series(db_session, pl.id, sid_absent)
    cached_row = _row_for_series(db_session, pl.id, sid_cached)
    assert absent_row.absence_count == 1
    assert absent_row.first_absence_at is not None
    assert absent_row.last_evidence_source == "catalog_sync"
    assert cached_row.absence_count == 0

    n2 = record_catalog_sync_absence(
        db_session, TEST_CONNECTION_ID, TEST_APP_USER_ID
    )
    assert n2 == 1
    assert _row_for_series(db_session, pl.id, sid_absent).absence_count == 2


def test_malformed_series_id_skipped_in_connection_filter(db_session):
    """Malformed series_id rows are skipped without aborting connection prune ops."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid_valid = _series_id("valid-show")
    pl = _seed_playlist(db_session, series_ids=[sid_valid])
    malformed = PlaylistSeriesRowOrm(
        id=str(uuid.uuid4()),
        playlist_id=pl.id,
        series_id="not-a-composite-id",
        mode="ordered",
        completion_policy="remove",
        completion_event="series_complete",
        sort_order=99,
    )
    db_session.add(malformed)
    db_session.flush()

    n = record_catalog_sync_absence(
        db_session, TEST_CONNECTION_ID, TEST_APP_USER_ID
    )
    assert n == 1
    assert _row_for_series(db_session, pl.id, sid_valid).absence_count == 1

    malformed.absence_count = PRUNE_THRESHOLD
    db_session.flush()

    deleted = execute_auto_prune(
        db_session,
        app_user_id=TEST_APP_USER_ID,
        trigger="catalog_sync",
        connection_id=TEST_CONNECTION_ID,
    )
    assert deleted == []
    assert (
        db_session.query(PlaylistSeriesRowOrm)
        .filter(PlaylistSeriesRowOrm.id == malformed.id)
        .count()
        == 1
    )
