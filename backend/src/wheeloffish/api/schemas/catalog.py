from pydantic import BaseModel, Field

from wheeloffish.domain.dto import Library, Series


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
