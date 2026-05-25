import pytest
import respx
from httpx import Response

from wheeloffish.integrations.plex.auth import resolve_server_connection


@pytest.mark.asyncio
@respx.mock
async def test_resolve_server_connection_uses_resource_access_token() -> None:
    respx.get("https://plex.tv/api/v2/resources").mock(
        return_value=Response(
            200,
            json=[
                {
                    "accessToken": "SERVER-SPECIFIC-TOKEN",
                    "connections": [
                        {"uri": "https://plex.example.com"},
                    ],
                }
            ],
        )
    )

    resolved = await resolve_server_connection(
        "PLEX-TV-TOKEN",
        "https://plex.example.com",
        "client-id",
        "Wheel of Fish TV",
    )

    assert resolved.base_url == "https://plex.example.com"
    assert resolved.token == "SERVER-SPECIFIC-TOKEN"


@pytest.mark.asyncio
@respx.mock
async def test_resolve_server_connection_falls_back_to_pin_token() -> None:
    respx.get("https://plex.tv/api/v2/resources").mock(
        return_value=Response(
            200,
            json=[
                {
                    "connections": [{"uri": "https://plex.example.com"}],
                }
            ],
        )
    )

    resolved = await resolve_server_connection(
        "PLEX-TV-TOKEN",
        "https://plex.example.com/",
        "client-id",
        "Wheel of Fish TV",
    )

    assert resolved.token == "PLEX-TV-TOKEN"
