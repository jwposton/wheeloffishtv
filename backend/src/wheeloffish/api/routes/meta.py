from fastapi import APIRouter, Depends

from wheeloffish.api.schemas.meta import ProvidersMetaResponse, VersionMetaResponse
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.version_check import get_version_info

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersMetaResponse)
def list_enabled_providers(
    settings: Settings = Depends(get_settings),
) -> ProvidersMetaResponse:
    return ProvidersMetaResponse(
        provider=settings.WOF_PROVIDER,
        oauth_callback_base=settings.WOF_OAUTH_CALLBACK_BASE,
    )


@router.get("/version", response_model=VersionMetaResponse)
def read_version() -> VersionMetaResponse:
    info = get_version_info()
    return VersionMetaResponse(
        version=info.version,
        latest_version=info.latest_version,
        update_available=info.update_available,
        release_url=info.release_url,
    )
