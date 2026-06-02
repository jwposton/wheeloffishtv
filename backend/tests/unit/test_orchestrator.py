"""Failure isolation unit tests for rebuild_playlist and nightly batch (D-11–D-17)."""
from __future__ import annotations

import uuid
import zoneinfo
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.core.orchestrator import prune_rebuild_history, rebuild_playlist, run_nightly_batch
from wheeloffish.core.playlist.rebuild_inputs import FetchResult
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.playlist_prune_event import PlaylistPruneEvent
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput
from wheeloffish.integrations.errors import ProviderError, ProviderNotFound

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

TEST_APP_USER_ID = "00000000-0000-4000-8000-000000000099"
TEST_APP_USER_ID_2 = "00000000-0000-4000-8000-000000000088"
TEST_CONNECTION_ID = "conn-aaaabbbb-1111-2222-3333-444455556666"
TEST_PROVIDER = "plex"
_ORCH = "wheeloffish.core.orchestrator"


def _ep(episode_id: str, season: int = 1, ep_index: int = 1) -> Episode:
    return Episode(
        id=episode_id,
        title=f"S{season}E{ep_index}",
        season_index=season,
        episode_index=ep_index,
        duration_ms=1_800_000,
        percent_watched=0.0,
    )


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


def _seed_user_media_link(
    db, connection_id: str = TEST_CONNECTION_ID, *, app_user_id: str = TEST_APP_USER_ID
) -> UserMediaLink:
    link = UserMediaLink(
        id=str(uuid.uuid4()),
        app_user_id=app_user_id,
        connection_id=connection_id,
        provider_user_id="plex-uid-test",
        linked_at=datetime.now(UTC),
    )
    db.add(link)
    db.flush()
    return link


def _seed_playlist(
    db,
    *,
    series_ids: list[str],
    cadence: str = "daily",
    dow: int | None = None,
    app_user_id: str = TEST_APP_USER_ID,
) -> PlaylistOrm:
    playlist_id = str(uuid.uuid4())
    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=app_user_id,
        name="Test Playlist",
        episode_count=4,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence=cadence,
        refresh_day_of_week=dow,
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


def _mock_provider() -> MagicMock:
    provider = MagicMock()
    provider.ping = AsyncMock(return_value=None)
    return provider


def _seed_cached_series(db, series_id: str) -> None:
    from wheeloffish.db.models.cached_series import CachedSeries
    from wheeloffish.domain.ids import parse_composite_id

    connection_id, _provider, native = parse_composite_id(series_id)
    db.add(
        CachedSeries(
            id=series_id,
            app_user_id=TEST_APP_USER_ID,
            connection_id=connection_id,
            library_native_id="1",
            native_id=native,
            title="Cached Show",
            synced_at=datetime.now(UTC),
        )
    )
    db.flush()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_not_found_fetch_result(db_session):
    """ProviderNotFound from list_episodes → FetchResult reason not_found (D-02)."""
    from wheeloffish.core.playlist.rebuild_inputs import fetch_rebuild_inputs_for_row

    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid = _series_id("show-not-found")
    _seed_cached_series(db_session, sid)
    db_session.commit()

    provider = MagicMock()
    provider.list_episodes = AsyncMock(side_effect=ProviderNotFound("Plex API error: 404"))
    provider.get_on_deck_episode = AsyncMock(return_value=None)

    result = await fetch_rebuild_inputs_for_row(
        db_session, TEST_APP_USER_ID, TEST_CONNECTION_ID, sid, provider
    )
    assert result.reason == "not_found"
    assert result.input is None


@pytest.mark.asyncio
async def test_fetch_failure_fetch_result(db_session):
    """Generic ProviderError → FetchResult reason fetch_failure."""
    from wheeloffish.core.playlist.rebuild_inputs import fetch_rebuild_inputs_for_row

    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid = _series_id("show-fetch-fail")
    _seed_cached_series(db_session, sid)
    db_session.commit()

    provider = MagicMock()
    provider.list_episodes = AsyncMock(side_effect=ProviderError("provider down"))
    provider.get_on_deck_episode = AsyncMock(return_value=None)

    result = await fetch_rebuild_inputs_for_row(
        db_session, TEST_APP_USER_ID, TEST_CONNECTION_ID, sid, provider
    )
    assert result.reason == "fetch_failure"
    assert result.input is None


