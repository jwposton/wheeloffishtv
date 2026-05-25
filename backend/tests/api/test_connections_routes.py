import json
from pathlib import Path
from unittest.mock import patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from wheeloffish.api.deps import get_db
from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.config import get_settings
from wheeloffish.core.connections import link_media_user
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
from wheeloffish.integrations.plex.auth import clear_pin_state, store_pin_state
from wheeloffish.integrations.plex.client import PlexProvider
from conftest import seed_cached_libraries
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


@pytest.fixture
async def connections_client(db_engine, db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_PROVIDER", "plex")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://plex.example.com")
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex,jellyfin")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        bootstrap = await client.post("/api/v1/auth/bootstrap-session")
        assert bootstrap.status_code == 200
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
async def jellyfin_connections_client(db_engine, db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_PROVIDER", "jellyfin")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://jellyfin.example.com")
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex,jellyfin")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        bootstrap = await client.post("/api/v1/auth/bootstrap-session")
        assert bootstrap.status_code == 200
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


async def _session_app_user_id(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    return response.json()["app_user_id"]


@pytest.mark.asyncio
async def test_post_connection_env_config_only(connections_client) -> None:
    response = await connections_client.post("/api/v1/connections", json=PLEX_PAYLOAD)

    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["code"] == "env_config_only"
    assert "Configure connection in .env" in body["detail"]["message"]


@pytest.mark.asyncio
async def test_list_connections_no_secrets(
    connections_client, db_session, vault
) -> None:
    settings = get_settings()
    connection = sync_connection_from_env(db_session, settings)
    session_user_id = await _session_app_user_id(connections_client)
    user = db_session.query(AppUser).filter(AppUser.id == session_user_id).one()
    link_media_user(
        db_session,
        vault,
        connection,
        user,
        provider_user_id="provider-user-1",
        provider_username="testuser",
        token=PLEX_PAYLOAD["token"],
    )

    response = await connections_client.get("/api/v1/connections")
    assert response.status_code == 200
    assert "token" not in response.text
    items = response.json()
    assert len(items) == 1
    assert items[0]["provider_type"] == "plex"


@pytest.mark.asyncio
@respx.mock
async def test_plex_oauth_start(connections_client, db_session) -> None:
    settings = get_settings()
    sync_connection_from_env(db_session, settings)

    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=Response(200, json=load_fixture("plex/pin_create"))
    )

    response = await connections_client.post(
        "/api/v1/connections/plex/oauth/start",
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pin_id"] == 123456789
    assert "auth_url" in body
    assert "app.plex.tv/auth" in body["auth_url"]
    assert "token" not in body


@pytest.mark.asyncio
@respx.mock
async def test_plex_oauth_callback_stores_vault_token(
    connections_client, db_session, vault
) -> None:
    settings = get_settings()
    connection = sync_connection_from_env(db_session, settings)
    session_user_id = await _session_app_user_id(connections_client)

    clear_pin_state(123456789)
    store_pin_state(
        123456789,
        connection_id=connection.id,
        base_url=connection.base_url,
        verify_ssl=connection.verify_ssl,
        client_identifier="11111111-2222-4333-8444-555555555555",
        app_user_id=session_user_id,
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
        "/api/v1/connections/plex/oauth/callback?pin_id=123456789",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert db_session.query(Connection).count() == 1

    me = await connections_client.get("/api/v1/auth/me")
    linked_user_id = me.json()["app_user_id"]
    assert vault.get_plex_user_credentials(connection.id, linked_user_id) is not None
    assert vault.get_media_user_token(connection.id, linked_user_id) == "SANITIZED_PLEX_TOKEN"


@pytest.mark.asyncio
@respx.mock
async def test_plex_list_libraries(connections_client, db_session, vault) -> None:
    settings = get_settings()
    connection = sync_connection_from_env(db_session, settings)
    session_user_id = await _session_app_user_id(connections_client)
    user = db_session.query(AppUser).filter(AppUser.id == session_user_id).one()
    link_media_user(
        db_session,
        vault,
        connection,
        user,
        provider_user_id="provider-user-1",
        provider_username="testuser",
        token=PLEX_PAYLOAD["token"],
        plex_client_identifier="11111111-2222-4333-8444-555555555555",
    )

    seed_cached_libraries(
        db_session,
        connection.id,
        [
            {"native_id": "1", "title": "Fictional TV Shows", "in_scope": True},
            {"native_id": "2", "title": "Other Shows", "in_scope": True},
        ],
    )

    respx.get("https://plex.example.com/library/sections").mock(
        return_value=Response(200, json=load_fixture("plex/library_sections"))
    )

    with patch(
        "wheeloffish.core.connections.build_provider_for_connection",
        return_value=PlexProvider(
            base_url=PLEX_PAYLOAD["base_url"],
            token=PLEX_PAYLOAD["token"],
            client_identifier="11111111-2222-4333-8444-555555555555",
            connection_id=connection.id,
            verify_ssl=True,
        ),
    ):
        response = await connections_client.get(
            f"/api/v1/connections/{connection.id}/libraries"
        )

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 2
    assert libraries[0]["title"] == "Fictional TV Shows"
    assert ":plex:" in libraries[0]["id"]
    assert "token" not in response.text


JELLYFIN_AUTH_PAYLOAD = {
    "username": "testuser",
    "password": "secret-password",
}


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_auth_success(
    jellyfin_connections_client, db_session, vault
) -> None:
    settings = get_settings()
    connection = sync_connection_from_env(db_session, settings)

    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(200, json=load_fixture("jellyfin/authenticate"))
    )
    respx.get("https://jellyfin.example.com/Users/Me").mock(
        return_value=Response(
            200,
            json={"Id": "22222222-3333-4444-8555-666666666666", "Name": "testuser"},
        )
    )
    respx.get("https://jellyfin.example.com/Library/MediaFolders").mock(
        return_value=Response(200, json=load_fixture("jellyfin/media_folders"))
    )

    response = await jellyfin_connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "connected"
    assert body["auth_token_present"] is True
    assert body["connection_id"] == connection.id
    assert "SANITIZED_JELLYFIN_TOKEN" not in json.dumps(body)
    assert "secret-password" not in response.text

    assert db_session.query(Connection).count() == 1

    me = await jellyfin_connections_client.get("/api/v1/auth/me")
    linked_user_id = me.json()["app_user_id"]
    assert vault.get_media_user_token(connection.id, linked_user_id) == "SANITIZED_JELLYFIN_TOKEN"


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_auth_unauthorized(jellyfin_connections_client, db_session) -> None:
    sync_connection_from_env(db_session, get_settings())

    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(401)
    )

    response = await jellyfin_connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unauthorized"
    assert db_session.query(Connection).count() == 1


