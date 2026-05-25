from typing import Any

import httpx

from wheeloffish.domain.dto import Episode, Library, PagedSeries
from wheeloffish.integrations.errors import (
    ProviderError,
    ProviderSSLError,
    ProviderUnauthorized,
    ProviderUnreachable,
)
from wheeloffish.integrations.plex.mappers import (
    map_episode,
    map_library,
    map_series,
    parse_series_guid,
    resolve_guid_to_rating_key,
)

PROVIDER = "plex"
PLEX_REQUEST_TIMEOUT_SECONDS = 60.0


class PlexProvider:
    def __init__(
        self,
        base_url: str,
        token: str,
        client_identifier: str,
        connection_id: str,
        verify_ssl: bool,
        product_name: str = "Wheel of Fish TV",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client_identifier = client_identifier
        self.connection_id = connection_id
        self.verify_ssl = verify_ssl
        self.product_name = product_name
        self.provider_user_id: str = "unknown"
        self.provider_username: str | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "X-Plex-Token": self.token,
            "X-Plex-Client-Identifier": self.client_identifier,
            "X-Plex-Product": self.product_name,
            "X-Plex-Version": "1.0.0",
            "X-Plex-Platform": "Web",
            "X-Plex-Device": self.product_name,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            verify=self.verify_ssl,
            timeout=httpx.Timeout(PLEX_REQUEST_TIMEOUT_SECONDS),
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
        if response.status_code >= 400:
            raise ProviderError(f"Plex API error: {response.status_code}")
        return response

    async def ping(self) -> None:
        await self._request("GET", "/library/sections")

    async def list_libraries(self) -> list[Library]:
        response = await self._request("GET", "/library/sections")
        data = response.json()
        directories = data.get("MediaContainer", {}).get("Directory") or []
        libraries: list[Library] = []
        for section in directories:
            if section.get("type") == "show":
                libraries.append(map_library(self.connection_id, section))
        return libraries

    async def list_series(
        self,
        library_native_id: str,
        *,
        page: int,
        limit: int,
        q: str | None,
    ) -> PagedSeries:
        start = (page - 1) * limit
        params: dict[str, str | int] = {
            "type": 2,
            "X-Plex-Container-Start": start,
            "X-Plex-Container-Size": limit,
        }
        if q:
            params["title"] = q

        response = await self._request(
            "GET",
            f"/library/sections/{library_native_id}/all",
            params=params,
        )
        container = response.json().get("MediaContainer", {})
        metadata = container.get("Metadata") or []
        total = int(container.get("totalSize") or container.get("size") or len(metadata))
        items = [
            map_series(self.connection_id, library_native_id, item) for item in metadata
        ]
        return PagedSeries(items=items, page=page, limit=limit, total=total)

    async def _find_series_thumb_in_library(
        self,
        library_native_id: str,
        guid: str,
        series_composite_id: str,
    ) -> str | None:
        """Locate a show's thumb path by paging library listings (works for home users)."""
        page = 1
        limit = 100
        while True:
            page_result = await self.list_series(
                library_native_id,
                page=page,
                limit=limit,
                q=None,
            )
            for item in page_result.items:
                if (item.native_id == guid or item.id == series_composite_id) and item.thumb_url:
                    return str(item.thumb_url)
            if not page_result.items or page * limit >= page_result.total:
                break
            page += 1
        return None

    async def _rating_key_for_series(
        self,
        series_composite_id: str,
        *,
        rating_key: str | None = None,
        library_native_id: str | None = None,
    ) -> str:
        if rating_key is not None:
            return rating_key
        _, provider, guid = parse_series_guid(series_composite_id)
        if provider != PROVIDER:
            raise ProviderError("wrong_type")
        async with self._client() as client:
            return await resolve_guid_to_rating_key(
                client,
                self.base_url,
                self.token,
                self.client_identifier,
                self.product_name,
                guid,
                library_native_id=library_native_id,
            )

    async def list_episodes(
        self,
        series_composite_id: str,
        *,
        rating_key: str | None = None,
        library_native_id: str | None = None,
    ) -> list[Episode]:
        resolved_key = await self._rating_key_for_series(
            series_composite_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
        response = await self._request("GET", f"/library/metadata/{resolved_key}/allLeaves")
        metadata = response.json().get("MediaContainer", {}).get("Metadata") or []
        return [map_episode(self.connection_id, item) for item in metadata]

    async def get_on_deck_episode(
        self,
        series_composite_id: str,
        *,
        rating_key: str | None = None,
        library_native_id: str | None = None,
    ) -> Episode | None:
        resolved_key = await self._rating_key_for_series(
            series_composite_id,
            rating_key=rating_key,
            library_native_id=library_native_id,
        )
        response = await self._request(
            "GET",
            f"/library/metadata/{resolved_key}",
            params={"includeOnDeck": 1},
        )
        metadata_list = response.json().get("MediaContainer", {}).get("Metadata") or []
        if not metadata_list:
            return None
        on_deck = metadata_list[0].get("OnDeck", {}).get("Metadata")
        if not on_deck:
            return None
        return map_episode(self.connection_id, on_deck)

    async def resolve_series_thumb_path(
        self,
        series_composite_id: str,
        *,
        library_native_id: str | None = None,
    ) -> str | None:
        """Return the poster path for this user/token (from live metadata lookup)."""
        _, _, guid = parse_series_guid(series_composite_id)
        if library_native_id is not None:
            thumb = await self._find_series_thumb_in_library(
                library_native_id,
                guid,
                series_composite_id,
            )
            if thumb:
                return thumb
            return None

        resolved_key = await self._rating_key_for_series(series_composite_id)
        response = await self._request("GET", f"/library/metadata/{resolved_key}")
        metadata_list = response.json().get("MediaContainer", {}).get("Metadata") or []
        if not metadata_list:
            return None
        thumb = metadata_list[0].get("thumb")
        return str(thumb) if thumb else None

    async def fetch_artwork(self, path: str) -> tuple[bytes, str]:
        if ".." in path or not path.startswith("/library/"):
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
