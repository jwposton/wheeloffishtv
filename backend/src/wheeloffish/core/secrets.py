import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings
from wheeloffish.core.logging import fernet_from_secret_key
from wheeloffish.core.namespaces import (
    MEDIA_SERVER_NS,
    connection_secrets_prefix,
    media_server_token_key,
    media_user_client_identifier_key,
    media_user_token_key,
    plex_user_credentials_key,
)
from wheeloffish.db.models.secret import Secret


@dataclass(frozen=True)
class PlexUserCredentials:
    token: str
    client_identifier: str


class SecretsVault:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._fernet = fernet_from_secret_key(settings.WOF_SECRET_KEY)

    def get_secret(self, namespace: str, key: str) -> str | None:
        row = (
            self._session.query(Secret)
            .filter(Secret.namespace == namespace, Secret.key == key)
            .one_or_none()
        )
        if row is None:
            return None
        return self._fernet.decrypt(row.ciphertext.encode()).decode()

    def set_secret(self, namespace: str, key: str, value: str, *, commit: bool = True) -> None:
        ciphertext = self._fernet.encrypt(value.encode()).decode()
        row = (
            self._session.query(Secret)
            .filter(Secret.namespace == namespace, Secret.key == key)
            .one_or_none()
        )
        now = datetime.now(UTC)
        if row is None:
            row = Secret(
                namespace=namespace,
                key=key,
                ciphertext=ciphertext,
                created_at=now,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.ciphertext = ciphertext
            row.updated_at = now
        if commit:
            self._session.commit()

    def delete_secret(self, namespace: str, key: str, *, commit: bool = True) -> bool:
        row = (
            self._session.query(Secret)
            .filter(Secret.namespace == namespace, Secret.key == key)
            .one_or_none()
        )
        if row is None:
            return False
        self._session.delete(row)
        if commit:
            self._session.commit()
        return True

    def store_media_token(self, connection_id: str, token: str) -> None:
        self.set_secret(MEDIA_SERVER_NS, media_server_token_key(connection_id), token)

    def get_media_token(self, connection_id: str) -> str | None:
        return self.get_secret(MEDIA_SERVER_NS, media_server_token_key(connection_id))

    def delete_media_token(self, connection_id: str) -> bool:
        return self.delete_secret(MEDIA_SERVER_NS, media_server_token_key(connection_id))

    def store_media_user_token(
        self,
        connection_id: str,
        app_user_id: str,
        token: str,
        *,
        commit: bool = True,
    ) -> None:
        self.set_secret(
            MEDIA_SERVER_NS,
            media_user_token_key(connection_id, app_user_id),
            token,
            commit=commit,
        )

    def get_media_user_token(self, connection_id: str, app_user_id: str) -> str | None:
        return self.get_secret(
            MEDIA_SERVER_NS,
            media_user_token_key(connection_id, app_user_id),
        )

    def store_media_user_client_identifier(
        self,
        connection_id: str,
        app_user_id: str,
        client_identifier: str,
        *,
        commit: bool = True,
    ) -> None:
        self.set_secret(
            MEDIA_SERVER_NS,
            media_user_client_identifier_key(connection_id, app_user_id),
            client_identifier,
            commit=commit,
        )

    def get_media_user_client_identifier(
        self,
        connection_id: str,
        app_user_id: str,
    ) -> str | None:
        return self.get_secret(
            MEDIA_SERVER_NS,
            media_user_client_identifier_key(connection_id, app_user_id),
        )

    def store_plex_user_credentials(
        self,
        connection_id: str,
        app_user_id: str,
        token: str,
        client_identifier: str,
        *,
        commit: bool = True,
    ) -> None:
        """Store token + client ID as one atomic unit (must stay paired for Plex)."""
        payload = json.dumps({"token": token, "client_identifier": client_identifier})
        self.set_secret(
            MEDIA_SERVER_NS,
            plex_user_credentials_key(connection_id, app_user_id),
            payload,
            commit=False,
        )
        self.set_secret(
            MEDIA_SERVER_NS,
            media_user_token_key(connection_id, app_user_id),
            token,
            commit=False,
        )
        self.set_secret(
            MEDIA_SERVER_NS,
            media_user_client_identifier_key(connection_id, app_user_id),
            client_identifier,
            commit=commit,
        )

    def get_plex_user_credentials(
        self,
        connection_id: str,
        app_user_id: str,
    ) -> PlexUserCredentials | None:
        combined = self.get_secret(
            MEDIA_SERVER_NS,
            plex_user_credentials_key(connection_id, app_user_id),
        )
        if combined:
            try:
                data = json.loads(combined)
                token = str(data["token"])
                client_identifier = str(data["client_identifier"])
                return PlexUserCredentials(token=token, client_identifier=client_identifier)
            except (KeyError, TypeError, json.JSONDecodeError):
                pass

        token = self.get_media_user_token(connection_id, app_user_id)
        client_identifier = self.get_media_user_client_identifier(connection_id, app_user_id)
        if token and client_identifier:
            return PlexUserCredentials(token=token, client_identifier=client_identifier)
        return None

    def clear_plex_user_credentials(
        self,
        connection_id: str,
        app_user_id: str,
        *,
        commit: bool = True,
    ) -> None:
        self.delete_secret(
            MEDIA_SERVER_NS,
            plex_user_credentials_key(connection_id, app_user_id),
            commit=False,
        )
        self.delete_secret(
            MEDIA_SERVER_NS,
            media_user_token_key(connection_id, app_user_id),
            commit=False,
        )
        self.delete_secret(
            MEDIA_SERVER_NS,
            media_user_client_identifier_key(connection_id, app_user_id),
            commit=commit,
        )

    def delete_media_user_token(
        self,
        connection_id: str,
        app_user_id: str,
        *,
        commit: bool = True,
    ) -> bool:
        return self.delete_secret(
            MEDIA_SERVER_NS,
            media_user_token_key(connection_id, app_user_id),
            commit=commit,
        )

    def delete_all_connection_secrets(self, connection_id: str, *, commit: bool = True) -> int:
        prefix = connection_secrets_prefix(connection_id)
        rows = (
            self._session.query(Secret)
            .filter(Secret.namespace == MEDIA_SERVER_NS, Secret.key.startswith(prefix))
            .all()
        )
        for row in rows:
            self._session.delete(row)
        if commit and rows:
            self._session.commit()
        return len(rows)
