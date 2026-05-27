import asyncio
import time
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import APP_USER_ID, seed_cached_libraries, seed_cached_series, seed_series_in_scope
from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect

from wheeloffish.api.deps import get_app_user_id, get_current_user, get_db
from wheeloffish.core.config import get_settings
from wheeloffish.core.resume import ResumeService
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.dto import Episode, Library, PagedSeries, Series
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.plex.client import PlexProvider
from wheeloffish.main import app

SECOND_APP_USER_ID = "00000000-0000-4000-8000-000000000002"


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
                in_scope=True,
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


def _episode(
    connection_id: str,
    native_guid: str,
    season: int,
    index: int,
    *,
    percent: float = 0.0,
    played: bool = False,
    title: str | None = None,
) -> Episode:
    return Episode(
        id=format_composite_id(connection_id, "plex", native_guid),
        title=title or f"S{season}E{index}",
        season_index=season,
        episode_index=index,
        duration_ms=3_600_000,
        percent_watched=percent,
        provider_marked_played=played,
    )


def _mock_episode_provider(
    connection_id: str,
    *,
    episodes: list[Episode],
    on_deck: Episode | None = None,
) -> MagicMock:
    provider = MagicMock()
    provider.ping = AsyncMock(return_value=None)
    provider.provider_user_id = "provider-user-1"
    provider.list_episodes = AsyncMock(return_value=episodes)
    provider.get_on_deck_episode = AsyncMock(return_value=on_deck)
    return provider


def _skip_ahead_episodes(connection_id: str) -> tuple[list[Episode], Episode]:
    episodes = [
        _episode(connection_id, "s1e1", 1, 1, percent=100, played=True),
        _episode(connection_id, "s1e2", 1, 2, percent=100, played=True),
        _episode(connection_id, "s1e3", 1, 3, percent=100, played=True),
        _episode(connection_id, "s1e4", 1, 4, percent=100, played=True),
        _episode(connection_id, "s1e5", 1, 5),
        _episode(connection_id, "s2e1", 2, 1),
    ]
    on_deck = _episode(connection_id, "s2e1", 2, 1)
    return episodes, on_deck


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
        "wheeloffish.core.catalog_sync.build_plex_provider_for_user",
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
    monkeypatch: pytest.MonkeyPatch,
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

    provider = _mock_library_list_provider(connection.id)
    monkeypatch.setattr(
        "wheeloffish.core.catalog_sync._build_provider",
        lambda *args, **kwargs: provider,
    )

    response = await catalog_client.get(f"/api/v1/connections/{connection.id}/libraries")

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 2
    in_scope_only = [lib for lib in libraries if lib["in_scope"]]
    assert len(in_scope_only) == 1
    assert in_scope_only[0]["native_id"] == "1"

    scope_response = await catalog_client.put(
        f"/api/v1/connections/{connection.id}/library-scope",
        json={"in_scope_library_native_ids": ["2"]},
    )
    assert scope_response.status_code == 200
    scoped = {lib["native_id"]: lib["in_scope"] for lib in scope_response.json()["libraries"]}
    assert scoped["1"] is False
    assert scoped["2"] is True

    libraries_response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/libraries"
    )
    in_scope_after = [lib for lib in libraries_response.json() if lib["in_scope"]]
    assert len(in_scope_after) == 1
    assert in_scope_after[0]["native_id"] == "2"


@pytest.mark.asyncio
async def test_episodes_live_fetch(
    catalog_client,
    connection_factory,
    db_session,
    db_engine,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(db_session, connection.id, series_id)
    episodes = [
        _episode(connection.id, "ep-1", 1, 1),
        _episode(connection.id, "ep-2", 1, 2, percent=100, played=True),
        _episode(connection.id, "ep-3", 1, 3, percent=50),
    ]
    provider = _mock_episode_provider(connection.id, episodes=episodes)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/episodes"
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["episodes"]) == 3
    assert body["episodes"][0]["percent_watched"] == 0.0
    assert body["episodes"][0]["provider_marked_played"] is False
    assert body["episodes"][1]["provider_marked_played"] is True
    assert body["episodes"][2]["percent_watched"] == 50.0
    provider.list_episodes.assert_awaited_once_with(
        series_id,
        rating_key=None,
        library_native_id="1",
    )

    inspector = inspect(db_engine)
    assert not any("episode" in name for name in inspector.get_table_names())


