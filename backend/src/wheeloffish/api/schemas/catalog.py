from typing import Literal

from pydantic import BaseModel, Field, model_validator

from wheeloffish.domain.dto import Library, Series
from wheeloffish.integrations.base import WatchAction, WatchScope


class SyncStatusEmbed(BaseModel):
    status: str
    progress_pct: float | None = None
    library_native_id: str | None = None
    error_message: str | None = None


class SyncStatusResponse(SyncStatusEmbed):
    pass


class SeriesBrowseResponse(BaseModel):
    items: list[Series]
    page: int
    limit: int
    total: int
    sync: SyncStatusEmbed


class LibraryScopeUpdate(BaseModel):
    in_scope_library_native_ids: list[str] = Field(default_factory=list)


class LibraryScopeResponse(BaseModel):
    libraries: list[Library]


class SessionCatalogRefreshResponse(BaseModel):
    sync: dict[str, SyncStatusEmbed]


class WatchStateMutationRequest(BaseModel):
    target_id: str | None = None
    target_ids: list[str] = Field(default_factory=list)
    scope: WatchScope
    action: WatchAction

    @model_validator(mode="after")
    def validate_targets(self) -> "WatchStateMutationRequest":
        if self.target_id is None and not self.target_ids:
            raise ValueError("target_id or target_ids is required")
        return self


class WatchStateMutationResponse(BaseModel):
    status: Literal["succeeded", "partial", "failed"]
    scope: WatchScope
    updated_count: int
    failed_count: int
    failed_ids: list[str] = Field(default_factory=list)
    error_code: Literal["auth", "forbidden", "not_found", "provider_error"] | None = None
    message: str
