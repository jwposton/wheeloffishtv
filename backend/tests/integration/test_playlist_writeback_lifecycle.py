"""Integration tests for provider playlist lifecycle sync."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from wheeloffish.api.deps import get_current_user, get_db
from wheeloffish.core.config import get_settings
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.db.session import reset_session_state
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.main import app

TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
TEST_CONNECTION_ID = "conn-lifecycle-test"


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("WOF_PROVIDER", "plex")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://plex.example.com")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    reset_session_state()
    yield
    get_settings.cache_clear()
    reset_session_state()


@pytest.fixture
def base_client(db_engine, db_session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _set_user(user: AppUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def _seed_playlist(db_session, user: AppUser) -> PlaylistOrm:
    now = datetime.now(UTC)
    conn = db_session.query(Connection).filter(Connection.provider_type == "plex").one_or_none()
    if conn is None:
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
        db_session.flush()
    connection_id = conn.id
    existing_link = (
        db_session.query(UserMediaLink)
        .filter(
            UserMediaLink.app_user_id == user.id,
            UserMediaLink.connection_id == connection_id,
        )
        .one_or_none()
    )
    if existing_link is None:
        db_session.add(
            UserMediaLink(
                id=str(uuid.uuid4()),
                app_user_id=user.id,
                connection_id=connection_id,
                provider_user_id="plex-user",
                linked_at=now,
            )
        )
    series_id = format_composite_id(connection_id, "plex", "show-guid")
    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=user.id,
            connection_id=connection_id,
            library_native_id="1",
            title="Show",
            native_id="show-guid",
            provider_metadata={},
            synced_at=now,
        )
    )
    playlist = PlaylistOrm(
        id=str(uuid.uuid4()),
        app_user_id=user.id,
        name="Old Name",
        episode_count=5,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        provider_playlist_id="777",
        provider_kind="plex",
        created_at=now,
        updated_at=now,
    )
    db_session.add(playlist)
    db_session.flush()
    db_session.add(
        PlaylistSeriesRowOrm(
            id=str(uuid.uuid4()),
            playlist_id=playlist.id,
            series_id=series_id,
            mode="ordered",
            completion_policy="remove",
            completion_event="series_complete",
            sort_order=0,
        )
    )
    db_session.commit()
    db_session.refresh(playlist)
    return playlist


def test_rename_playlist_calls_provider_rename(base_client: TestClient, db_session):
    user = AppUser(provider_user_id="user-a", provider_username="user-a")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _set_user(user)
    playlist = _seed_playlist(db_session, user)

    with (
        patch(
            "wheeloffish.api.routes.playlists._with_provider_for_playlist",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "wheeloffish.api.routes.playlists.rename_linked",
            new=AsyncMock(),
        ) as mock_rename,
    ):
        response = base_client.put(
            f"/api/v1/playlists/{playlist.id}",
            json={"name": "New Name"},
        )
    assert response.status_code == 200
    mock_rename.assert_awaited_once()


def test_delete_playlist_calls_provider_delete(base_client: TestClient, db_session):
    user = AppUser(provider_user_id="user-b", provider_username="user-b")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _set_user(user)
    playlist = _seed_playlist(db_session, user)

    with (
        patch(
            "wheeloffish.api.routes.playlists._with_provider_for_playlist",
            new=AsyncMock(return_value=object()),
        ),
        patch(
            "wheeloffish.api.routes.playlists.delete_linked",
            new=AsyncMock(),
        ) as mock_delete,
    ):
        response = base_client.delete(f"/api/v1/playlists/{playlist.id}")
    assert response.status_code == 204
    mock_delete.assert_awaited_once()