@pytest.mark.asyncio
@respx.mock
async def test_jellyfin_list_libraries(
    jellyfin_connections_client, db_session, vault, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "WOF_SCOPED_LIBRARY_IDS",
        "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
    )
    get_settings.cache_clear()
    settings = get_settings()
    connection = sync_connection_from_env(db_session, settings)

    respx.post("https://jellyfin.example.com/Users/AuthenticateByName").mock(
        return_value=Response(200, json=load_fixture("jellyfin/authenticate"))
    )
    respx.get("https://jellyfin.example.com/Users/Me").mock(
        return_value=Response(
            200,
            json={"Id": "22222222-3333-4444-8555-666666666666", "Name": "testuser"},
        )
    )
    respx.get("https://jellyfin.example.com/Library/MediaFolders").mock(
        return_value=Response(200, json=load_fixture("jellyfin/media_folders"))
    )

    auth_response = await jellyfin_connections_client.post(
        "/api/v1/connections/jellyfin/auth",
        json=JELLYFIN_AUTH_PAYLOAD,
    )
    assert auth_response.status_code == 201

    response = await jellyfin_connections_client.get(
        f"/api/v1/connections/{connection.id}/libraries"
    )

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 1
    assert libraries[0]["title"] == "TV Shows"
    assert ":jellyfin:" in libraries[0]["id"]
    assert "token" not in response.text
