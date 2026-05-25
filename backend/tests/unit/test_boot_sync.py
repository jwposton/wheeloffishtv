import pytest
from pydantic import ValidationError

from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.config import Settings
from wheeloffish.db.models.connection import Connection

TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def test_sync_connection_from_env_creates_row_when_empty(db_session) -> None:
    settings = Settings(
        WOF_SECRET_KEY=TEST_SECRET_KEY,
        DATABASE_URL="sqlite:///:memory:",
        WOF_PROVIDER="plex",
        WOF_MEDIA_SERVER_URL="https://plex.example.com",
    )
    connection = sync_connection_from_env(db_session, settings)

    assert connection.provider_type == "plex"
    assert connection.base_url == "https://plex.example.com"
    assert db_session.query(Connection).count() == 1


def test_sync_connection_from_env_updates_without_duplicate(db_session) -> None:
    settings = Settings(
        WOF_SECRET_KEY=TEST_SECRET_KEY,
        DATABASE_URL="sqlite:///:memory:",
        WOF_PROVIDER="plex",
        WOF_MEDIA_SERVER_URL="https://plex.example.com",
    )
    sync_connection_from_env(db_session, settings)

    updated_settings = settings.model_copy(
        update={"WOF_MEDIA_SERVER_URL": "https://plex-new.example.com"}
    )
    connection = sync_connection_from_env(db_session, updated_settings)

    assert db_session.query(Connection).count() == 1
    assert connection.base_url == "https://plex-new.example.com"


def test_invalid_wof_provider_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        Settings(
            WOF_SECRET_KEY=TEST_SECRET_KEY,
            WOF_PROVIDER="invalid",  # type: ignore[arg-type]
            WOF_MEDIA_SERVER_URL="https://plex.example.com",
        )
