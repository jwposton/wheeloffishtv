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
