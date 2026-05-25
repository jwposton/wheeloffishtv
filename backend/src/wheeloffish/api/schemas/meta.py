from pydantic import BaseModel


class ProvidersMetaResponse(BaseModel):
    provider: str
    oauth_callback_base: str
