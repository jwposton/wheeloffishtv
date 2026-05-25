import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from wheeloffish.integrations.errors import ProviderError, ProviderUnauthorized, ProviderUnreachable

PLEX_TV_BASE = "https://plex.tv/api/v2"
PLEX_AUTH_URL = "https://app.plex.tv/auth#"
PIN_STATE_TTL_SECONDS = 15 * 60


@dataclass
class PinState:
    connection_id: str
    base_url: str
    verify_ssl: bool
    client_identifier: str
    app_user_id: str
    created_at: float


@dataclass(frozen=True)
class ResolvedServerConnection:
    """PMS base URL and token that work for this user on the configured server."""

    base_url: str
    token: str


_pin_state: dict[int, PinState] = {}


def _plex_headers(
    client_identifier: str,
    product_name: str,
    *,
    token: str | None = None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "X-Plex-Product": product_name,
        "X-Plex-Client-Identifier": client_identifier,
    }
    if token is not None:
        headers["X-Plex-Token"] = token
    return headers


def _normalize_url(url: str) -> str:
    return url.rstrip("/").lower()


def store_pin_state(
    pin_id: int,
    *,
    connection_id: str,
    base_url: str,
    verify_ssl: bool,
    client_identifier: str,
    app_user_id: str,
) -> None:
    _purge_expired_pin_state()
    _pin_state[pin_id] = PinState(
        connection_id=connection_id,
        base_url=base_url,
        verify_ssl=verify_ssl,
        client_identifier=client_identifier,
        app_user_id=app_user_id,
        created_at=time.monotonic(),
    )


def get_pin_state(pin_id: int) -> PinState | None:
    _purge_expired_pin_state()
    return _pin_state.get(pin_id)


def clear_pin_state(pin_id: int) -> None:
    _pin_state.pop(pin_id, None)


def _purge_expired_pin_state() -> None:
    now = time.monotonic()
    expired = [
        pin_id
        for pin_id, state in _pin_state.items()
        if now - state.created_at > PIN_STATE_TTL_SECONDS
    ]
    for pin_id in expired:
        _pin_state.pop(pin_id, None)


def build_auth_url(
    *,
    client_identifier: str,
    code: str,
    product_name: str,
    callback_base: str,
    pin_id: int,
) -> str:
    callback = (
        f"{callback_base.rstrip('/')}/api/v1/connections/plex/oauth/callback?pin_id={pin_id}"
    )
    return (
        f"{PLEX_AUTH_URL}?"
        f"clientID={quote(client_identifier, safe='')}"
        f"&code={code}"
        f"&forwardUrl={quote(callback, safe='')}"
        f"&context[device][product]={quote(product_name, safe='')}"
    )


async def create_pin(
    client_identifier: str,
    product_name: str,
) -> tuple[int, str, str]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PLEX_TV_BASE}/pins",
            params={"strong": "true"},
            headers=_plex_headers(client_identifier, product_name),
        )
        response.raise_for_status()
        data = response.json()

    pin_id = int(data["id"])
    code = str(data["code"])
    return pin_id, code, code


async def poll_pin(pin_id: int, client_identifier: str, product_name: str) -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PLEX_TV_BASE}/pins/{pin_id}",
            headers=_plex_headers(client_identifier, product_name),
        )
        response.raise_for_status()
        data = response.json()

    auth_token = data.get("authToken")
    if auth_token:
        return str(auth_token)
    return None


async def validate_token(token: str, client_identifier: str, product_name: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PLEX_TV_BASE}/user",
            headers=_plex_headers(client_identifier, product_name, token=token),
        )
        if response.status_code == 401:
            raise ProviderUnauthorized()
        response.raise_for_status()
        return response.json()


async def _fetch_server_resources(
    token: str,
    client_identifier: str,
    product_name: str,
) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PLEX_TV_BASE}/resources",
            params={"includeHttps": "1", "includeRelay": "1"},
            headers=_plex_headers(client_identifier, product_name, token=token),
        )
        if response.status_code == 401:
            raise ProviderUnauthorized()
        response.raise_for_status()
        return response.json()


async def resolve_server_connection(
    token: str,
    base_url: str,
    client_identifier: str,
    product_name: str,
) -> ResolvedServerConnection:
    """Map configured server URL to this user's working PMS URL and token.

    Home/shared users often need the per-resource ``accessToken`` from plex.tv,
    not the PIN auth token, when calling the media server API.
    """
    target = _normalize_url(base_url)
    resources = await _fetch_server_resources(token, client_identifier, product_name)

    for resource in resources:
        resource_token = resource.get("accessToken") or token
        for connection in resource.get("connections", []):
            uri = connection.get("uri")
            if uri and _normalize_url(str(uri)) == target:
                return ResolvedServerConnection(
                    base_url=str(uri).rstrip("/"),
                    token=str(resource_token),
                )
    raise ProviderUnreachable()


async def discover_server(
    token: str,
    base_url: str,
    client_identifier: str,
    product_name: str,
) -> bool:
    try:
        await resolve_server_connection(token, base_url, client_identifier, product_name)
    except ProviderError:
        return False
    return True


async def create_pin_with_auth_url(
    client_identifier: str,
    product_name: str,
    callback_base: str,
) -> tuple[int, str, str]:
    pin_id, code, _ = await create_pin(client_identifier, product_name)
    auth_url = build_auth_url(
        client_identifier=client_identifier,
        code=code,
        product_name=product_name,
        callback_base=callback_base,
        pin_id=pin_id,
    )
    return pin_id, code, auth_url
