import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import seed_cached_libraries, seed_cached_series
from httpx import ASGITransport, AsyncClient

from wheeloffish.api.deps import get_db
from wheeloffish.core.config import get_settings
from wheeloffish.domain.dto import Library, PagedSeries, Series
from wheeloffish.main import app


@pytest.fixture
def sync_task_collector(monkeypatch: pytest.MonkeyPatch):
    tasks: list[asyncio.Task] = []
    original_create_task = asyncio.create_task

    def collect(coro):
        task = original_create_task(coro)
        tasks.append(task)
        return task

    monkeypatch.setattr(asyncio, "create_task", collect)
    return tasks


@pytest.fixture
async def catalog_client(db_engine, db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WOF_ENABLED_PROVIDERS", "plex,jellyfin")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def _mock_sync_provider(*, series_count: int = 1) -> MagicMock:
    provider = MagicMock()
    provider.ping = AsyncMock(return_value=None)
    provider.provider_user_id = "provider-user-1"
    provider.list_libraries = AsyncMock(
        return_value=[
            Library(
                id="ignored",
                title="TV Shows",
                native_id="1",
                connection_id="ignored",
                provider="plex",
            )
        ]
    )

    async def list_series(library_native_id: str, *, page: int, limit: int, q: str | None):
        start = (page - 1) * limit
        end = min(start + limit, series_count)
        items = [
            Series(
                id=f"series-{index}",
                title=f"Synced Show {index}",
                native_id=f"native-{index}",
                library_native_id=library_native_id,
                connection_id="pending",
                provider="plex",
            )
            for index in range(start, end)
        ]
        return PagedSeries(items=items, page=page, limit=limit, total=series_count)

    provider.list_series = AsyncMock(side_effect=list_series)
    return provider


@pytest.mark.asyncio
async def test_series_page(catalog_client, connection_factory, db_session) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    seed_cached_series(db_session, connection.id, 120, library_native_id="1")

    response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/series",
        params={"page": 1, "limit": 50},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 120
    assert len(body["items"]) == 50
    assert body["page"] == 1
    assert body["limit"] == 50
    assert "sync" in body


@pytest.mark.asyncio
async def test_series_search(catalog_client, connection_factory, db_session) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    seed_cached_series(db_session, connection.id, 5, library_native_id="1", title_prefix="Alpha")
    seed_cached_series(
        db_session,
        connection.id,
        3,
        library_native_id="1",
        title_prefix="Beta Filter",
        start_index=100,
    )

    response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/series",
        params={"q": "Filter"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert all("Filter" in item["title"] for item in body["items"])


@pytest.mark.asyncio
async def test_sync_status(
    catalog_client,
    connection_factory,
    db_session,
    sync_task_collector,
) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    release_sync = asyncio.Event()
    provider = _mock_sync_provider(series_count=1)

    async def delayed_list_series(
        library_native_id: str, *, page: int, limit: int, q: str | None
    ):
        await release_sync.wait()
        return PagedSeries(
            items=[
                Series(
                    id=f"{connection.id}:plex:native-0",
                    title="Synced Show 0",
                    native_id="native-0",
                    library_native_id=library_native_id,
                    connection_id=connection.id,
                    provider="plex",
                )
            ],
            page=page,
            limit=limit,
            total=1,
        )

    provider.list_series = AsyncMock(side_effect=delayed_list_series)

    with patch(
        "wheeloffish.core.catalog_sync.build_provider_for_connection",
        return_value=provider,
    ):
        sync_response = await catalog_client.post(f"/api/v1/connections/{connection.id}/sync")

    assert sync_response.status_code == 202
    assert sync_response.json()["status"] == "running"

    running_response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/sync/status"
    )
    assert running_response.status_code == 200
    assert running_response.json()["status"] == "running"

    release_sync.set()
    if sync_task_collector:
        await asyncio.gather(*sync_task_collector)

    complete_response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/sync/status"
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "complete"


@pytest.mark.asyncio
async def test_sync_non_blocking(catalog_client, connection_factory, db_session) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )

    async def slow_sync(_connection_id: str, _app_user_id: str) -> None:
        await asyncio.sleep(10)

    with patch("wheeloffish.core.catalog_sync.run_chunked_sync", side_effect=slow_sync):
        start = time.perf_counter()
        response = await catalog_client.post(f"/api/v1/connections/{connection.id}/sync")
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 202
    assert response.json()["status"] == "running"
    assert elapsed_ms < 500


@pytest.mark.asyncio
async def test_session_catalog_refresh(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )

    with patch("wheeloffish.core.catalog_sync.run_chunked_sync", new=AsyncMock(return_value=None)):
        start = time.perf_counter()
        response = await catalog_client.post("/api/v1/session/catalog-refresh")
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 202
    assert elapsed_ms < 500
    body = response.json()
    assert connection.id in body["sync"]
    assert body["sync"][connection.id]["status"] == "running"


@pytest.mark.asyncio
async def test_library_scope_filter(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [
            {"native_id": "1", "title": "In Scope TV", "in_scope": True},
            {"native_id": "2", "title": "Out of Scope TV", "in_scope": False},
        ],
    )

    response = await catalog_client.get(f"/api/v1/connections/{connection.id}/libraries")

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 1
    assert libraries[0]["native_id"] == "1"
    assert libraries[0]["title"] == "In Scope TV"

    scope_response = await catalog_client.put(
        f"/api/v1/admin/connections/{connection.id}/library-scope",
        json={"in_scope_library_native_ids": ["2"]},
    )
    assert scope_response.status_code == 200
    scoped = scope_response.json()["libraries"]
    assert len(scoped) == 1
    assert scoped[0]["native_id"] == "2"

    libraries_response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/libraries"
    )
    assert len(libraries_response.json()) == 1
    assert libraries_response.json()[0]["native_id"] == "2"
