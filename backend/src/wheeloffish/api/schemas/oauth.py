from pydantic import BaseModel, ConfigDict, Field


class PlexOAuthStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlexOAuthStartResponse(BaseModel):
    pin_id: int
    auth_url: str


class PlexOAuthStatusResponse(BaseModel):
    status: str
    auth_token_present: bool


class JellyfinAuthRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=512)
