import json
import re
from pathlib import Path

import pytest
import respx
from httpx import Response

from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.plex.auth import (
    build_auth_url,
    create_pin_with_auth_url,
    discover_server,
    poll_pin,
    validate_token,
)
from wheeloffish.integrations.plex.client import PlexProvider

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())

CLIENT_ID = "11111111-2222-4333-8444-555555555555"
CONNECTION_ID = "conn-test-uuid"
BASE_URL = "https://plex.example.com"
TOKEN = "SANITIZED_PLEX_TOKEN"
PRODUCT = "Wheel of Fish TV"


@pytest.mark.asyncio
@respx.mock
async def test_oauth_start_create_pin() -> None:
    pin_create = load_fixture("plex/pin_create")
    route = respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=Response(200, json=pin_create)
    )

    pin_id, code, auth_url = await create_pin_with_auth_url(
        CLIENT_ID,
        PRODUCT,
        "http://localhost:8000",
    )

    assert route.called
    assert pin_id == 123456789
    assert code == "ABCD"
    assert "clientID=" in auth_url
    assert "code=ABCD" in auth_url
    assert "app.plex.tv/auth" in auth_url


@pytest.mark.asyncio
@respx.mock
async def test_oauth_start_build_auth_url() -> None:
    auth_url = build_auth_url(
        client_identifier=CLIENT_ID,
        code="ABCD",
        product_name=PRODUCT,
        callback_base="http://localhost:8000",
        pin_id=123456789,
    )
    assert f"clientID={CLIENT_ID}" in auth_url
    assert "code=ABCD" in auth_url
    assert "pin_id%3D123456789" in auth_url


@pytest.mark.asyncio
@respx.mock
async def test_oauth_poll_pin_claimed() -> None:
    respx.get("https://plex.tv/api/v2/pins/123456789").mock(
        return_value=Response(200, json=load_fixture("plex/pin_claimed"))
    )

    token = await poll_pin(123456789, CLIENT_ID, PRODUCT)
    assert token == TOKEN


@pytest.mark.asyncio
@respx.mock
async def test_oauth_validate_token() -> None:
    respx.get("https://plex.tv/api/v2/user").mock(
        return_value=Response(200, json={"id": 999, "username": "testuser"})
    )

    user = await validate_token(TOKEN, CLIENT_ID, PRODUCT)
    assert user["id"] == 999
    assert user["username"] == "testuser"


@pytest.mark.asyncio
@respx.mock
async def test_oauth_discover_server() -> None:
    respx.get("https://plex.tv/api/v2/resources").mock(
        return_value=Response(
            200,
            json=[
                {
                    "name": "Home",
                    "connections": [{"uri": "https://plex.example.com"}],
                }
            ],
        )
    )

    found = await discover_server(TOKEN, BASE_URL, CLIENT_ID, PRODUCT)
    assert found is True


def _provider() -> PlexProvider:
    return PlexProvider(
        base_url=BASE_URL,
        token=TOKEN,
        client_identifier=CLIENT_ID,
        connection_id=CONNECTION_ID,
        verify_ssl=True,
        product_name=PRODUCT,
    )


@pytest.mark.asyncio
@respx.mock
async def test_list_libraries() -> None:
    respx.get(f"{BASE_URL}/library/sections").mock(
        return_value=Response(200, json=load_fixture("plex/library_sections"))
    )

    libraries = await _provider().list_libraries()

    assert len(libraries) == 2
    assert libraries[0].title == "Fictional TV Shows"
    assert libraries[0].native_id == "1"
    assert ":plex:" in libraries[0].id
    assert "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee" in libraries[0].id


@pytest.mark.asyncio
@respx.mock
async def test_list_series_paged() -> None:
    respx.get(re.compile(rf"{BASE_URL}/library/sections/1/all.*")).mock(
        return_value=Response(200, json=load_fixture("plex/show_series"))
    )

    page = await _provider().list_series("1", page=1, limit=50, q=None)

    assert page.total == 2
    assert len(page.items) == 2
    assert page.items[0].title == "Fictional Show"
    assert ":plex:" in page.items[0].id
    assert "com.plexapp.agents.thetvdb" in page.items[0].id
    assert "1001" not in page.items[0].id


@pytest.mark.asyncio
@respx.mock
async def test_list_episodes_watch_fields() -> None:
    series_id = format_composite_id(CONNECTION_ID, "plex", "com.plexapp.agents.thetvdb://12345")

    respx.get(f"{BASE_URL}/library/all").mock(
        return_value=Response(200, json=load_fixture("plex/guid_lookup"))
    )
    respx.get(f"{BASE_URL}/library/metadata/1001/allLeaves").mock(
        return_value=Response(200, json=load_fixture("plex/show_leaves"))
    )

    episodes = await _provider().list_episodes(series_id)

    assert len(episodes) == 4
    assert episodes[0].percent_watched == 0.0
    assert episodes[0].provider_marked_played is False
    assert episodes[1].provider_marked_played is True
    assert episodes[2].percent_watched == pytest.approx(50.0)
    assert episodes[2].provider_marked_played is False
