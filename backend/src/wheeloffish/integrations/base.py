from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from wheeloffish.domain.dto import Episode, Library, PagedSeries


class WatchScope(StrEnum):
    EPISODE = "episode"
    SEASON = "season"
    SERIES = "series"


class WatchAction(StrEnum):
    WATCHED = "watched"
    UNWATCHED = "unwatched"


@dataclass(frozen=True, slots=True)
class WatchMutationRequest:
    target_id: str
    scope: WatchScope
    action: WatchAction

    @classmethod
    def from_values(cls, *, target_id: str, scope: str, action: str) -> "WatchMutationRequest":
        try:
            scope_value = WatchScope(scope)
        except ValueError as err:
            raise ValueError(f"Unsupported watch scope: {scope!r}") from err
        try:
            action_value = WatchAction(action)
        except ValueError as err:
            raise ValueError(f"Unsupported watch action: {action!r}") from err
        return cls(target_id=target_id, scope=scope_value, action=action_value)


class MediaProvider(Protocol):
    async def ping(self) -> None: ...

    async def list_libraries(self) -> list[Library]: ...

    async def list_series(
        self,
        library_native_id: str,
        *,
        page: int,
        limit: int,
        q: str | None,
    ) -> PagedSeries: ...

    async def list_episodes(self, series_composite_id: str) -> list[Episode]: ...

    async def get_on_deck_episode(self, series_composite_id: str) -> Episode | None: ...

    async def mutate_watch_state(self, request: WatchMutationRequest) -> None: ...
