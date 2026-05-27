from typing import Any

import httpx

from wheeloffish.domain.dto import Episode, Library, PagedSeries
from wheeloffish.integrations.errors import (
    ProviderError,
    ProviderNotFound,
    ProviderSSLError,
    ProviderUnauthorized,
    ProviderUnreachable,
)
from wheeloffish.integrations.jellyfin.auth import _authorization_header
from wheeloffish.integrations.jellyfin.mappers import (
    map_episode,
    map_library,
    map_series,
    parse_series_id,
)

PROVIDER = "jellyfin"
JELLYFIN_REQUEST_TIMEOUT_SECONDS = 60.0


def _is_safe_jellyfin_image_path(path: str) -> bool:
    """Reject path traversal; require ``/Items/.../Images/<type>`` (optional ``?tag=``)."""
    if ".." in path or not path.startswith("/Items/"):
        return False
    head = path.split("?", 1)[0]
    if "/Images/" not in head:
        return False
    parts = [p for p in head.split("/") if p]
    # Items, {id}, Images, {type}
    return len(parts) >= 4 and parts[0] == "Items" and parts[2] == "Images"


class JellyfinProvider:
    def __init__(
        self,
        base_url: str,
        token: str,
        user_id: str,
        connection_id: str,
        verify_ssl: bool,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.user_id = user_id
        self.connection_id = connection_id
        self.verify_ssl = verify_ssl
        self.provider_user_id: str = user_id
        self.provider_username: str | None = None

    def _headers(self) -> dict[str, str]:
        return _authorization_header(token=self.token)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            verify=self.verify_ssl,
            timeout=httpx.Timeout(JELLYFIN_REQUEST_TIMEOUT_SECONDS),
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"
        try:
            async with self._client() as client:
                response = await client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.ConnectError as err:
            raise ProviderUnreachable() from err
        except httpx.TimeoutException as err:
            raise ProviderUnreachable() from err
        except httpx.RequestError as err:
            if "ssl" in str(err).lower():
                raise ProviderSSLError() from err
            raise ProviderUnreachable() from err

        if response.status_code == 401:
            raise ProviderUnauthorized()
        if response.status_code == 404:
            raise ProviderNotFound(f"Jellyfin API error: {response.status_code}")
        if response.status_code >= 400:
            raise ProviderError(f"Jellyfin API error: {response.status_code}")
        return response

    async def ping(self) -> None:
        await self._request("GET", "/Users/Me")

    async def list_libraries(self) -> list[Library]:
        response = await self._request("GET", "/Library/MediaFolders")
        items = response.json().get("Items") or []
        libraries: list[Library] = []
        for folder in items:
            if folder.get("CollectionType") == "tvshows":
                libraries.append(map_library(self.connection_id, folder))
        return libraries

    async def list_series(
        self,
        library_native_id: str,
        *,
        page: int,
        limit: int,
        q: str | None,
    ) -> PagedSeries:
        start_index = (page - 1) * limit
        params: dict[str, str | int | bool] = {
            "ParentId": library_native_id,
            "IncludeItemTypes": "Series",
            "Recursive": True,
            "StartIndex": start_index,
            "Limit": limit,
            # DateCreated is not in the default item payload; required for library_added_at sort.
            "Fields": "DateCreated",
        }
        if q:
            params["SearchTerm"] = q

        response = await self._request("GET", "/Items", params=params)
        data = response.json()
        metadata = data.get("Items") or []
        total = int(data.get("TotalRecordCount") or len(metadata))
        items = [
            map_series(self.connection_id, library_native_id, item) for item in metadata
        ]
        return PagedSeries(items=items, page=page, limit=limit, total=total)

    async def list_episodes(self, series_composite_id: str) -> list[Episode]:
        _, provider, series_id = parse_series_id(series_composite_id)
        if provider != PROVIDER:
            raise ProviderError("wrong_type")

        response = await self._request(
            "GET",
            f"/Shows/{series_id}/Episodes",
            params={"userId": self.user_id, "EnableUserData": True},
        )
        items = response.json().get("Items") or []
        return [map_episode(self.connection_id, item) for item in items]

    async def get_on_deck_episode(self, series_composite_id: str) -> Episode | None:
        _, provider, series_id = parse_series_id(series_composite_id)
        if provider != PROVIDER:
            raise ProviderError("wrong_type")

        response = await self._request(
            "GET",
            "/Shows/NextUp",
            params={
                "userId": self.user_id,
                "seriesId": series_id,
                "Limit": 1,
                "EnableUserData": True,
            },
        )
        items = response.json().get("Items") or []
        if not items:
            return None
        return map_episode(self.connection_id, items[0])

    async def fetch_artwork(self, path: str) -> tuple[bytes, str]:
        if not _is_safe_jellyfin_image_path(path):
            raise ProviderError("invalid_path")
        url = f"{self.base_url}{path}"
        try:
            async with self._client() as client:
                response = await client.get(
                    url,
                    headers={**self._headers(), "Accept": "image/*"},
                )
        except httpx.ConnectError as err:
            raise ProviderUnreachable() from err
        except httpx.TimeoutException as err:
            raise ProviderUnreachable() from err
        except httpx.RequestError as err:
            if "ssl" in str(err).lower():
                raise ProviderSSLError() from err
            raise ProviderUnreachable() from err

        if response.status_code == 401:
            raise ProviderUnauthorized()
        if response.status_code >= 400:
            raise ProviderError("not_found")
        media_type = response.headers.get("content-type", "image/jpeg")
        return response.content, media_type
