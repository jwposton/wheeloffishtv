"""Unit tests for Jellyfin playlist writeback client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.jellyfin import playlists as jellyfin_playlists
from wheeloffish.integrations.jellyfin.client import JellyfinProvider

CONNECTION_ID = "conn-jf"
USER_ID = "user-jf"


def _provider() -> JellyfinProvider:
    return JellyfinProvider(
        base_url="https://jellyfin.example.com",
        token="token",
        user_id=USER_ID,
        connection_id=CONNECTION_ID,
        verify_ssl=True,
    )


def _response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


@pytest.mark.asyncio
async def test_replace_playlist_items():
    provider = _provider()
    with patch.object(provider, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            _response({"Items": [{"PlaylistItemId": "entry-1"}]}),
            _response({}),
            _response({}),
        ]
        await jellyfin_playlists.replace_playlist_items(provider, "pl-1", ["ep-1", "ep-2"])
    methods = [call.args[0] for call in mock_request.call_args_list]
    assert methods == ["GET", "DELETE", "POST"]


def test_episode_native_id():
    episode_id = format_composite_id(CONNECTION_ID, "jellyfin", "abc-episode-id")
    assert jellyfin_playlists.episode_native_id(episode_id) == "abc-episode-id"
