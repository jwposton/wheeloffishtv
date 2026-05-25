import json
from pathlib import Path

import pytest
import respx
from httpx import Response
from starlette.testclient import TestClient

from wheeloffish.api.deps import get_current_user, get_db
from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.config import get_settings
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.integrations.plex.auth import clear_pin_state, store_pin_state
from wheeloffish.main import app

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def _override_db(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db


def _clear_overrides() -> None:
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
def phase3_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_PROVIDER", "plex")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://plex.example.com")
    monkeypatch.setenv("WOF_ADMIN_PROVIDER_USER_ID", "admin-plex-user")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
def auth_client(db_engine, db_session, phase3_settings):
    _override_db(db_session)
    with TestClient(app) as client:
        yield client
    _clear_overrides()


def _authenticate_client(client: TestClient, user: AppUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture
def authenticated_client(auth_client, db_session):
    user = AppUser(provider_user_id="regular-user", provider_username="viewer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _authenticate_client(auth_client, user)
    yield auth_client, user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admin_client(auth_client, db_session, phase3_settings):
    user = AppUser(
        provider_user_id=phase3_settings.WOF_ADMIN_PROVIDER_USER_ID,
        provider_username="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _authenticate_client(auth_client, user)
    yield auth_client, user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def non_admin_client(auth_client, db_session):
    user = AppUser(provider_user_id="not-admin", provider_username="viewer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _authenticate_client(auth_client, user)
    yield auth_client, user
    app.dependency_overrides.pop(get_current_user, None)


def test_auth_me_unauthenticated_returns_401(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "unauthenticated"


def test_bootstrap_session_returns_200_and_sets_cookie(auth_client: TestClient, db_session) -> None:
    response = auth_client.post("/api/v1/auth/bootstrap-session")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    me_response = auth_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    body = me_response.json()
    assert body["provider_user_id"].startswith("__pending__:")
    assert db_session.query(AppUser).count() == 1


def test_auth_me_includes_setup_mode_when_admin_unset(
    auth_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WOF_ADMIN_PROVIDER_USER_ID", "")
    get_settings.cache_clear()

    user = AppUser(provider_user_id="setup-user")
    db_session.add(user)
    db_session.commit()
    _authenticate_client(auth_client, user)

    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["setup_mode"] is True
    app.dependency_overrides.pop(get_current_user, None)


def test_non_admin_require_admin_returns_403(
    non_admin_client, db_session, phase3_settings
) -> None:
    client, _user = non_admin_client
    connection = sync_connection_from_env(db_session, phase3_settings)

    response = client.put(
        f"/api/v1/admin/connections/{connection.id}/library-scope",
        json={"in_scope_library_native_ids": []},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_admin_passes_require_admin(
    admin_client, db_session, phase3_settings
) -> None:
    client, _user = admin_client
    connection = sync_connection_from_env(db_session, phase3_settings)

    response = client.put(
        f"/api/v1/admin/connections/{connection.id}/library-scope",
        json={"in_scope_library_native_ids": []},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("start_body", [{}, None])
@respx.mock
def test_plex_oauth_start_without_base_url(
    auth_client: TestClient,
    db_session,
    phase3_settings,
    start_body,
) -> None:
    sync_connection_from_env(db_session, phase3_settings)
    auth_client.post("/api/v1/auth/bootstrap-session")

    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=Response(200, json=load_fixture("plex/pin_create"))
    )

    kwargs = {} if start_body is None else {"json": start_body}
    response = auth_client.post("/api/v1/connections/plex/oauth/start", **kwargs)

    assert response.status_code == 200
    body = response.json()
    assert body["pin_id"] == 123456789
    assert "auth_url" in body


@respx.mock
def test_plex_oauth_start_wrong_provider(
    auth_client: TestClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WOF_PROVIDER", "jellyfin")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://jellyfin.example.com")
    get_settings.cache_clear()

    auth_client.post("/api/v1/auth/bootstrap-session")
    sync_connection_from_env(db_session, get_settings())

    response = auth_client.post("/api/v1/connections/plex/oauth/start", json={})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "provider_disabled"
    get_settings.cache_clear()


@respx.mock
def test_plex_oauth_callback_session_cookie(
    auth_client: TestClient,
    db_session,
    vault,
    phase3_settings,
) -> None:
    connection = sync_connection_from_env(db_session, phase3_settings)
    bootstrap = auth_client.post("/api/v1/auth/bootstrap-session")
    assert bootstrap.status_code == 200
    pending_user_id = auth_client.get("/api/v1/auth/me").json()["app_user_id"]

    clear_pin_state(123456789)
    store_pin_state(
        123456789,
        connection_id=connection.id,
        base_url=connection.base_url,
        verify_ssl=connection.verify_ssl,
        client_identifier="11111111-2222-4333-8444-555555555555",
        app_user_id=pending_user_id,
    )

    respx.get("https://plex.tv/api/v2/pins/123456789").mock(
        return_value=Response(200, json=load_fixture("plex/pin_claimed"))
    )
    respx.get("https://plex.tv/api/v2/user").mock(
        return_value=Response(200, json={"id": 999, "username": "plexuser"})
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

    response = auth_client.get(
        "/api/v1/connections/plex/oauth/callback?pin_id=123456789",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/browse")

    me_response = auth_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["provider_user_id"] == "999"
    assert me_response.json()["has_media_link"] is True

    from wheeloffish.db.models.user_media_link import UserMediaLink

    link = (
        db_session.query(UserMediaLink)
        .filter(
            UserMediaLink.connection_id == connection.id,
            UserMediaLink.provider_user_id == "999",
        )
        .one()
    )
    assert link.connection_id == connection.id
    assert vault.get_media_user_token(connection.id, link.app_user_id) == "SANITIZED_PLEX_TOKEN"
