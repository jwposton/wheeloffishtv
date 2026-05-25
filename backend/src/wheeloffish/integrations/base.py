from typing import Protocol

from wheeloffish.domain.dto import Episode, Library, PagedSeries


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
