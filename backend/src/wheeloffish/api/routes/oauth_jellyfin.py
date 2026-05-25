from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.oauth import JellyfinAuthRequest
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import create_connection
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.jellyfin.auth import authenticate, validate_token

router = APIRouter(prefix="/connections/jellyfin", tags=["jellyfin-auth"])


@router.post("/auth")
async def jellyfin_auth(
    body: JellyfinAuthRequest,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> JSONResponse:
    if "jellyfin" not in settings.enabled_providers_set:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "provider_disabled", "message": "Jellyfin is not enabled"},
        )

    try:
        token, user_id, username = await authenticate(
            body.base_url,
            body.username,
            body.password,
            body.verify_ssl,
        )
        await validate_token(body.base_url, token, body.verify_ssl)
        connection = await create_connection(
            db,
            vault,
            settings,
            provider_type="jellyfin",
            display_name=body.display_name,
            base_url=body.base_url,
            verify_ssl=body.verify_ssl,
            token=token,
            app_user_id=app_user_id,
            provider_user_id=user_id,
            provider_username=username,
        )
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
