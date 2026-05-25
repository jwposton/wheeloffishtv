from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from wheeloffish.core.auth import is_admin, is_setup_mode
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.app_user import AppUser
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


def get_current_user(request: Request, db: Session = Depends(get_db)) -> AppUser:
    app_user_id = request.session.get("app_user_id")
    if not app_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )
    user = db.query(AppUser).filter(AppUser.id == app_user_id).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )
    return user


def get_app_user_id(user: AppUser = Depends(get_current_user)) -> str:
    return user.id


def require_admin(
    user: AppUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> AppUser:
    if is_setup_mode(settings) or not is_admin(user, settings):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden"},
        )
    return user
