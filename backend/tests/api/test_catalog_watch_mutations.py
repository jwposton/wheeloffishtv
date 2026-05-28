from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import APP_USER_ID
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient

from wheeloffish.api.deps import get_app_user_id, get_current_user, get_db
from wheeloffish.core.config import get_settings
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.integrations.errors import ProviderNotFound
from wheeloffish.main import app


@pytest.fixture
async def catalog_client(db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex,jellyfin")
    get_settings.cache_clear()

    regular_user = AppUser(
        id=APP_USER_ID,
        provider_user_id="catalog-user",
        provider_username="viewer",
    )
    db_session.add(regular_user)
    db_session.commit()
    db_session.refresh(regular_user)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: regular_user
    app.dependency_overrides[get_app_user_id] = lambda: APP_USER_ID
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("scope", ["episode", "season", "series"])
@pytest.mark.parametrize("action", ["watched", "unwatched"])
async def test_watch_mutation_accepts_scope_and_action(
    catalog_client,
    connection_factory,
    scope: str,
    action: str,
) -> None:
    connection = await connection_factory()
    target_id = f"{connection.id}:plex:rating-key-1"
    provider = MagicMock()
    provider.mutate_watch_state = AsyncMock(return_value=None)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.post(
            f"/api/v1/connections/{connection.id}/watch-state",
            json={"target_id": target_id, "scope": scope, "action": action},
        )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "succeeded",
        "scope": scope,
        "updated_count": 1,
        "failed_count": 0,
        "failed_ids": [],
        "error_code": None,
        "message": "Watch state updated",
    }
    provider.mutate_watch_state.assert_awaited_once()


@pytest.mark.asyncio
async def test_watch_mutation_rejects_invalid_scope_and_action(
    catalog_client,
    connection_factory,
) -> None:
    connection = await connection_factory()
    target_id = f"{connection.id}:plex:rating-key-1"

    bad_scope = await catalog_client.post(
        f"/api/v1/connections/{connection.id}/watch-state",
        json={"target_id": target_id, "scope": "show", "action": "watched"},
    )
    assert bad_scope.status_code == 422

    bad_action = await catalog_client.post(
        f"/api/v1/connections/{connection.id}/watch-state",
        json={"target_id": target_id, "scope": "episode", "action": "toggle"},
    )
    assert bad_action.status_code == 422


@pytest.mark.asyncio
async def test_watch_mutation_maps_unauthorized_provider_session(
    catalog_client,
    connection_factory,
) -> None:
    connection = await connection_factory()
    target_id = f"{connection.id}:plex:rating-key-1"

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        side_effect=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unauthorized", "message": "No token for user"},
        ),
    ):
        response = await catalog_client.post(
            f"/api/v1/connections/{connection.id}/watch-state",
            json={"target_id": target_id, "scope": "episode", "action": "watched"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "scope": "episode",
        "updated_count": 0,
        "failed_count": 1,
        "failed_ids": [target_id],
        "error_code": "auth",
        "message": "Provider session is not authorized",
    }


@pytest.mark.asyncio
async def test_watch_mutation_rejects_cross_connection_targets_as_forbidden(
    catalog_client,
    connection_factory,
) -> None:
    connection = await connection_factory()
    other = await connection_factory(provider_type="jellyfin")
    target_id = f"{other.id}:jellyfin:item-1"

    response = await catalog_client.post(
        f"/api/v1/connections/{connection.id}/watch-state",
        json={"target_id": target_id, "scope": "episode", "action": "watched"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "scope": "episode",
        "updated_count": 0,
        "failed_count": 1,
        "failed_ids": [target_id],
        "error_code": "forbidden",
        "message": "Mutation target is outside this connection scope",
    }


@pytest.mark.asyncio
async def test_watch_mutation_returns_deterministic_success_payload_for_bulk_targets(
    catalog_client,
    connection_factory,
) -> None:
    connection = await connection_factory()
    target_ids = [
        f"{connection.id}:plex:rating-key-1",
        f"{connection.id}:plex:rating-key-2",
    ]
    provider = MagicMock()
    provider.mutate_watch_state = AsyncMock(return_value=None)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.post(
            f"/api/v1/connections/{connection.id}/watch-state",
            json={
                "target_ids": target_ids,
                "scope": "episode",
                "action": "watched",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "succeeded",
        "scope": "episode",
        "updated_count": 2,
        "failed_count": 0,
        "failed_ids": [],
        "error_code": None,
        "message": "Watch state updated",
    }
    assert provider.mutate_watch_state.await_count == 2


@pytest.mark.asyncio
async def test_watch_mutation_returns_partial_payload_for_bulk_failure(
    catalog_client,
    connection_factory,
) -> None:
    connection = await connection_factory()
    target_ids = [
        f"{connection.id}:plex:rating-key-1",
        f"{connection.id}:plex:missing-rating-key",
    ]
    provider = MagicMock()

    async def mutate_side_effect(request):
        if request.target_id.endswith("missing-rating-key"):
            raise ProviderNotFound()
        return None

    provider.mutate_watch_state = AsyncMock(side_effect=mutate_side_effect)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.post(
            f"/api/v1/connections/{connection.id}/watch-state",
            json={
                "target_ids": target_ids,
                "scope": "episode",
                "action": "watched",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "partial",
        "scope": "episode",
        "updated_count": 1,
        "failed_count": 1,
        "failed_ids": [target_ids[1]],
        "error_code": "not_found",
        "message": "Watch state updated with partial failures",
    }
