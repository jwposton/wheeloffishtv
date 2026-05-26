"""Unit tests for Plex playlist writeback client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wheeloffish.integrations.playlist_names import provider_playlist_display_name
from wheeloffish.integrations.plex import playlists as plex_playlists
from wheeloffish.integrations.plex.client import PlexProvider

CONNECTION_ID = "conn-test"


def _provider() -> PlexProvider:
    return PlexProvider(
        base_url="https://plex.example.com",
        token="test-token",
        client_identifier="wof-test",
        connection_id=CONNECTION_ID,
        verify_ssl=True,
    )


def _response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


def test_provider_playlist_display_name():
    assert provider_playlist_display_name("Saturday Mix") == "Saturday Mix [WoF]"


@pytest.mark.asyncio
async def test_create_video_playlist():
    provider = _provider()
    with patch.object(provider, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            _response({"MediaContainer": {"machineIdentifier": "machine-1"}}),
            _response({"MediaContainer": {"Metadata": [{"ratingKey": "999"}]}}),
        ]
        key = await plex_playlists.create_video_playlist(
            provider, "Mix [WoF]", ["101", "102"]
        )
    assert key == "999"
    create_call = mock_request.call_args_list[1]
    assert create_call.args[0] == "POST"
    assert create_call.kwargs["params"]["uri"] == (
        "server://machine-1/com.plexapp.plugins.library/library/metadata/101,102"
    )


@pytest.mark.asyncio
async def test_replace_playlist_items():
    provider = _provider()
    with patch.object(provider, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            _response({}),
            _response({"MediaContainer": {"machineIdentifier": "machine-1"}}),
            _response({}),
        ]
        await plex_playlists.replace_playlist_items(provider, "777", ["101", "102"])
    methods = [call.args[0] for call in mock_request.call_args_list]
    assert methods == ["DELETE", "GET", "PUT"]
    clear_call = mock_request.call_args_list[0]
    assert clear_call.args[1] == "/playlists/777/items"
    put_call = mock_request.call_args_list[2]
    assert put_call.kwargs["params"]["uri"] == (
        "server://machine-1/com.plexapp.plugins.library/library/metadata/101,102"
    )