@pytest.mark.asyncio
async def test_resume_matches_resume_service(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(db_session, connection.id, series_id)
    episodes = [
        _episode(connection.id, "s1e1", 1, 1, percent=100, played=True),
        _episode(connection.id, "s1e2", 1, 2, percent=50),
        _episode(connection.id, "s1e3", 1, 3),
    ]
    provider = _mock_episode_provider(connection.id, episodes=episodes, on_deck=None)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/resume"
        )

    assert response.status_code == 200
    expected = ResumeService().compute(series_id, episodes, None)
    body = response.json()
    assert body["episode_id"] == expected.episode_id
    assert body["source"] == expected.source
    assert body["season_index"] == expected.season_index
    assert body["episode_index"] == expected.episode_index


@pytest.mark.asyncio
async def test_resume_on_deck_ahead(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(db_session, connection.id, series_id)
    episodes, on_deck = _skip_ahead_episodes(connection.id)
    provider = _mock_episode_provider(connection.id, episodes=episodes, on_deck=on_deck)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/resume"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "on_deck"
    assert body["episode_id"] == on_deck.id


@pytest.mark.asyncio
async def test_resume_per_user_isolation(
    catalog_client,
    connection_factory,
    db_session,
    vault,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(db_session, connection.id, series_id)
    seed_series_in_scope(
        db_session,
        connection.id,
        series_id,
        app_user_id=SECOND_APP_USER_ID,
    )

    user1_episodes = [
        _episode(connection.id, "s1e1", 1, 1),
        _episode(connection.id, "s1e2", 1, 2, percent=100, played=True),
    ]
    user2_episodes = [
        _episode(connection.id, "s1e1", 1, 1, percent=100, played=True),
        _episode(connection.id, "s1e2", 1, 2, percent=50),
    ]

    now = datetime.now(UTC)
    db_session.add(
        UserMediaLink(
            id=str(uuid.uuid4()),
            app_user_id=SECOND_APP_USER_ID,
            connection_id=connection.id,
            provider_user_id="provider-user-2",
            provider_username=None,
            linked_at=now,
        )
    )
    db_session.commit()
    vault.store_plex_user_credentials(
        connection.id,
        SECOND_APP_USER_ID,
        "second-user-token",
        "second-client-id",
    )

    def build_provider_side_effect(_db, _vault, connection_obj, app_user_id, **_kwargs):
        episodes = user1_episodes if app_user_id == APP_USER_ID else user2_episodes
        return _mock_episode_provider(connection_obj.id, episodes=episodes)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        side_effect=build_provider_side_effect,
    ):
        app.dependency_overrides[get_app_user_id] = lambda: APP_USER_ID
        response_user1 = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/resume"
        )
        app.dependency_overrides[get_app_user_id] = lambda: SECOND_APP_USER_ID
        response_user2 = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/resume"
        )

    assert response_user1.status_code == 200
    assert response_user2.status_code == 200
    assert response_user1.json()["episode_id"] != response_user2.json()["episode_id"]
    assert response_user1.json()["episode_id"] == user1_episodes[0].id
    assert response_user2.json()["episode_id"] == user2_episodes[1].id


def _mock_library_list_provider(connection_id: str) -> MagicMock:
    provider = MagicMock()
    provider.list_libraries = AsyncMock(
        return_value=[
            Library(
                id="ignored",
                title="In Scope TV",
                native_id="1",
                connection_id=connection_id,
                provider="plex",
                in_scope=True,
            ),
            Library(
                id="ignored",
                title="Out of Scope TV",
                native_id="2",
                connection_id=connection_id,
                provider="plex",
                in_scope=False,
            ),
        ]
    )
    return provider


@pytest.mark.asyncio
async def test_get_libraries_includes_in_scope_flag(
    catalog_client, connection_factory, db_session, monkeypatch: pytest.MonkeyPatch
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
    monkeypatch.setattr(
        "wheeloffish.core.catalog_sync._build_provider",
        lambda *args, **kwargs: _mock_library_list_provider(connection.id),
    )

    response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/libraries"
    )

    assert response.status_code == 200
    libraries = response.json()
    assert len(libraries) == 2
    in_scope_ids = {lib["native_id"]: lib["in_scope"] for lib in libraries}
    assert in_scope_ids["1"] is True
    assert in_scope_ids["2"] is False


