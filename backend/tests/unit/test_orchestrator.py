"""Failure isolation unit tests for rebuild_playlist and nightly batch (D-11–D-17)."""
from __future__ import annotations

import uuid
import zoneinfo
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.core.orchestrator import prune_rebuild_history, rebuild_playlist, run_nightly_batch
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

TEST_APP_USER_ID = "00000000-0000-4000-8000-000000000099"
TEST_CONNECTION_ID = "conn-aaaabbbb-1111-2222-3333-444455556666"
TEST_PROVIDER = "plex"


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


def _seed_user_media_link(db, connection_id: str = TEST_CONNECTION_ID) -> UserMediaLink:
    link = UserMediaLink(
        id=str(uuid.uuid4()),
        app_user_id=TEST_APP_USER_ID,
        connection_id=connection_id,
        provider_user_id="plex-uid-test",
        linked_at=datetime.now(UTC),
    )
    db.add(link)
    db.flush()
    return link


def _seed_playlist(db, *, series_ids: list[str], cadence: str = "daily", dow: int | None = None) -> PlaylistOrm:
    playlist_id = str(uuid.uuid4())
    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=TEST_APP_USER_ID,
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


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
            return good_input
        return None  # sid_b fails

    with (
        patch("wheeloffish.core.orchestrator.build_provider_for_user", return_value=_mock_provider()),
        patch("wheeloffish.core.orchestrator.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
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
    prior_snapshot = [{"episode_id": "prior-ep1", "series_id": sid_a, "slot_index": 0, "row_mode": "ordered", "title": "Old"}]
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
        return None  # both rows fail

    with (
        patch("wheeloffish.core.orchestrator.build_provider_for_user", return_value=_mock_provider()),
        patch("wheeloffish.core.orchestrator.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch_all_fail),
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
        return good_input if series_id == sid_a else empty_input

    with (
        patch("wheeloffish.core.orchestrator.build_provider_for_user", return_value=_mock_provider()),
        patch("wheeloffish.core.orchestrator.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="test")

    # Should have episodes from series_a
    assert run.snapshot_json is not None
    fetch_warnings = run.row_outcomes_json["fetch_warnings"]
    assert any(
        w["series_id"] == sid_b and w["reason"] == "empty_snapshot" for w in fetch_warnings
    ), f"Expected empty_snapshot warning for {sid_b} in {fetch_warnings}"


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
        patch("wheeloffish.core.orchestrator.SecretsVault", return_value=mock_vault),
        patch("wheeloffish.core.orchestrator.build_provider_for_user", return_value=_mock_provider()),
        patch("wheeloffish.core.orchestrator.check_provider_reachable", new_callable=AsyncMock, return_value=True),
        patch("wheeloffish.core.orchestrator.fetch_rebuild_inputs_for_row", new_callable=AsyncMock),
    ):
        await run_nightly_batch(db_session, mock_settings)

    runs = (
        db_session.query(RebuildRun).filter(RebuildRun.playlist_id == pl.id).all()
    )
    assert runs == [], f"Weekly playlist not due today should not have a rebuild run, got: {runs}"
