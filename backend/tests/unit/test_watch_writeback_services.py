from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.base import (
    WatchAction,
    WatchMutationRequest,
    WatchScope,
)
from wheeloffish.integrations.errors import ProviderUnauthorized
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.plex.client import PlexProvider


@pytest.mark.parametrize("scope", [WatchScope.EPISODE, WatchScope.SEASON, WatchScope.SERIES])
@pytest.mark.parametrize("action", [WatchAction.WATCHED, WatchAction.UNWATCHED])
def test_watch_mutation_request_accepts_scope_and_action(scope: WatchScope, action: WatchAction):
    request = WatchMutationRequest(
        target_id="conn-a:plex:item-1",
        scope=scope,
        action=action,
    )

    assert request.scope is scope
    assert request.action is action
    assert request.target_id == "conn-a:plex:item-1"


@pytest.mark.parametrize("scope", ["bad", "", "serieses"])
def test_watch_mutation_request_rejects_invalid_scope(scope: str):
    with pytest.raises(ValueError):
        WatchMutationRequest.from_values(
            target_id="conn-a:plex:item-1",
            scope=scope,
            action="watched",
        )


@pytest.mark.parametrize("action", ["seen", "", "watch"])
def test_watch_mutation_request_rejects_invalid_action(action: str):
    with pytest.raises(ValueError):
        WatchMutationRequest.from_values(
            target_id="conn-a:plex:item-1",
            scope="episode",
            action=action,
        )


def _plex_provider() -> PlexProvider:
    return PlexProvider(
        base_url="https://plex.example.com",
        token="token",
        client_identifier="wof",
        connection_id="conn-plex",
        verify_ssl=True,
    )


def _jellyfin_provider() -> JellyfinProvider:
    return JellyfinProvider(
        base_url="https://jellyfin.example.com",
        token="token",
        user_id="user-1",
        connection_id="conn-jf",
        verify_ssl=True,
    )


@pytest.mark.asyncio
async def test_plex_mutate_watch_state_resolves_rating_key_before_scrobble():
    provider = _plex_provider()
    request = WatchMutationRequest(
        target_id=format_composite_id("conn-plex", "plex", "plex://episode-guid"),
        scope=WatchScope.EPISODE,
        action=WatchAction.WATCHED,
    )

    with (
        patch(
            "wheeloffish.integrations.plex.client.resolve_guid_to_rating_key",
            new=AsyncMock(return_value="12345"),
        ) as mock_resolve,
        patch.object(provider, "_request", new=AsyncMock()) as mock_request,
    ):
        await provider.mutate_watch_state(request)

    mock_resolve.assert_awaited_once()
    mock_request.assert_awaited_once_with(
        "GET",
        "/:/scrobble",
        params={"identifier": "com.plexapp.plugins.library", "key": "12345"},
    )


@pytest.mark.asyncio
async def test_jellyfin_mutate_watch_state_uses_user_played_items_routes():
    provider = _jellyfin_provider()
    watched = WatchMutationRequest(
        target_id=format_composite_id("conn-jf", "jellyfin", "season-1"),
        scope=WatchScope.SEASON,
        action=WatchAction.WATCHED,
    )
    unwatched = WatchMutationRequest(
        target_id=format_composite_id("conn-jf", "jellyfin", "series-1"),
        scope=WatchScope.SERIES,
        action=WatchAction.UNWATCHED,
    )

    with patch.object(provider, "_request", new=AsyncMock()) as mock_request:
        await provider.mutate_watch_state(watched)
        await provider.mutate_watch_state(unwatched)

    assert mock_request.await_args_list[0].args == ("POST", "/UserPlayedItems/season-1")
    assert mock_request.await_args_list[1].args == ("DELETE", "/UserPlayedItems/series-1")


@pytest.mark.asyncio
async def test_mutate_watch_state_does_not_swallow_provider_auth_errors():
    provider = _plex_provider()
    request = WatchMutationRequest(
        target_id=format_composite_id("conn-plex", "plex", "12345"),
        scope=WatchScope.EPISODE,
        action=WatchAction.WATCHED,
    )

    with patch.object(provider, "_request", new=AsyncMock(side_effect=ProviderUnauthorized())):
        with pytest.raises(ProviderUnauthorized):
            await provider.mutate_watch_state(request)
