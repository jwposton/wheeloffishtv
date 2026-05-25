from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_current_user, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.oauth import JellyfinAuthRequest
from wheeloffish.core.auth import upsert_app_user
from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.catalog_sync import trigger_sync
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import link_media_user
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.jellyfin.auth import authenticate, validate_token

router = APIRouter(prefix="/connections/jellyfin", tags=["jellyfin-auth"])


@router.post("/auth")
async def jellyfin_auth(
    body: JellyfinAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    user: AppUser = Depends(get_current_user),
) -> JSONResponse:
    if settings.WOF_PROVIDER != "jellyfin":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "provider_disabled", "message": "Jellyfin is not enabled"},
        )

    connection = sync_connection_from_env(db, settings)

    try:
        token, user_id, username = await authenticate(
            connection.base_url,
            body.username,
            body.password,
            connection.verify_ssl,
        )
        await validate_token(connection.base_url, token, connection.verify_ssl)
        app_user = upsert_app_user(
            db,
            provider_user_id=user_id,
            provider_username=username,
        )
        link_media_user(
            db,
            vault,
            connection,
            app_user,
            provider_user_id=user_id,
            provider_username=username,
            token=token,
        )
        request.session["app_user_id"] = app_user.id
        trigger_sync(db, connection.id, app_user.id)
    except ProviderError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": str(err) or err.code},
        ) from err

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "connected",
            "connection_id": connection.id,
            "auth_token_present": True,
        },
    )