@pytest.mark.asyncio
async def test_row_skip_on_fetch_failure(db_session):
    """One row fetch returns None → status partial; snapshot has episodes from good rows (D-11)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-alpha")
    sid_b = _series_id("show-beta")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid_a,
        episodes=[_ep("alpha-s1e1"), _ep("alpha-s1e2"), _ep("alpha-s1e3")],
    )

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        if series_id == sid_a:
            return FetchResult(good_input, "ok")
        return FetchResult(None, "fetch_failure")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    assert run.status == "partial"
    assert run.snapshot_json is not None
    assert len(run.snapshot_json) > 0
    assert all(ep["series_id"] == sid_a for ep in run.snapshot_json)
    fetch_warnings = run.row_outcomes_json["fetch_warnings"]
    assert any(w["series_id"] == sid_b and w["reason"] == "fetch_failure" for w in fetch_warnings)


@pytest.mark.asyncio
async def test_all_excluded_marks_failed(db_session):
    """All rows empty or skipped → status failed; prior snapshot_json unchanged (D-12, D-17)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-gamma")
    sid_b = _series_id("show-delta")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])

    # Seed a prior successful run so D-17 can be verified
    prior_snapshot = [
        {
            "episode_id": "prior-ep1",
            "series_id": sid_a,
            "slot_index": 0,
            "row_mode": "ordered",
            "title": "Old",
        }
    ]
    prior_run = RebuildRun(
        playlist_id=pl.id,
        status="succeeded",
        rebuild_seed="prior-seed",
        snapshot_json=prior_snapshot,
        row_outcomes_json={"outcomes": [], "fetch_warnings": []},
        slots_requested=4,
        slots_filled=1,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
    )
    db_session.add(prior_run)
    db_session.commit()

    async def _mock_fetch_all_fail(db, app_user_id, connection_id, series_id, provider):
        return FetchResult(None, "fetch_failure")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch_all_fail),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    assert run.status == "failed"
    assert run.snapshot_json is None  # failed run has no snapshot (D-17)

    # Prior run's snapshot must be preserved
    db_session.refresh(prior_run)
    assert prior_run.snapshot_json == prior_snapshot


@pytest.mark.asyncio
async def test_empty_snapshot_row_warning(db_session):
    """Row with episodes=[] excluded with empty_snapshot in outcomes (D-14, CR-01)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-epsilon")
    sid_b = _series_id("show-zeta")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid_a,
        episodes=[_ep("ep1"), _ep("ep2"), _ep("ep3")],
    )
    empty_input = SeriesRebuildInput(series_id=sid_b, episodes=[])

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        if series_id == sid_a:
            return FetchResult(good_input, "ok")
        return FetchResult(empty_input, "empty_snapshot")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    # Should have episodes from series_a
    assert run.snapshot_json is not None
    fetch_warnings = run.row_outcomes_json["fetch_warnings"]
    assert any(
        w["series_id"] == sid_b and w["reason"] == "empty_snapshot" for w in fetch_warnings
    ), f"Expected empty_snapshot warning for {sid_b} in {fetch_warnings}"


def _row_for_series(db, playlist_id: str, series_id: str) -> PlaylistSeriesRowOrm:
    return (
        db.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == playlist_id,
            PlaylistSeriesRowOrm.series_id == series_id,
        )
        .one()
    )


@pytest.mark.asyncio
async def test_not_found_increments(db_session):
    """Reachable provider + not_found row increments absence_count (D-02)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-found")
    sid_b = _series_id("show-gone")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid_a,
        episodes=[_ep("a1"), _ep("a2"), _ep("a3")],
    )

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        if series_id == sid_a:
            return FetchResult(good_input, "ok")
        return FetchResult(None, "not_found")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        await rebuild_playlist(db_session, pl.id, trigger="test")

    row_b = _row_for_series(db_session, pl.id, sid_b)
    assert row_b.absence_count == 1
    assert row_b.last_evidence_source == "rebuild"


