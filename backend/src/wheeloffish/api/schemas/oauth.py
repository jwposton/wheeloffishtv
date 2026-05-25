from pydantic import BaseModel, Field


class PlexOAuthStartRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., min_length=1, max_length=512)
    verify_ssl: bool = True


class PlexOAuthStartResponse(BaseModel):
    pin_id: int
    auth_url: str


class PlexOAuthStatusResponse(BaseModel):
    status: str
    auth_token_present: bool


class JellyfinAuthRequest(BaseModel):
    base_url: str = Field(..., min_length=1, max_length=512)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=512)
    display_name: str = Field(..., min_length=1, max_length=255)
    verify_ssl: bool = True
