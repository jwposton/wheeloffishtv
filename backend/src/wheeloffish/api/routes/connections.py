from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.connections import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResponse,
)
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import (
    create_connection,
    delete_connection,
    list_connection_libraries,
    list_connections,
    test_connection,
)
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.domain.dto import Library

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionResponse])
def get_connections(db: Session = Depends(get_db)) -> list[ConnectionResponse]:
    return list_connections(db)


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def post_connection(
    body: ConnectionCreate,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> ConnectionResponse:
    connection = await create_connection(
        db,
        vault,
        settings,
        provider_type=body.provider_type,
        display_name=body.display_name,
        base_url=body.base_url,
        verify_ssl=body.verify_ssl,
        token=body.token,
        app_user_id=app_user_id,
        plex_client_identifier=body.plex_client_identifier,
    )
    return ConnectionResponse.model_validate(connection)


@router.get("/{connection_id}/libraries", response_model=list[Library])
async def get_connection_libraries(
    connection_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> list[Library]:
    return await list_connection_libraries(
        db, vault, connection_id, app_user_id, settings=settings
    )


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
async def post_connection_test(
    connection_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
    settings: Settings = Depends(get_settings_dep),
    app_user_id: str = Depends(get_app_user_id),
) -> ConnectionTestResponse:
    result = await test_connection(
        db, vault, connection_id, app_user_id, settings=settings
    )
    return ConnectionTestResponse(**result)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    vault: SecretsVault = Depends(get_vault),
) -> None:
    delete_connection(db, vault, connection_id)
