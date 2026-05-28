from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_current_user, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.auth import (
    AuthMeResponse,
    BootstrapSessionResponse,
    ConnectionSummary,
    InstallScheduleSummary,
    LogoutResponse,
)
from wheeloffish.core.auth import (
    get_env_connection,
    has_usable_media_credentials,
    libraries_scoped,
)
from wheeloffish.core.config import Settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.app_user import AppUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthMeResponse)
def auth_me(
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
) -> AuthMeResponse:
    connection = get_env_connection(db, settings)
    connection_summary = None
    linked = False
    scoped = False
    if connection is not None:
        connection_summary = ConnectionSummary(
            id=connection.id,
            provider=connection.provider_type,
            display_name=connection.display_name,
            base_url=connection.base_url,
        )
        linked = has_usable_media_credentials(db, vault, connection, user.id)
        scoped = libraries_scoped(db, connection.id, user.id)

    return AuthMeResponse(
        app_user_id=user.id,
        provider_user_id=user.provider_user_id,
        provider_username=user.provider_username,
        connection=connection_summary,
        has_media_link=linked,
        libraries_scoped=scoped,
        install_schedule=InstallScheduleSummary(
            install_timezone=settings.WOF_INSTALL_TIMEZONE,
            rebuild_cron=settings.WOF_REBUILD_CRON,
        ),
    )


@router.post("/bootstrap-session", response_model=BootstrapSessionResponse)
def bootstrap_session(
    request: Request,
    db: Session = Depends(get_db),
) -> BootstrapSessionResponse:
    existing_id = request.session.get("app_user_id")
    if existing_id:
        user = db.query(AppUser).filter(AppUser.id == existing_id).one_or_none()
        if user is not None:
            return BootstrapSessionResponse(status="ok")

    user = AppUser(provider_user_id=f"__pending__:{uuid4()}")
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["app_user_id"] = user.id
    return BootstrapSessionResponse(status="ok")


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request) -> LogoutResponse:
    request.session.clear()
    return LogoutResponse(status="ok")
