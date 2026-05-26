from pydantic import BaseModel


class ProvidersMetaResponse(BaseModel):
    provider: str
    oauth_callback_base: str


class VersionMetaResponse(BaseModel):
    version: str
    latest_version: str | None
    update_available: bool
    release_url: str | None
