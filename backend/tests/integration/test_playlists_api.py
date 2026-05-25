"""Integration tests: Playlist CRUD + rebuild API ownership and correctness (Phase 05 Plan 04).

Decision coverage: D-04 defaults, D-06/D-22 rebuild, D-16 history, D-18 ownership.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from wheeloffish.api.deps import get_current_user, get_db
from wheeloffish.core.config import get_settings
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.db.session import reset_session_state
from wheeloffish.main import app

TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
SERIES_ID_A = "conn-aaaa::plex::show-alpha"
SERIES_ID_B = "conn-aaaa::plex::show-beta"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


def _make_user(db_session, provider_user_id: str = "user-a") -> AppUser:
    user = AppUser(provider_user_id=provider_user_id, provider_username=provider_user_id)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _set_user(user: AppUser) -> None:
    """Switch the active get_current_user override to the given user."""
    app.dependency_overrides[get_current_user] = lambda: user


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _create_body(**overrides) -> dict:
    defaults: dict = {
        "name": "My Playlist",
        "rows": [{"series_id": SERIES_ID_A}],
    }
    return {**defaults, **overrides}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_playlist_returns_201(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)
    resp = base_client.post("/api/v1/playlists", json=_create_body())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "My Playlist"
    assert body["refresh_cadence"] == "daily"
    assert body["episode_count"] == 20
    assert len(body["rows"]) == 1
    assert body["rows"][0]["series_id"] == SERIES_ID_A


def test_create_playlist_defaults(base_client: TestClient, db_session) -> None:
    """D-04: refresh_cadence defaults to daily, episode_count to 20."""
    user = _make_user(db_session)
    _set_user(user)
    resp = base_client.post("/api/v1/playlists", json={"name": "Defaults", "rows": []})
    assert resp.status_code == 201
    body = resp.json()
    assert body["refresh_cadence"] == "daily"
    assert body["episode_count"] == 20


def test_list_playlists_scoped_to_user(base_client: TestClient, db_session) -> None:
    """D-18: User B cannot see User A's playlist in the list."""
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    base_client.post("/api/v1/playlists", json=_create_body(name="A's Playlist"))

    _set_user(user_b)
    resp_b = base_client.get("/api/v1/playlists")
    assert resp_b.status_code == 200
    assert resp_b.json() == []

    _set_user(user_a)
    resp_a = base_client.get("/api/v1/playlists")
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
    assert resp_a.json()[0]["name"] == "A's Playlist"


def test_get_other_users_playlist_404(base_client: TestClient, db_session) -> None:
    """D-18: Cross-user access returns 404 (not 403 — avoids existence leakage)."""
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    _set_user(user_b)
    resp = base_client.get(f"/api/v1/playlists/{playlist_id}")
    assert resp.status_code == 404


def test_update_playlist_rows(base_client: TestClient, db_session) -> None:
    """PUT replaces rows; ownership gate allows owner."""
    user = _make_user(db_session)
    _set_user(user)

    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    update = base_client.put(
        f"/api/v1/playlists/{playlist_id}",
        json={
            "rows": [
                {"series_id": SERIES_ID_A},
                {"series_id": SERIES_ID_B},
            ]
        },
    )
    assert update.status_code == 200, update.text
    body = update.json()
    assert len(body["rows"]) == 2
    assert body["rows"][1]["series_id"] == SERIES_ID_B


def test_update_other_users_playlist_404(base_client: TestClient, db_session) -> None:
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    _set_user(user_b)
    resp = base_client.put(f"/api/v1/playlists/{playlist_id}", json={"name": "Hijacked"})
    assert resp.status_code == 404


def test_delete_playlist(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)

    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    delete = base_client.delete(f"/api/v1/playlists/{playlist_id}")
    assert delete.status_code == 204

    get = base_client.get(f"/api/v1/playlists/{playlist_id}")
    assert get.status_code == 404


def test_delete_other_users_playlist_404(base_client: TestClient, db_session) -> None:
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    _set_user(user_b)
    resp = base_client.delete(f"/api/v1/playlists/{playlist_id}")
    assert resp.status_code == 404


def test_rebuild_owner_only_returns_run_summary(base_client: TestClient, db_session) -> None:
    """D-22: Rebuild trigger returns 404 for non-owner; owner gets run summary."""
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    # Non-owner should 404
    _set_user(user_b)
    resp_b = base_client.post(f"/api/v1/playlists/{playlist_id}/rebuild")
    assert resp_b.status_code == 404

    # Owner succeeds — mock the underlying orchestrator
    fake_run = RebuildRun(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id,
        status="succeeded",
        slots_filled=5,
        slots_requested=20,
    )

    _set_user(user_a)
    with patch(
        "wheeloffish.api.routes.playlists.run_manual_rebuild",
        new=AsyncMock(return_value=fake_run),
    ):
        resp_a = base_client.post(f"/api/v1/playlists/{playlist_id}/rebuild")

    assert resp_a.status_code == 200, resp_a.text
    body = resp_a.json()
    assert body["status"] == "succeeded"
    assert body["slots_filled"] == 5


