from datetime import UTC, datetime

import pytest

from wheeloffish.core.connections import build_provider_for_connection
from wheeloffish.core.secrets import PlexUserCredentials
from wheeloffish.db.models.connection import Connection
from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.plex.client import PlexProvider


def _connection_with_stored_client_id() -> Connection:
    return Connection(
        id="conn-1",
        provider_type="plex",
        display_name="Plex",
        base_url="https://plex.example.com",
        verify_ssl=True,
        plex_client_identifier="admin-client-id-on-connection-row",
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_build_provider_requires_explicit_client_id() -> None:
    connection = _connection_with_stored_client_id()

    with pytest.raises(ProviderError, match="plex_client_identifier required"):
        build_provider_for_connection(connection, "user-token")


def test_build_provider_uses_only_explicit_client_id() -> None:
    connection = _connection_with_stored_client_id()

    provider = build_provider_for_connection(
        connection,
        "user-token",
        plex_client_identifier="user-client-id",
    )

    assert isinstance(provider, PlexProvider)
    assert provider.client_identifier == "user-client-id"
    assert provider.client_identifier != connection.plex_client_identifier


def test_build_plex_provider_for_user_ignores_connection_client_id() -> None:
    from wheeloffish.core.connections import build_plex_provider_for_user

    connection = _connection_with_stored_client_id()
    credentials = PlexUserCredentials(token="user-token", client_identifier="vault-client-id")

    provider = build_plex_provider_for_user(connection, credentials)

    assert provider.client_identifier == "vault-client-id"
    assert provider.token == "user-token"
