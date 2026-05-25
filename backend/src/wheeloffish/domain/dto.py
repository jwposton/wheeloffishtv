from typing import Any, Literal

from pydantic import BaseModel, Field


class Library(BaseModel):
    id: str
    title: str
    native_id: str
    connection_id: str
    provider: str
    in_scope: bool = True


class Series(BaseModel):
    id: str
    title: str
    native_id: str
    library_native_id: str
    connection_id: str
    provider: str
    year: int | None = None
    thumb_url: str | None = None
    provider_metadata: dict[str, Any] | None = None


class PagedSeries(BaseModel):
    items: list[Series]
    page: int
    limit: int
    total: int


class WatchSnapshot(BaseModel):
    percent_watched: float = Field(ge=0, le=100)
    provider_marked_played: bool = False


class Episode(BaseModel):
    id: str
    title: str
    season_index: int
    episode_index: int
    duration_ms: int
    percent_watched: float = Field(ge=0, le=100)
    provider_marked_played: bool = False
    part_index: int | None = None
    multipart_group_id: str | None = None
    is_special: bool = False
    special_for_season: int | None = None


ResumeSource = Literal["earliest_unfinished", "on_deck"]


class ResumeCursor(BaseModel):
    series_id: str | None = None
    episode_id: str | None = None
    season_index: int | None = None
    episode_index: int | None = None
    percent_watched: float | None = None
    source: ResumeSource | None = None
    series_complete: bool = False
    episode: Episode | None = None
