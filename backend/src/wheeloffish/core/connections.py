import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.user_media_link import UserMediaLink
from wheeloffish.domain.dto import Library
from wheeloffish.integrations.base import MediaProvider
from wheeloffish.integrations.errors import ProviderDisabled, ProviderError
from wheeloffish.integrations.plex.client import PlexProvider

ProviderType = Literal["plex", "jellyfin"]


@dataclass
class ConnectionConfig:
    provider_type: ProviderType
    base_url: str
    verify_ssl: bool
    plex_client_identifier: str | None = None


class EphemeralMediaProvider:
    """Stub provider for test-then-save until real clients ship in plans 03-04."""

    def __init__(self, config: ConnectionConfig, token: str) -> None:
        self.config = config
        self.token = token
        self.provider_user_id: str = "unknown"
        self.provider_username: str | None = None

    async def ping(self) -> None:
        return None

    async def list_libraries(self) -> list:
        raise NotImplementedError

    async def list_series(
        self,
        library_native_id: str,
        *,
        page: int,
        limit: int,
        q: str | None,
    ) -> list:
        raise NotImplementedError

    async def list_episodes(self, series_composite_id: str) -> list:
        raise NotImplementedError

    async def get_on_deck_episode(self, series_composite_id: str):
        raise NotImplementedError


def build_ephemeral_provider(config: ConnectionConfig, token: str) -> MediaProvider:
    return EphemeralMediaProvider(config, token)


def build_provider_for_connection(
    connection: Connection | ConnectionConfig,
    token: str,
    *,
    settings: Settings | None = None,
) -> MediaProvider:
    if isinstance(connection, ConnectionConfig):
        config = connection
        connection_id = "pending"
    else:
        config = ConnectionConfig(
            provider_type=connection.provider_type,  # type: ignore[arg-type]
            base_url=connection.base_url,
            verify_ssl=connection.verify_ssl,
            plex_client_identifier=connection.plex_client_identifier,
        )
        connection_id = connection.id

    product_name = settings.WOF_PLEX_PRODUCT_NAME if settings else "Wheel of Fish TV"

    if config.provider_type == "plex":
        if not config.plex_client_identifier:
            raise ProviderError("plex_client_identifier required for Plex")
        return PlexProvider(
            base_url=config.base_url,
            token=token,
            client_identifier=config.plex_client_identifier,
            connection_id=connection_id,
            verify_ssl=config.verify_ssl,
            product_name=product_name,
        )
    return build_ephemeral_provider(config, token)


def _provider_error_to_http(err: ProviderError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": err.code, "message": str(err) or err.code},
    )


async def create_connection(
    db: Session,
    vault: SecretsVault,
    settings: Settings,
    *,
    provider_type: str,
    display_name: str,
    base_url: str,
    verify_ssl: bool,
    token: str,
    app_user_id: str,
    plex_client_identifier: str | None = None,
    provider_user_id: str | None = None,
    provider_username: str | None = None,
) -> Connection:
    if provider_type not in settings.enabled_providers_set:
        raise _provider_error_to_http(ProviderDisabled())

    if provider_type == "plex" and not plex_client_identifier:
        plex_client_identifier = str(uuid.uuid4())

    existing = db.query(Connection).filter(Connection.provider_type == provider_type).one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_provider_type", "message": "Connection already exists"},
        )

    connection_id = str(uuid.uuid4())
    pending = Connection(
        id=connection_id,
        provider_type=provider_type,
        display_name=display_name,
        base_url=base_url,
        verify_ssl=verify_ssl,
        plex_client_identifier=plex_client_identifier,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    provider = build_provider_for_connection(pending, token, settings=settings)
    if provider_user_id:
        provider.provider_user_id = provider_user_id
    if provider_username:
        provider.provider_username = provider_username

    try:
        await provider.ping()
    except ProviderError as err:
        raise _provider_error_to_http(err) from err

    now = datetime.now(UTC)
    connection = Connection(
        id=connection_id,
        provider_type=provider_type,
        display_name=display_name,
        base_url=base_url,
        verify_ssl=verify_ssl,
        plex_client_identifier=plex_client_identifier,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    link = UserMediaLink(
        id=str(uuid.uuid4()),
        app_user_id=app_user_id,
        connection_id=connection.id,
        provider_user_id=provider_user_id or getattr(provider, "provider_user_id", "unknown"),
        provider_username=provider_username or getattr(provider, "provider_username", None),
        linked_at=now,
    )

    try:
        db.add(connection)
        db.add(link)
        db.flush()
        vault.store_media_user_token(connection.id, app_user_id, token, commit=False)
        db.commit()
        db.refresh(connection)
    except Exception:
        db.rollback()
        raise

    return connection


async def test_connection(
    db: Session,
    vault: SecretsVault,
    connection_id: str,
    app_user_id: str,
    *,
    settings: Settings | None = None,
) -> dict[str, str]:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    token = vault.get_media_user_token(connection_id, app_user_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unauthorized", "message": "No token for user"},
        )

    resolved_settings = settings or get_settings()
    provider = build_provider_for_connection(connection, token, settings=resolved_settings)

    try:
        await provider.ping()
    except ProviderError as err:
        raise _provider_error_to_http(err) from err

    return {"status": "ok"}


async def list_connection_libraries(
    db: Session,
    vault: SecretsVault,
    connection_id: str,
    app_user_id: str,
    *,
    settings: Settings | None = None,
) -> list[Library]:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    token = vault.get_media_user_token(connection_id, app_user_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unauthorized", "message": "No token for user"},
        )

    resolved_settings = settings or get_settings()
    provider = build_provider_for_connection(connection, token, settings=resolved_settings)
    try:
        return await provider.list_libraries()
    except ProviderError as err:
        raise _provider_error_to_http(err) from err


def list_connections(db: Session) -> list[Connection]:
    return db.query(Connection).order_by(Connection.created_at).all()


def delete_connection(db: Session, vault: SecretsVault, connection_id: str) -> None:
    connection = db.query(Connection).filter(Connection.id == connection_id).one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    try:
        vault.delete_all_connection_secrets(connection_id, commit=False)
        db.delete(connection)
        db.commit()
    except Exception:
        db.rollback()
        raise