@pytest.mark.asyncio
async def test_no_increment_when_unreachable(db_session):
    """Unreachable provider → not_found does not increment absence_count (D-04)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid = _series_id("show-unreachable")
    pl = _seed_playlist(db_session, series_ids=[sid])
    db_session.commit()

    provider = _mock_provider()
    provider.ping = AsyncMock(side_effect=ConnectionError("down"))

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        return FetchResult(None, "not_found")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=provider),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        await rebuild_playlist(db_session, pl.id, trigger="test")

    row = _row_for_series(db_session, pl.id, sid)
    assert row.absence_count == 0


@pytest.mark.asyncio
async def test_fetch_failure_no_increment(db_session):
    """fetch_failure does not increment absence_count (T-10-06)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-ok")
    sid_b = _series_id("show-fail")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid_a,
        episodes=[_ep("ok1"), _ep("ok2"), _ep("ok3")],
    )

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        if series_id == sid_a:
            return FetchResult(good_input, "ok")
        return FetchResult(None, "fetch_failure")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        await rebuild_playlist(db_session, pl.id, trigger="test")

    row_b = _row_for_series(db_session, pl.id, sid_b)
    assert row_b.absence_count == 0


@pytest.mark.asyncio
async def test_rebuild_recovery_clears_counter(db_session):
    """Successful fetch clears prior absence_count on the row (D-11)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid = _series_id("show-recover")
    pl = _seed_playlist(db_session, series_ids=[sid])
    row = _row_for_series(db_session, pl.id, sid)
    row.absence_count = 2
    row.last_evidence_source = "rebuild"
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid,
        episodes=[_ep("r1"), _ep("r2"), _ep("r3")],
    )

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        return FetchResult(good_input, "ok")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        await rebuild_playlist(db_session, pl.id, trigger="test")

    db_session.refresh(row)
    assert row.absence_count == 0
    assert row.last_evidence_source is None


@pytest.mark.asyncio
async def test_rebuild_auto_prune_at_threshold(db_session):
    """Succeeded rebuild auto-prunes at-threshold rows for this playlist only (D-06)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-keep")
    sid_b = _series_id("show-prune")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    row_b = _row_for_series(db_session, pl.id, sid_b)
    row_b.absence_count = 3
    db_session.commit()

    input_a = SeriesRebuildInput(
        series_id=sid_a,
        episodes=[_ep("k1"), _ep("k2"), _ep("k3")],
    )
    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        if series_id == sid_a:
            return FetchResult(input_a, "ok")
        # fetch_failure: no recovery clear; row stays at threshold for auto-prune
        return FetchResult(None, "fetch_failure")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    assert run.status in ("succeeded", "partial")
    remaining = (
        db_session.query(PlaylistSeriesRowOrm)
        .filter(PlaylistSeriesRowOrm.playlist_id == pl.id)
        .all()
    )
    assert len(remaining) == 1
    assert remaining[0].series_id == sid_a
    events = (
        db_session.query(PlaylistPruneEvent)
        .filter(
            PlaylistPruneEvent.playlist_id == pl.id,
            PlaylistPruneEvent.event_type == "auto_pruned",
        )
        .all()
    )
    assert len(events) == 1
    assert events[0].series_id == sid_b


