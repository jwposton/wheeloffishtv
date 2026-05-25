from pydantic import BaseModel


class ProvidersMetaResponse(BaseModel):
    enabled: list[str]
