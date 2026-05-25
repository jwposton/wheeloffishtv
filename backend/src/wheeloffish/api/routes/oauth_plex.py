import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.oauth import (
    PlexOAuthStartRequest,
    PlexOAuthStartResponse,
    PlexOAuthStatusResponse,
)
from wheeloffish.core.catalog_sync import trigger_sync
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import create_connection
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.integrations.errors import ProviderError
from wheeloffish.integrations.plex.auth import (
    clear_pin_state,
    create_pin_with_auth_url,
    discover_server,
    get_pin_state,
    poll_pin,
    store_pin_state,
    validate_token,
)

router = APIRouter(prefix="/connections/plex/oauth", tags=["plex-oauth"])


@router.post("/start", response_model=PlexOAuthStartResponse)
async def plex_oauth_start(
    body: PlexOAuthStartRequest,
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> PlexOAuthStartResponse:
    if "plex" not in settings.enabled_providers_set:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "provider_disabled", "message": "Plex is not enabled"},
        )

    client_identifier = str(uuid.uuid4())
    pin_id, _, auth_url = await create_pin_with_auth_url(
        client_identifier,
        settings.WOF_PLEX_PRODUCT_NAME,
        settings.WOF_OAUTH_CALLBACK_BASE,
    )
    store_pin_state(
        pin_id,
        display_name=body.display_name,
        base_url=body.base_url,
        verify_ssl=body.verify_ssl,
        client_identifier=client_identifier,
        app_user_id=app_user_id,
    )
    return PlexOAuthStartResponse(pin_id=pin_id, auth_url=auth_url)


@router.get("/status/{pin_id}", response_model=PlexOAuthStatusResponse)
async def plex_oauth_status(
    pin_id: int,
    settings: Settings = Depends(get_settings_dep),
) -> PlexOAuthStatusResponse:
    state = get_pin_state(pin_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN not found or expired",
        )

    token = await poll_pin(pin_id, state.client_identifier, settings.WOF_PLEX_PRODUCT_NAME)
    if token:
        return PlexOAuthStatusResponse(status="claimed", auth_token_present=True)
    return PlexOAuthStatusResponse(status="pending", auth_token_present=False)


@router.get("/callback")
async def plex_oauth_callback(
    pin_id: int,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
) -> JSONResponse:
    state = get_pin_state(pin_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN not found or expired",
        )

    product_name = settings.WOF_PLEX_PRODUCT_NAME
    token = await poll_pin(pin_id, state.client_identifier, product_name)
    if not token:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"status": "pending", "auth_token_present": False},
        )

    try:
        user = await validate_token(token, state.client_identifier, product_name)
        if not await discover_server(
            token, state.base_url, state.client_identifier, product_name
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "unreachable",
                    "message": "Configured Plex server not found in account resources",
                },
            )

        connection = await create_connection(
            db,
            vault,
            settings,
            provider_type="plex",
            display_name=state.display_name,
            base_url=state.base_url,
            verify_ssl=state.verify_ssl,
            token=token,
            app_user_id=state.app_user_id,
            plex_client_identifier=state.client_identifier,
            provider_user_id=str(user.get("id", "unknown")),
            provider_username=user.get("username") or user.get("email"),
        )
        trigger_sync(db, connection.id, state.app_user_id)
    except ProviderError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": str(err) or err.code},
        ) from err
    finally:
        clear_pin_state(pin_id)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "connected",
            "connection_id": connection.id,
            "auth_token_present": True,
        },
    )