@pytest.mark.asyncio
async def test_failed_rebuild_no_auto_prune(db_session):
    """Failed rebuild does not auto-prune at-threshold rows."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    sid_a = _series_id("show-fail-a")
    sid_b = _series_id("show-fail-b")
    pl = _seed_playlist(db_session, series_ids=[sid_a, sid_b])
    row_b = _row_for_series(db_session, pl.id, sid_b)
    row_b.absence_count = 3
    db_session.commit()

    async def _mock_fetch_all_fail(db, app_user_id, connection_id, series_id, provider):
        return FetchResult(None, "fetch_failure")

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch_all_fail),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    assert run.status == "failed"
    db_session.refresh(row_b)
    assert row_b.absence_count == 3
    events = (
        db_session.query(PlaylistPruneEvent)
        .filter(PlaylistPruneEvent.playlist_id == pl.id)
        .all()
    )
    assert events == []


def test_prune_keeps_last_three_runs(db_session):
    """Insert 5 successful runs, prune leaves exactly 3 (D-16)."""
    _seed_app_user(db_session)
    playlist_id = str(uuid.uuid4())
    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=TEST_APP_USER_ID,
        name="Prune Test",
        episode_count=4,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(pl)
    db_session.flush()

    for i in range(5):
        run = RebuildRun(
            playlist_id=playlist_id,
            status="succeeded",
            rebuild_seed=f"seed-{i}",
            snapshot_json=[{"episode_id": f"ep-{i}"}],
            row_outcomes_json={"outcomes": [], "fetch_warnings": []},
            slots_requested=4,
            slots_filled=1,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        db_session.add(run)
    db_session.commit()

    prune_rebuild_history(db_session, playlist_id, keep=3)
    db_session.commit()

    remaining = (
        db_session.query(RebuildRun)
        .filter(
            RebuildRun.playlist_id == playlist_id,
            RebuildRun.snapshot_json.isnot(None),
        )
        .all()
    )
    assert len(remaining) == 3


@pytest.mark.asyncio
async def test_nightly_sync_before_rebuild_order(db_session):
    """run_chunked_sync is awaited before rebuild_playlist for due playlists (D-05)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid = _series_id("show-nightly-order")
    pl = _seed_playlist(db_session, series_ids=[sid], cadence="daily")
    db_session.commit()

    calls: list[str] = []

    async def _sync_side_effect(connection_id, app_user_id):
        calls.append("sync")

    async def _rebuild_side_effect(db, playlist_id, *, trigger):
        calls.append("rebuild")

    mock_settings = MagicMock()
    mock_settings.install_tz.return_value = zoneinfo.ZoneInfo("UTC")

    with (
        patch(f"{_ORCH}.SecretsVault", return_value=MagicMock()),
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(
            f"{_ORCH}.check_provider_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(f"{_ORCH}.run_chunked_sync", side_effect=_sync_side_effect),
        patch(f"{_ORCH}.rebuild_playlist", side_effect=_rebuild_side_effect),
    ):
        await run_nightly_batch(db_session, mock_settings)

    assert "sync" in calls
    assert "rebuild" in calls
    assert calls.index("sync") < calls.index("rebuild")


@pytest.mark.asyncio
async def test_nightly_unreachable_resets_counters(db_session):
    """Unreachable provider resets absence counters and skips sync (D-04)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid = _series_id("show-nightly-reset")
    pl = _seed_playlist(db_session, series_ids=[sid], cadence="daily")
    row = _row_for_series(db_session, pl.id, sid)
    row.absence_count = 2
    db_session.commit()

    mock_sync = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.install_tz.return_value = zoneinfo.ZoneInfo("UTC")

    with (
        patch(f"{_ORCH}.SecretsVault", return_value=MagicMock()),
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(
            f"{_ORCH}.check_provider_reachable",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ORCH}.run_chunked_sync", mock_sync),
    ):
        await run_nightly_batch(db_session, mock_settings)

    db_session.refresh(row)
    assert row.absence_count == 0
    mock_sync.assert_not_awaited()
    failed_runs = (
        db_session.query(RebuildRun)
        .filter(RebuildRun.playlist_id == pl.id, RebuildRun.status == "failed")
        .all()
    )
    assert len(failed_runs) == 1
    assert failed_runs[0].error_message == "Provider unreachable — nightly batch aborted"


@pytest.mark.asyncio
async def test_nightly_skips_non_due_weekly(db_session):
    """Weekly playlist not due today is excluded from the nightly rebuild loop (D-03)."""
    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid_a = _series_id("show-weekly")
    # Use a DOW guaranteed not to be today
    today_dow = datetime.now(UTC).weekday()
    non_due_dow = (today_dow + 3) % 7

    pl = _seed_playlist(
        db_session,
        series_ids=[sid_a],
        cadence="weekly",
        dow=non_due_dow,
    )
    db_session.commit()

    mock_settings = MagicMock()
    mock_settings.install_tz.return_value = zoneinfo.ZoneInfo("UTC")

    mock_vault = MagicMock()
    with (
        patch(f"{_ORCH}.SecretsVault", return_value=mock_vault),
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(
            f"{_ORCH}.check_provider_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(f"{_ORCH}.run_chunked_sync", new_callable=AsyncMock),
        patch(f"{_ORCH}.rebuild_playlist", new_callable=AsyncMock),
    ):
        await run_nightly_batch(db_session, mock_settings)

    runs = (
        db_session.query(RebuildRun).filter(RebuildRun.playlist_id == pl.id).all()
    )
    assert runs == [], f"Weekly playlist not due today should not have a rebuild run, got: {runs}"


@pytest.mark.asyncio
async def test_nightly_expire_all_prevents_stale_absence_overwrite(db_session):
    """expire_all after sync prevents rebuild from clobbering sync-written absence counts."""
    from wheeloffish.core.catalog_prune import record_rebuild_row_absence
    from wheeloffish.db.session import get_session_factory

    _seed_app_user(db_session)
    _seed_connection(db_session)
    _seed_user_media_link(db_session)
    sid = _series_id("show-stale-session")
    pl = _seed_playlist(db_session, series_ids=[sid], cadence="daily")
    row = _row_for_series(db_session, pl.id, sid)
    row.absence_count = 0
    db_session.commit()

    async def _sync_side_effect(connection_id, app_user_id):
        other = get_session_factory()()
        try:
            other_row = (
                other.query(PlaylistSeriesRowOrm)
                .filter(
                    PlaylistSeriesRowOrm.playlist_id == pl.id,
                    PlaylistSeriesRowOrm.series_id == sid,
                )
                .one()
            )
            other_row.absence_count = 2
            other.commit()
        finally:
            other.close()

    async def _rebuild_side_effect(db, playlist_id, *, trigger):
        playlist_orm = (
            db.query(PlaylistOrm).filter(PlaylistOrm.id == playlist_id).one()
        )
        record_rebuild_row_absence(db, playlist_orm.rows[0])
        db.commit()

    mock_settings = MagicMock()
    mock_settings.install_tz.return_value = zoneinfo.ZoneInfo("UTC")

    with (
        patch(f"{_ORCH}.SecretsVault", return_value=MagicMock()),
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(
            f"{_ORCH}.check_provider_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(f"{_ORCH}.run_chunked_sync", side_effect=_sync_side_effect),
        patch(f"{_ORCH}.rebuild_playlist", side_effect=_rebuild_side_effect),
    ):
        await run_nightly_batch(db_session, mock_settings)

    db_session.expire_all()
    assert _row_for_series(db_session, pl.id, sid).absence_count == 3


@pytest.mark.asyncio
async def test_nightly_sync_per_app_user(db_session):
    """Due playlists grouped by (connection, app_user); sync runs per owner (D-04/D-05)."""
    _seed_app_user(db_session)
    user2 = AppUser(
        id=TEST_APP_USER_ID_2,
        provider_user_id="plex-uid-test-2",
    )
    db_session.add(user2)
    _seed_connection(db_session)
    _seed_user_media_link(db_session, app_user_id=TEST_APP_USER_ID)
    _seed_user_media_link(db_session, app_user_id=TEST_APP_USER_ID_2)
    sid_a = _series_id("show-user-a")
    sid_b = _series_id("show-user-b")
    pl_a = _seed_playlist(
        db_session, series_ids=[sid_a], cadence="daily", app_user_id=TEST_APP_USER_ID
    )
    pl_b = _seed_playlist(
        db_session, series_ids=[sid_b], cadence="daily", app_user_id=TEST_APP_USER_ID_2
    )
    db_session.commit()

    sync_calls: list[tuple[str, str]] = []

    async def _sync_side_effect(connection_id, app_user_id):
        sync_calls.append((connection_id, app_user_id))

    mock_settings = MagicMock()
    mock_settings.install_tz.return_value = zoneinfo.ZoneInfo("UTC")

    with (
        patch(f"{_ORCH}.SecretsVault", return_value=MagicMock()),
        patch(f"{_ORCH}.build_provider_for_user", return_value=_mock_provider()),
        patch(
            f"{_ORCH}.check_provider_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(f"{_ORCH}.run_chunked_sync", side_effect=_sync_side_effect),
        patch(f"{_ORCH}.rebuild_playlist", new_callable=AsyncMock),
    ):
        await run_nightly_batch(db_session, mock_settings)

    assert (TEST_CONNECTION_ID, TEST_APP_USER_ID) in sync_calls
    assert (TEST_CONNECTION_ID, TEST_APP_USER_ID_2) in sync_calls
    assert len(sync_calls) == 2
