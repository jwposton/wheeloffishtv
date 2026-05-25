from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

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
from wheeloffish.main import app

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
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
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
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unauthorized"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_unreachable(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderUnreachable())
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unreachable"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_ssl_error(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderSSLError())
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
        response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ssl_error"
    assert db_session.query(Connection).count() == 0


@pytest.mark.asyncio
async def test_create_wrong_type(connections_client, db_session) -> None:
    provider = _mock_provider(ping_side_effect=ProviderWrongType())
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
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
        with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
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
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
        first = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)
        second = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "duplicate_provider_type"
    assert db_session.query(Connection).count() == 1


@pytest.mark.asyncio
async def test_connection_response_excludes_token(connections_client) -> None:
    provider = _mock_provider()
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
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
    with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
        await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    response = await connections_client.get("/api/v1/connections")
    assert response.status_code == 200
    assert "token" not in response.text
    assert media_user_token_key("ignored", app_user_id) not in response.text
