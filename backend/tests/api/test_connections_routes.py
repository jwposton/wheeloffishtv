import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from wheeloffish.api.deps import get_db
from wheeloffish.core.config import get_settings
from wheeloffish.core.namespaces import media_user_token_key
from wheeloffish.db.models.connection import Connection
from wheeloffish.integrations.errors import (
    ProviderSSLError,
    ProviderUnauthorized,
    ProviderUnreachable,
    ProviderWrongType,
)
from wheeloffish.integrations.plex.auth import clear_pin_state, store_pin_state
from wheeloffish.integrations.plex.client import PlexProvider
from wheeloffish.main import app

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())

PLEX_PAYLOAD = {
    "provider_type": "plex",
    "display_name": "Home Plex",
    "base_url": "https://plex.example.com",
    "verify_ssl": True,
    "token": "plex-test-token",
}

JELLYFIN_PAYLOAD = {
    "provider_type": "jellyfin",
    "display_name": "Home Jellyfin",
    "base_url": "https://jellyfin.example.com",
    "verify_ssl": True,
    "token": "jellyfin-test-token",
}


def _mock_provider(*, ping_side_effect=None) -> MagicMock:
    provider = MagicMock()
    provider.ping = AsyncMock(side_effect=ping_side_effect)
    provider.provider_user_id = "provider-user-1"
    provider.provider_username = "testuser"
    return provider


@pytest.fixture
async def connections_client(db_engine, db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex,jellyfin")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_create_connection_success(
    connections_client, db_session, vault, app_user_id
) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["provider_type"] == "plex"
    assert "token" not in body

    connection_id = body["id"]
    assert db_session.query(Connection).count() == 1
    assert vault.get_media_user_token(connection_id, app_user_id) == PLEX_PAYLOAD["token"]
    provider.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_unauthorized(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderUnauthorized())
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unauthorized"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_unreachable(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderUnreachable())
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unreachable"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_ssl_error(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderSSLError())
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ssl_error"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_wrong_type(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderWrongType())
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "wrong_type"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_provider_disabled(db_engine, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    provider = _mock_provider()
    try:
        with patch(
            "wheeloffish.core.connections.build_provider_for_connection",
            return_value=provider,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/connections", json=JELLYFIN_PAYLOAD)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "provider_disabled"
    assert db_session.query(Connection).count() == 0
    provider.ping.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_provider_type(connections_client, db_session) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        first = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)
        second = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "duplicate_provider_type"
    assert db_session.query(Connection).count() == 1


@pytest.mark.asyncio
async def test_connection_response_excludes_token(connections_client) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        create_response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)
        list_response = await connections_client.get("/api/v1/connections")

    assert create_response.status_code == 201
    assert "token" not in create_response.json()

    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert "token" not in items[0]


@pytest.mark.asyncio
async def test_list_connections_no_secrets(connections_client, vault, app_user_id) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    response = await connections_client.get("/api/v1/connections")
    assert response.status_code == 200
    assert "token" not in response.text
    assert media_user_token_key("ignored", app_user_id) not in response.text


PLEX_OAUTH_START = {
    "display_name": "Home Plex",
    "base_url": "https://plex.example.com",
    "verify_ssl": True,
}


