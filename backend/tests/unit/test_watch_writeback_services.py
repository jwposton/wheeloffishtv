from __future__ import annotations

import pytest

from wheeloffish.integrations.base import (
    WatchAction,
    WatchMutationRequest,
    WatchScope,
)


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
