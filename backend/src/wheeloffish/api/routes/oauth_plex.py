import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_current_user, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.oauth import (
    PlexOAuthStartRequest,
    PlexOAuthStartResponse,
    PlexOAuthStatusResponse,
)
from wheeloffish.core.auth import is_setup_mode, upsert_app_user
from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.catalog_sync import trigger_sync
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import link_media_user
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.connection import Connection
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
    _body: PlexOAuthStartRequest | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    user: AppUser = Depends(get_current_user),
) -> PlexOAuthStartResponse:
    if settings.WOF_PROVIDER != "plex":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "provider_disabled", "message": "Plex is not enabled"},
        )

    connection = sync_connection_from_env(db, settings)
    client_identifier = str(uuid.uuid4())
    pin_id, _, auth_url = await create_pin_with_auth_url(
        client_identifier,
        settings.WOF_PLEX_PRODUCT_NAME,
        settings.WOF_OAUTH_CALLBACK_BASE,
    )
    store_pin_state(
        pin_id,
        connection_id=connection.id,
        base_url=connection.base_url,
        verify_ssl=connection.verify_ssl,
        client_identifier=client_identifier,
        app_user_id=user.id,
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
    request: Request,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
) -> RedirectResponse:
    state = get_pin_state(pin_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN not found or expired",
        )

    session_user_id = request.session.get("app_user_id")
    if session_user_id != state.app_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "session_mismatch", "message": "PIN session does not match"},
        )

    product_name = settings.WOF_PLEX_PRODUCT_NAME
    token = await poll_pin(pin_id, state.client_identifier, product_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={"status": "pending", "auth_token_present": False},
        )

    connection = (
        db.query(Connection).filter(Connection.id == state.connection_id).one_or_none()
    )
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    try:
        user_info = await validate_token(token, state.client_identifier, product_name)
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

        provider_user_id = str(user_info.get("id", "unknown"))
        provider_username = user_info.get("username") or user_info.get("email")
        app_user = upsert_app_user(
            db,
            provider_user_id=provider_user_id,
            provider_username=provider_username,
        )
        link_media_user(
            db,
            vault,
            connection,
            app_user,
            provider_user_id=provider_user_id,
            provider_username=provider_username,
            token=token,
        )
        request.session["app_user_id"] = app_user.id
        trigger_sync(db, connection.id, app_user.id)
    except ProviderError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": str(err) or err.code},
        ) from err
    finally:
        clear_pin_state(pin_id)

    redirect_path = "/setup" if is_setup_mode(settings) else "/"
    redirect_url = f"{settings.WOF_OAUTH_CALLBACK_BASE.rstrip('/')}{redirect_path}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
