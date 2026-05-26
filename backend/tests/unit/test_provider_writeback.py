"""Unit tests for provider writeback service."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.core.provider_writeback import ORPHAN_RECREATED_WARNING, push_snapshot
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.errors import ProviderNotFound
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.plex.client import PlexProvider

CONNECTION_ID = "conn-test"


def _playlist() -> PlaylistOrm:
    return PlaylistOrm(
        id="pl-1",
        app_user_id="user-1",
        name="Mix",
        episode_count=4,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        refresh_day_of_week=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _plex_provider() -> PlexProvider:
    return PlexProvider(
        base_url="https://plex.example.com",
        token="token",
        client_identifier="wof",
        connection_id=CONNECTION_ID,
        verify_ssl=True,
    )


@pytest.mark.asyncio
async def test_push_snapshot_creates_playlist(db_session):
    playlist = _playlist()
    db_session.add(playlist)
    db_session.commit()
    run = MagicMock()
    snapshot = [
        {"episode_id": format_composite_id(CONNECTION_ID, "plex", "1001")},
        {"episode_id": format_composite_id(CONNECTION_ID, "plex", "1002")},
    ]
    provider = _plex_provider()
    with (
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.resolve_episode_rating_key",
            new=AsyncMock(side_effect=["1001", "1002"]),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.create_video_playlist",
            new=AsyncMock(return_value="555"),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.list_playlist_item_keys",
            new=AsyncMock(return_value=["1001", "1002"]),
        ),
    ):
        result = await push_snapshot(db_session, playlist, run, snapshot, provider)
    assert result.status == "succeeded"
    assert playlist.provider_playlist_id == "555"
    assert playlist.provider_kind == "plex"


@pytest.mark.asyncio
async def test_push_snapshot_failed_when_zero_mapped():
    playlist = _playlist()
    run = MagicMock()
    provider = _plex_provider()
    with patch(
        "wheeloffish.core.provider_writeback.plex_playlists.resolve_episode_rating_key",
        new=AsyncMock(side_effect=ValueError("missing")),
    ):
        result = await push_snapshot(
            db=MagicMock(),
            playlist=playlist,
            run=run,
            snapshot=[{"episode_id": "x"}],
            provider=provider,
        )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_push_snapshot_recreates_when_plex_playlist_orphaned(db_session):
    playlist = _playlist()
    playlist.provider_playlist_id = "999"
    playlist.provider_kind = "plex"
    db_session.add(playlist)
    db_session.commit()
    provider = _plex_provider()
    snapshot = [{"episode_id": format_composite_id(CONNECTION_ID, "plex", "1001")}]
    with (
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.resolve_episode_rating_key",
            new=AsyncMock(return_value="1001"),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.replace_playlist_items",
            new=AsyncMock(side_effect=ProviderNotFound("Plex API error: 404")),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.playlist_exists",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.create_video_playlist",
            new=AsyncMock(return_value="555"),
        ) as mock_create,
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.list_playlist_item_keys",
            new=AsyncMock(return_value=["1001"]),
        ),
    ):
        result = await push_snapshot(db_session, playlist, MagicMock(), snapshot, provider)
    assert result.status == "succeeded"
    assert playlist.provider_playlist_id == "555"
    mock_create.assert_awaited_once()
    assert any(
        w.get("reason") == ORPHAN_RECREATED_WARNING["reason"]
        for w in (result.warnings or [])
    )


@pytest.mark.asyncio
async def test_push_snapshot_partial_when_episode_mapping_fails():
    playlist = _playlist()
    provider = _plex_provider()
    snapshot = [
        {"episode_id": format_composite_id(CONNECTION_ID, "plex", "1001")},
        {"episode_id": format_composite_id(CONNECTION_ID, "plex", "bad-guid")},
    ]
    with (
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.resolve_episode_rating_key",
            new=AsyncMock(side_effect=["1001", ValueError("missing guid")]),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.create_video_playlist",
            new=AsyncMock(return_value="555"),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.list_playlist_item_keys",
            new=AsyncMock(return_value=["1001"]),
        ),
    ):
        result = await push_snapshot(
            MagicMock(),
            playlist,
            MagicMock(),
            snapshot,
            provider,
        )
    assert result.status == "partial"
    assert len([w for w in (result.warnings or []) if w.get("episode_id")]) == 1


@pytest.mark.asyncio
async def test_push_snapshot_does_not_recreate_when_replace_fails_but_playlist_exists():
    playlist = _playlist()
    playlist.provider_playlist_id = "999"
    playlist.provider_kind = "plex"
    provider = _plex_provider()
    snapshot = [{"episode_id": format_composite_id(CONNECTION_ID, "plex", "1001")}]
    with (
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.resolve_episode_rating_key",
            new=AsyncMock(return_value="1001"),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.replace_playlist_items",
            new=AsyncMock(side_effect=ProviderNotFound("Plex API error: 404")),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.playlist_exists",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "wheeloffish.core.provider_writeback.plex_playlists.create_video_playlist",
            new=AsyncMock(),
        ) as mock_create,
    ):
        result = await push_snapshot(
            MagicMock(),
            playlist,
            MagicMock(),
            snapshot,
            provider,
        )
    assert result.status == "failed"
    assert playlist.provider_playlist_id == "999"
    mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_push_snapshot_jellyfin(db_session):
    playlist = _playlist()
    db_session.add(playlist)
    db_session.commit()
    provider = JellyfinProvider(
        base_url="https://jf.example.com",
        token="token",
        user_id="u1",
        connection_id=CONNECTION_ID,
        verify_ssl=True,
    )
    snapshot = [{"episode_id": format_composite_id(CONNECTION_ID, "jellyfin", "ep-1")}]
    with patch(
        "wheeloffish.core.provider_writeback.jellyfin_playlists.create_playlist",
        new=AsyncMock(return_value="jf-pl-1"),
    ):
        result = await push_snapshot(db_session, playlist, MagicMock(), snapshot, provider)
    assert result.status == "succeeded"
    assert playlist.provider_kind == "jellyfin"
