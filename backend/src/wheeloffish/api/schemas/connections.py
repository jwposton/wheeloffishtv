from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreate(BaseModel):
    provider_type: Literal["plex", "jellyfin"]
    display_name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., min_length=1, max_length=512)
    verify_ssl: bool = True
    token: str = Field(..., min_length=1)
    plex_client_identifier: str | None = Field(default=None, max_length=64)


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_type: str
    display_name: str
    base_url: str
    verify_ssl: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ConnectionTestResponse(BaseModel):
    status: str
