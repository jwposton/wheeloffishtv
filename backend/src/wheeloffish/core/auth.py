from sqlalchemy.orm import Session

from wheeloffish.core.config import Settings
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.cached_library import CachedLibrary
from wheeloffish.db.models.connection import Connection
from wheeloffish.db.models.user_media_link import UserMediaLink


def is_admin(app_user: AppUser, settings: Settings) -> bool:
    if settings.WOF_ADMIN_PROVIDER_USER_ID:
        if app_user.provider_user_id == settings.WOF_ADMIN_PROVIDER_USER_ID:
            return True
    if settings.WOF_ADMIN_USERNAME:
        if app_user.provider_username == settings.WOF_ADMIN_USERNAME:
            return True
        if app_user.provider_email == settings.WOF_ADMIN_USERNAME:
            return True
    return False


def is_setup_mode(settings: Settings) -> bool:
    return not bool(settings.WOF_ADMIN_PROVIDER_USER_ID.strip())


def upsert_app_user(
    db: Session,
    *,
    provider_user_id: str,
    provider_username: str | None = None,
    provider_email: str | None = None,
) -> AppUser:
    user = (
        db.query(AppUser).filter(AppUser.provider_user_id == provider_user_id).one_or_none()
    )
    if user is None:
        user = AppUser(
            provider_user_id=provider_user_id,
            provider_username=provider_username,
            provider_email=provider_email,
        )
        db.add(user)
    else:
        user.provider_username = provider_username
        user.provider_email = provider_email
    db.commit()
    db.refresh(user)
    return user


def libraries_scoped(db: Session, connection_id: str) -> bool:
    return (
        db.query(CachedLibrary)
        .filter(
            CachedLibrary.connection_id == connection_id,
            CachedLibrary.in_scope.is_(True),
        )
        .first()
        is not None
    )


def has_media_link(db: Session, app_user_id: str, connection_id: str) -> bool:
    return (
        db.query(UserMediaLink)
        .filter(
            UserMediaLink.app_user_id == app_user_id,
            UserMediaLink.connection_id == connection_id,
        )
        .first()
        is not None
    )


def get_env_connection(db: Session, settings: Settings) -> Connection | None:
    return (
        db.query(Connection).filter(Connection.provider_type == settings.WOF_PROVIDER).one_or_none()
    )
