import json
import re
from pathlib import Path

import pytest
import respx
from httpx import Response

from wheeloffish.domain.dto import Episode, Library, Series
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.errors import ProviderUnauthorized
from wheeloffish.integrations.jellyfin.auth import authenticate, validate_token
from wheeloffish.integrations.jellyfin.client import JellyfinProvider

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())

BASE_URL = "https://jellyfin.example.com"
CONNECTION_ID = "conn-test-uuid"
USER_ID = "22222222-3333-4444-8555-666666666666"
TOKEN = "SANITIZED_JELLYFIN_TOKEN"


def _provider() -> JellyfinProvider:
    return JellyfinProvider(
        base_url=BASE_URL,
        token=TOKEN,
        user_id=USER_ID,
        connection_id=CONNECTION_ID,
        verify_ssl=True,
    )


@pytest.mark.asyncio
@respx.mock
async def test_auth_authenticate_by_name() -> None:
    route = respx.post(f"{BASE_URL}/Users/AuthenticateByName").mock(
        return_value=Response(200, json=load_fixture("jellyfin/authenticate"))
    )

    token, user_id, username = await authenticate(
        BASE_URL,
        "testuser",
        "secret-password",
        verify_ssl=True,
    )

    assert route.called
    assert token == TOKEN
    assert user_id == USER_ID
    assert username == "testuser"
    request_body = route.calls[0].request.content.decode()
    assert "secret-password" in request_body
    assert TOKEN not in request_body


@pytest.mark.asyncio
@respx.mock
async def test_auth_unauthorized() -> None:
    respx.post(f"{BASE_URL}/Users/AuthenticateByName").mock(return_value=Response(401))

    with pytest.raises(ProviderUnauthorized):
        await authenticate(BASE_URL, "testuser", "wrong-password", verify_ssl=True)


@pytest.mark.asyncio
async def test_auth_rejects_api_key_username() -> None:
    api_key = "0123456789abcdef0123456789abcdef"
    with pytest.raises(ProviderUnauthorized, match="API key"):
        await authenticate(BASE_URL, api_key, "ignored", verify_ssl=True)


@pytest.mark.asyncio
@respx.mock
async def test_auth_validate_token() -> None:
    respx.get(f"{BASE_URL}/Users/Me").mock(
        return_value=Response(
            200,
            json={"Id": USER_ID, "Name": "testuser"},
        )
    )

    user = await validate_token(BASE_URL, TOKEN, verify_ssl=True)
    assert user["Id"] == USER_ID
    assert user["Name"] == "testuser"


@pytest.mark.asyncio
@respx.mock
async def test_list_libraries() -> None:
    respx.get(f"{BASE_URL}/Library/MediaFolders").mock(
        return_value=Response(200, json=load_fixture("jellyfin/media_folders"))
    )

    libraries = await _provider().list_libraries()

    assert len(libraries) == 1
    assert libraries[0].title == "TV Shows"
    assert libraries[0].native_id == "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee"
    assert ":jellyfin:" in libraries[0].id


@pytest.mark.asyncio
@respx.mock
async def test_list_series_paged() -> None:
    library_id = "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee"
    respx.get(re.compile(rf"{BASE_URL}/Items.*")).mock(
        return_value=Response(200, json=load_fixture("jellyfin/series_items"))
    )

    page = await _provider().list_series(library_id, page=1, limit=50, q=None)

    assert page.total == 2
    assert len(page.items) == 2
    assert page.items[0].title == "Fictional Show"
    assert ":jellyfin:" in page.items[0].id
    assert "11111111-2222-4333-8444-555555555555" in page.items[0].id


@pytest.mark.asyncio
@respx.mock
async def test_list_episodes_watch_fields() -> None:
    series_id = format_composite_id(
        CONNECTION_ID,
        "jellyfin",
        "11111111-2222-4333-8444-555555555555",
    )
    respx.get(
        f"{BASE_URL}/Shows/11111111-2222-4333-8444-555555555555/Episodes"
    ).mock(return_value=Response(200, json=load_fixture("jellyfin/episodes")))

    episodes = await _provider().list_episodes(series_id)

    assert len(episodes) == 4
    assert episodes[0].percent_watched == 0.0
    assert episodes[0].provider_marked_played is False
    assert episodes[1].provider_marked_played is True
    assert episodes[2].percent_watched == pytest.approx(50.0)
    assert episodes[2].provider_marked_played is False


@pytest.mark.asyncio
@respx.mock
async def test_get_on_deck_episode() -> None:
    series_id = format_composite_id(
        CONNECTION_ID,
        "jellyfin",
        "11111111-2222-4333-8444-555555555555",
    )
    respx.get(re.compile(rf"{BASE_URL}/Shows/NextUp.*")).mock(
        return_value=Response(200, json=load_fixture("jellyfin/next_up"))
    )

    episode = await _provider().get_on_deck_episode(series_id)

    assert episode is not None
    assert episode.title == "Season Two Premiere"
    assert ":jellyfin:" in episode.id


def test_dto_shape_matches_plex() -> None:
    assert Library.model_fields.keys() == Library.model_fields.keys()
    assert Series.model_fields.keys() == Series.model_fields.keys()
    assert Episode.model_fields.keys() == Episode.model_fields.keys()

    library = Library(
        id=f"{CONNECTION_ID}:jellyfin:test",
        title="TV Shows",
        native_id="lib-1",
        connection_id=CONNECTION_ID,
        provider="jellyfin",
    )
    series = Series(
        id=f"{CONNECTION_ID}:jellyfin:series-1",
        title="Show",
        native_id="series-1",
        library_native_id="lib-1",
        connection_id=CONNECTION_ID,
        provider="jellyfin",
    )
    episode = Episode(
        id=f"{CONNECTION_ID}:jellyfin:ep-1",
        title="Pilot",
        season_index=1,
        episode_index=1,
        duration_ms=3600000,
        percent_watched=0.0,
    )

    assert isinstance(library, Library)
    assert isinstance(series, Series)
    assert isinstance(episode, Episode)
    assert set(Library.model_fields) == {
        "id",
        "title",
        "native_id",
        "connection_id",
        "provider",
        "in_scope",
    }
    assert set(Episode.model_fields) == {
        "id",
        "title",
        "season_index",
        "episode_index",
        "duration_ms",
        "percent_watched",
        "provider_marked_played",
        "part_index",
        "multipart_group_id",
        "is_special",
        "special_for_season",
    }
