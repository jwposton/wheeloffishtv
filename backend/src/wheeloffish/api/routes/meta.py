from fastapi import APIRouter, Depends

from wheeloffish.api.schemas.meta import ProvidersMetaResponse
from wheeloffish.core.config import Settings, get_settings

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersMetaResponse)
def list_enabled_providers(
    settings: Settings = Depends(get_settings),
) -> ProvidersMetaResponse:
    enabled = sorted(settings.enabled_providers_set)
    return ProvidersMetaResponse(enabled=enabled)
