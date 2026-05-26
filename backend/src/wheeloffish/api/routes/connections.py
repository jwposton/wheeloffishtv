from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from wheeloffish.api.deps import get_app_user_id, get_db, get_settings_dep, get_vault
from wheeloffish.api.schemas.connections import (
    ConnectionResponse,
    ConnectionTestResponse,
)
from wheeloffish.core.config import Settings
from wheeloffish.core.connections import (
    delete_connection,
    list_connections,
    test_connection,
)
from wheeloffish.core.secrets import SecretsVault

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=list[ConnectionResponse])
def get_connections(db: Session = Depends(get_db)) -> list[ConnectionResponse]:
    return list_connections(db)


@router.post("", status_code=status.HTTP_403_FORBIDDEN)
async def post_connection() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "env_config_only",
            "message": "Configure connection in .env and restart",
        },
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
    _app_user_id: str = Depends(get_app_user_id),
) -> None:
    delete_connection(db, vault, connection_id)
