"""Integration test: rebuild_playlist end-to-end with test DB + mocked provider.

Verifies that rebuild_playlist persists a valid snapshot with episode series_id
field when the provider returns fixture episodes (SCH-02 orchestration path).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.core.orchestrator import rebuild_playlist
from wheeloffish.core.playlist.rebuild_inputs import FetchResult
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput

_ORCH = "wheeloffish.core.orchestrator"

# Reuse stable IDs for e2e scenario
APP_USER_ID = "00000000-0000-4000-8000-000000000777"
CONNECTION_ID = "e2e-conn-aaaa-bbbb-cccc-ddddeeeeeeee"
PROVIDER = "plex"


def _series(native_id: str) -> str:
    return format_composite_id(CONNECTION_ID, PROVIDER, native_id)


def _episode(episode_id: str, season: int, ep_index: int, series_id: str) -> Episode:
    return Episode(
        id=episode_id,
        title=f"S{season}E{ep_index} - {series_id}",
        season_index=season,
        episode_index=ep_index,
        duration_ms=2_700_000,
        percent_watched=0.0,
    )


@pytest.fixture
def e2e_playlist(db_session):
    """Seed AppUser, Connection, and a 2-row Playlist for the e2e rebuild test."""
    user = AppUser(
        id=APP_USER_ID,
        provider_user_id="e2e-plex-uid",
    )
    db_session.add(user)

    now = datetime.now(UTC)
    conn = Connection(
        id=CONNECTION_ID,
        provider_type=PROVIDER,
        display_name="E2E Plex",
        base_url="https://plex.e2e.example.com",
        verify_ssl=True,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(conn)
    db_session.flush()

    playlist_id = str(uuid.uuid4())
    sid_a = _series("show-one")
    sid_b = _series("show-two")

    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=APP_USER_ID,
        name="E2E Rebuild Test",
        episode_count=6,
        slot_allocation="round_robin",
        default_completion_policy="remove",
        refresh_cadence="daily",
        created_at=now,
        updated_at=now,
    )
    db_session.add(pl)
    db_session.flush()

    for i, sid in enumerate([sid_a, sid_b]):
        row = PlaylistSeriesRowOrm(
            id=str(uuid.uuid4()),
            playlist_id=playlist_id,
            series_id=sid,
            mode="ordered",
            completion_policy="remove",
            completion_event="series_complete",
            sort_order=i,
        )
        db_session.add(row)
    db_session.commit()
    db_session.refresh(pl)

    return pl, sid_a, sid_b


@pytest.mark.asyncio
async def test_rebuild_persists_snapshot(db_session, e2e_playlist):
    """rebuild_playlist produces a RebuildRun with snapshot and rebuild_seed (SCH-02)."""
    pl, sid_a, sid_b = e2e_playlist

    # Fixture inputs matching builder golden vector shape
    inputs_map = {
        sid_a: SeriesRebuildInput(
            series_id=sid_a,
            episodes=[
                _episode("a-s1e1", 1, 1, sid_a),
                _episode("a-s1e2", 1, 2, sid_a),
                _episode("a-s1e3", 1, 3, sid_a),
            ],
        ),
        sid_b: SeriesRebuildInput(
            series_id=sid_b,
            episodes=[
                _episode("b-s1e1", 1, 1, sid_b),
                _episode("b-s1e2", 1, 2, sid_b),
                _episode("b-s1e3", 1, 3, sid_b),
            ],
        ),
    }

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        inp = inputs_map.get(series_id)
        if inp is None:
            return FetchResult(None, "fetch_failure")
        return FetchResult(inp, "ok")

    mock_provider = MagicMock()
    mock_provider.ping = AsyncMock(return_value=None)

    with (
        patch(f"{_ORCH}.build_provider_for_user", return_value=mock_provider),
        patch(f"{_ORCH}.fetch_rebuild_inputs_for_row", side_effect=_mock_fetch),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="e2e_test")

    assert run.status == "succeeded", f"Expected succeeded, got {run.status}: {run.error_message}"
    assert run.snapshot_json is not None
    assert len(run.snapshot_json) > 0
    assert run.rebuild_seed is not None and len(run.rebuild_seed) > 0

    # Every snapshot entry must have series_id present (SCH-02 requirement)
    for entry in run.snapshot_json:
        assert "series_id" in entry, f"Missing series_id in snapshot entry: {entry}"
        assert entry["series_id"] in (sid_a, sid_b)

    # Verify stored in DB
    stored = db_session.query(RebuildRun).filter(RebuildRun.id == run.id).one()
    assert stored.snapshot_json is not None
    assert stored.rebuild_seed == run.rebuild_seed
