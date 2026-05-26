"""Orchestrator writeback hook tests."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from wheeloffish.core.orchestrator import rebuild_playlist
from wheeloffish.core.provider_writeback import WritebackResult
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.domain.dto import Episode
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.domain.playlist import SeriesRebuildInput

TEST_APP_USER_ID = "00000000-0000-4000-8000-000000000099"
TEST_CONNECTION_ID = "conn-aaaabbbb-1111-2222-3333-444455556666"


def _ep(episode_id: str) -> Episode:
    return Episode(
        id=episode_id,
        title="E1",
        season_index=1,
        episode_index=1,
        duration_ms=1_800_000,
        percent_watched=0.0,
    )


@pytest.mark.asyncio
async def test_rebuild_sets_writeback_status(db_session):
    user = AppUser(id=TEST_APP_USER_ID, provider_user_id="plex-uid")
    db_session.add(user)
    now = datetime.now(UTC)
    conn = Connection(
        id=TEST_CONNECTION_ID,
        provider_type="plex",
        display_name="Plex",
        base_url="https://plex.example.com",
        verify_ssl=True,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(conn)
    sid = format_composite_id(TEST_CONNECTION_ID, "plex", "show-a")
    pl = PlaylistOrm(
        id=str(uuid.uuid4()),
        app_user_id=TEST_APP_USER_ID,
        name="Test",
        episode_count=2,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        created_at=now,
        updated_at=now,
    )
    db_session.add(pl)
    db_session.flush()
    db_session.add(
        PlaylistSeriesRowOrm(
            id=str(uuid.uuid4()),
            playlist_id=pl.id,
            series_id=sid,
            mode="ordered",
            completion_policy="remove",
            completion_event="series_complete",
            sort_order=0,
        )
    )
    db_session.commit()

    good_input = SeriesRebuildInput(
        series_id=sid,
        episodes=[_ep(format_composite_id(TEST_CONNECTION_ID, "plex", "1001"))],
    )

    async def _mock_fetch(db, app_user_id, connection_id, series_id, provider):
        return good_input

    with (
        patch(
            "wheeloffish.core.orchestrator.fetch_rebuild_inputs_for_row",
            side_effect=_mock_fetch,
        ),
        patch(
            "wheeloffish.core.orchestrator.build_provider_for_user",
            return_value=AsyncMock(),
        ),
        patch(
            "wheeloffish.core.orchestrator.push_snapshot",
            new=AsyncMock(
                return_value=WritebackResult(status="succeeded"),
            ),
        ),
    ):
        run = await rebuild_playlist(db_session, pl.id, trigger="manual")

    assert run.status == "succeeded"
    assert run.writeback_status == "succeeded"