@pytest.mark.asyncio
@respx.mock
async def test_plex_oauth_start(connections_client) -> None:
    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=Response(200, json=load_fixture("plex/pin_create"))
    )

    response = await connections_client.post(
        "/api/v1/connections/plex/oauth/start",
        json=PLEX_OAUTH_START,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pin_id"] == 123456789
    assert "auth_url" in body
    assert "app.plex.tv/auth" in body["auth_url"]
    assert "code=ABCD" in body["auth_url"]
    assert "token" not in body


@pytest.mark.asyncio
@respx.mock
async def test_plex_oauth_callback_stores_vault_token(
    connections_client, db_session, vault, app_user_id
) -> None:
    clear_pin_state(123456789)
    store_pin_state(
        123456789,
        display_name=PLEX_OAUTH_START["display_name"],
        base_url=PLEX_OAUTH_START["base_url"],
        verify_ssl=PLEX_OAUTH_START["verify_ssl"],
        client_identifier="11111111-2222-4333-8444-555555555555",
        app_user_id=app_user_id,
    )

    respx.get("https://plex.tv/api/v2/pins/123456789").mock(
        return_value=Response(200, json=load_fixture("plex/pin_claimed"))
    )
    respx.get("https://plex.tv/api/v2/user").mock(
        return_value=Response(200, json={"id": 999, "username": "testuser"})
    )
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
    respx.get("https://plex.example.com/library/sections").mock(
        return_value=Response(200, json=load_fixture("plex/library_sections"))
    )

    response = await connections_client.get(
        "/api/v1/connections/plex/oauth/callback?pin_id=123456789"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "connected"
    assert body["auth_token_present"] is True
    assert "SANITIZED_PLEX_TOKEN" not in json.dumps(body)

    connection_id = body["connection_id"]
    assert db_session.query(Connection).count() == 1
    assert vault.get_media_user_token(connection_id, app_user_id) == "SANITIZED_PLEX_TOKEN"


@pytest.mark.asyncio
@respx.mock
async def test_plex_list_libraries(connections_client) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_provider_for_connection", return_value=provider):
        create_response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)
    connection_id = create_response.json()["id"]

    respx.get("https://plex.example.com/library/sections").mock(
        return_value=Response(200, json=load_fixture("plex/library_sections"))
    )

    with patch(
        "wheeloffish.core.connections.build_provider_for_connection",
        return_value=PlexProvider(
            base_url=PLEX_PAYLOAD["base_url"],
            token=PLEX_PAYLOAD["token"],
            client_identifier="11111111-2222-4333-8444-555555555555",
            connection_id=connection_id,
            verify_ssl=True,
        ),
    ):
        response = await connections_client.get(
            f"/api/v1/connections/{connection_id}/libraries"
        )

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 2
    assert libraries[0]["title"] == "Fictional TV Shows"
    assert ":plex:" in libraries[0]["id"]
    assert "token" not in response.text


JELLYFIN_AUTH_PAYLOAD = {
    "base_url": "https://jellyfin.example.com",
    "username": "testuser",
    "password": "secret-password",
    "display_name": "Home Jellyfin",
    "verify_ssl": True,
}


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_auth_success(
    connections_client, db_session, vault, app_user_id
) -> None:
    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(200, json=load_fixture("jellyfin/authenticate"))
    )
    respx.get("https://jellyfin.example.com/Users/Me").mock(
        return_value=Response(
            200,
            json={"Id": "22222222-3333-4444-8555-666666666666", "Name": "testuser"},
        )
    )

    response = await connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "connected"
    assert body["auth_token_present"] is True
    assert "SANITIZED_JELLYFIN_TOKEN" not in json.dumps(body)
    assert "secret-password" not in response.text

    connection_id = body["connection_id"]
    assert db_session.query(Connection).count() == 1
    assert vault.get_media_user_token(connection_id, app_user_id) == "SANITIZED_JELLYFIN_TOKEN"


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_auth_unauthorized(connections_client, db_session) -> None:
    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(401)
    )

    response = await connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unauthorized"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_list_libraries(connections_client, db_session, vault, app_user_id) -> None:
    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(200, json=load_fixture("jellyfin/authenticate"))
    )
    respx.get("https://jellyfin.example.com/Users/Me").mock(
        return_value=Response(
            200,
            json={"Id": "22222222-3333-4444-8555-666666666666", "Name": "testuser"},
        )
    )

    auth_response = await connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )
    connection_id = auth_response.json()["connection_id"]

    respx.get("https://jellyfin.example.com/Library/MediaFolders").mock(
        return_value=Response(200, json=load_fixture("jellyfin/media_folders"))
    )

    response = await connections_client.get(
        f"/api/v1/connections/{connection_id}/libraries"
    )

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 1
    assert libraries[0]["title"] == "TV Shows"
    assert ":jellyfin:" in libraries[0]["id"]
    assert "token" not in response.text