@pytest.mark.asyncio
async def test_library_scope_put_succeeds(
    catalog_client, connection_factory, db_session
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

    response = await catalog_client.put(
        f"/api/v1/connections/{connection.id}/library-scope",
        json={"in_scope_library_native_ids": ["2"]},
    )

    assert response.status_code == 200
    scoped = response.json()["libraries"]
    assert len(scoped) == 2
    by_id = {lib["native_id"]: lib["in_scope"] for lib in scoped}
    assert by_id["1"] is False
    assert by_id["2"] is True


@pytest.mark.asyncio
async def test_series_artwork_serves_local_cache(
    catalog_client,
    connection_factory,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("WOF_ARTWORK_CACHE_DIR", str(tmp_path))
    get_settings.cache_clear()

    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    from wheeloffish.core.media_artwork import artwork_cache_path, write_cached_artwork
    from wheeloffish.db.models.cached_series import CachedSeries

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=APP_USER_ID,
            connection_id=connection.id,
            library_native_id="1",
            native_id="guid-123",
            title="Cached Show",
            thumb_url="/library/metadata/1001/thumb/abc",
            synced_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    cache_path = artwork_cache_path(str(tmp_path), APP_USER_ID, connection.id, series_id)
    write_cached_artwork(cache_path, b"cached-poster")

    response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/series/{series_id}/artwork"
    )

    assert response.status_code == 200
    assert response.content == b"cached-poster"


@pytest.mark.asyncio
async def test_series_artwork_lazy_fetch_with_user_token(
    catalog_client,
    connection_factory,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("WOF_ARTWORK_CACHE_DIR", str(tmp_path))
    get_settings.cache_clear()

    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    from wheeloffish.db.models.cached_series import CachedSeries

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=APP_USER_ID,
            connection_id=connection.id,
            library_native_id="1",
            native_id="guid-123",
            title="Cached Show",
            thumb_url="/library/metadata/1001/thumb/abc",
            synced_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    user_provider = PlexProvider(
        base_url="https://plex.example.com",
        token="test-token",
        client_identifier="test-client",
        connection_id=connection.id,
        verify_ssl=True,
    )
    user_provider.fetch_artwork = AsyncMock(return_value=(b"fresh-poster", "image/jpeg"))

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=user_provider,
    ):
        response = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/artwork"
        )

    assert response.status_code == 200
    assert response.content == b"fresh-poster"
    user_provider.fetch_artwork.assert_awaited_once_with("/library/metadata/1001/thumb/abc")


@pytest.mark.asyncio
async def test_get_series_detail(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(
        db_session,
        connection.id,
        series_id,
        title="Detail Show",
        provider_metadata={"ratingKey": "1001"},
    )

    response = await catalog_client.get(
        f"/api/v1/connections/{connection.id}/series/{series_id}"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == series_id
    assert body["title"] == "Detail Show"
    assert body["thumb_url"] is not None


@pytest.mark.asyncio
async def test_resume_uses_cached_rating_key(
    catalog_client,
    connection_factory,
    db_session,
) -> None:
    connection = await connection_factory()
    series_id = format_composite_id(connection.id, "plex", "guid-123")
    seed_series_in_scope(
        db_session,
        connection.id,
        series_id,
        provider_metadata={"ratingKey": "999"},
    )

    episodes = [
        _episode(connection.id, "s1e1", 1, 1, percent=50),
    ]
    provider = MagicMock(spec=PlexProvider)
    provider.list_episodes = AsyncMock(return_value=episodes)
    provider.get_on_deck_episode = AsyncMock(return_value=None)

    with patch(
        "wheeloffish.api.routes.catalog.build_provider_for_user",
        return_value=provider,
    ):
        response = await catalog_client.get(
            f"/api/v1/connections/{connection.id}/series/{series_id}/resume"
        )

    assert response.status_code == 200
    provider.list_episodes.assert_awaited_once_with(
        series_id,
        rating_key="999",
        library_native_id="1",
    )
    provider.get_on_deck_episode.assert_awaited_once_with(
        series_id,
        rating_key="999",
        library_native_id="1",
    )
    assert response.json()["episode_id"] == episodes[0].id