def test_rebuild_409_when_running(base_client: TestClient, db_session) -> None:
    """Rebuild returns 409 if a run is already in progress."""
    user = _make_user(db_session)
    _set_user(user)

    create = base_client.post("/api/v1/playlists", json=_create_body())
    playlist_id = create.json()["id"]

    running_run = RebuildRun(
        id=str(uuid.uuid4()),
        playlist_id=playlist_id,
        status="running",
    )
    db_session.add(running_run)
    db_session.commit()

    resp = base_client.post(f"/api/v1/playlists/{playlist_id}/rebuild")
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "rebuild_in_progress"


def test_unauthenticated_returns_401(base_client: TestClient) -> None:
    """T-05-04-04: All routes require authentication (no get_current_user override)."""
    resp = base_client.get("/api/v1/playlists")
    assert resp.status_code == 401


def test_weekly_cadence_requires_day_of_week(base_client: TestClient, db_session) -> None:
    """Validation: weekly cadence must include refresh_day_of_week."""
    user = _make_user(db_session)
    _set_user(user)
    resp = base_client.post(
        "/api/v1/playlists",
        json={"name": "Weekly", "refresh_cadence": "weekly", "rows": []},
    )
    assert resp.status_code == 422


def test_weekly_cadence_with_day_succeeds(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)
    resp = base_client.post(
        "/api/v1/playlists",
        json={
            "name": "Weekly Fri",
            "refresh_cadence": "weekly",
            "refresh_day_of_week": 5,
            "rows": [],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["refresh_day_of_week"] == 5


# ---------------------------------------------------------------------------
# Row append / remove / patch (Phase 06 Plan 02 — D-20)
# ---------------------------------------------------------------------------


def _create_empty_playlist(base_client: TestClient) -> str:
    resp = base_client.post(
        "/api/v1/playlists",
        json={"name": "Row Ops", "rows": []},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_append_row(base_client: TestClient, db_session) -> None:
    """POST /rows appends one series row with create defaults."""
    user = _make_user(db_session)
    _set_user(user)
    playlist_id = _create_empty_playlist(base_client)

    append = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert append.status_code in (200, 201), append.text
    body = append.json()
    assert len(body["rows"]) == 1
    assert body["rows"][0]["series_id"] == SERIES_ID_A
    assert body["rows"][0]["mode"] == "ordered"
    assert body["rows"][0]["completion_policy"] == "remove"

    detail = base_client.get(f"/api/v1/playlists/{playlist_id}")
    assert detail.status_code == 200
    assert len(detail.json()["rows"]) == 1


def test_append_row_duplicate_409(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)
    playlist_id = _create_empty_playlist(base_client)

    first = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert first.status_code in (200, 201), first.text

    second = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert second.status_code == 409


def test_remove_row(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)
    playlist_id = _create_empty_playlist(base_client)

    append = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert append.status_code in (200, 201), append.text

    delete = base_client.delete(f"/api/v1/playlists/{playlist_id}/rows/{SERIES_ID_A}")
    assert delete.status_code == 204

    detail = base_client.get(f"/api/v1/playlists/{playlist_id}")
    assert detail.status_code == 200
    assert detail.json()["rows"] == []


def test_patch_row_mode(base_client: TestClient, db_session) -> None:
    user = _make_user(db_session)
    _set_user(user)
    playlist_id = _create_empty_playlist(base_client)

    append = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert append.status_code in (200, 201), append.text

    patch = base_client.patch(
        f"/api/v1/playlists/{playlist_id}/rows/{SERIES_ID_A}",
        json={"mode": "disordered"},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["rows"][0]["mode"] == "disordered"

    detail = base_client.get(f"/api/v1/playlists/{playlist_id}")
    assert detail.status_code == 200
    assert detail.json()["rows"][0]["mode"] == "disordered"


def test_append_row_cross_user_404(base_client: TestClient, db_session) -> None:
    """D-18: Cross-user row append returns 404."""
    user_a = _make_user(db_session, "user-a")
    user_b = _make_user(db_session, "user-b")

    _set_user(user_a)
    playlist_id = _create_empty_playlist(base_client)

    _set_user(user_b)
    resp = base_client.post(
        f"/api/v1/playlists/{playlist_id}/rows",
        json={"series_id": SERIES_ID_A},
    )
    assert resp.status_code == 404
