from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.session import get_db as session_get_db

STUB_APP_USER_ID = "00000000-0000-4000-8000-000000000001"


def get_db() -> Generator[Session, None, None]:
    yield from session_get_db()


def get_settings_dep() -> Settings:
    return get_settings()


def get_vault(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> SecretsVault:
    return SecretsVault(db, settings)


def get_app_user_id() -> str:
    return STUB_APP_USER_ID


def require_admin() -> None:
    """Stub admin gate until Phase 3 auth ships."""
    return None
