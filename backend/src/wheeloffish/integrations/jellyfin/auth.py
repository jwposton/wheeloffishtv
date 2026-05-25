import re
import uuid
from typing import Any

import httpx

from wheeloffish.integrations.errors import (
    ProviderError,
    ProviderSSLError,
    ProviderUnauthorized,
    ProviderUnreachable,
)

CLIENT = "WheelOfFishTV"
DEVICE = "Server"
VERSION = "0.1.0"

# Admin API keys are 32-char hex strings — unsupported for per-user linking (D-13).
_API_KEY_PATTERN = re.compile(r"^[a-fA-F0-9]{32}$")


def _authorization_header(
    *,
    token: str | None = None,
    device_id: str | None = None,
) -> dict[str, str]:
    did = device_id or str(uuid.uuid4())
    parts = [
        f'MediaBrowser Client="{CLIENT}"',
        f'Device="{DEVICE}"',
        f'DeviceId="{did}"',
        f'Version="{VERSION}"',
    ]
    if token is not None:
        parts.append(f'Token="{token}"')
    return {"Authorization": ", ".join(parts), "Accept": "application/json"}


def _reject_api_key_only_flow(username: str, password: str) -> None:
    """Reject admin API-key-only auth; user linking requires AuthenticateByName."""
    trimmed_username = username.strip()
    if _API_KEY_PATTERN.match(trimmed_username):
        raise ProviderUnauthorized("API key authentication is not supported for user linking")
    if trimmed_username and not password.strip():
        raise ProviderUnauthorized("Password required for user linking")


async def authenticate(
    base_url: str,
    username: str,
    password: str,
    verify_ssl: bool,
) -> tuple[str, str, str]:
    """Authenticate via POST /Users/AuthenticateByName; password is never stored."""
    _reject_api_key_only_flow(username, password)
    url = f"{base_url.rstrip('/')}/Users/AuthenticateByName"
    device_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            response = await client.post(
                url,
                headers=_authorization_header(device_id=device_id),
                json={"Username": username, "Pw": password},
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
        raise ProviderError(f"Jellyfin auth error: {response.status_code}")

    data = response.json()
    user = data.get("User") or {}
    access_token = data.get("AccessToken")
    user_id = user.get("Id")
    display_name = user.get("Name")
    if not access_token or not user_id:
        raise ProviderUnauthorized()

    return str(access_token), str(user_id), str(display_name or username)


async def validate_token(base_url: str, token: str, verify_ssl: bool) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/Users/Me"
    try:
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            response = await client.get(url, headers=_authorization_header(token=token))
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
        raise ProviderError(f"Jellyfin token validation error: {response.status_code}")
    return response.json()
