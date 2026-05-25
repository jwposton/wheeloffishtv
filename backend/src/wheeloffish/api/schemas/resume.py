from __future__ import annotations

from pydantic import BaseModel, Field

from wheeloffish.domain.dto import Episode, ResumeCursor, ResumeSource


class EpisodeResponse(BaseModel):
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

    @classmethod
    def from_dto(cls, episode: Episode) -> EpisodeResponse:
        return cls.model_validate(episode.model_dump())


class EpisodesListResponse(BaseModel):
    episodes: list[EpisodeResponse]


class ResumePreviewResponse(BaseModel):
    series_id: str | None = None
    episode_id: str | None = None
    season_index: int | None = None
    episode_index: int | None = None
    percent_watched: float | None = None
    source: ResumeSource | None = None
    series_complete: bool = False

    @classmethod
    def from_cursor(cls, cursor: ResumeCursor) -> ResumePreviewResponse:
        return cls.model_validate(cursor.model_dump(exclude={"episode"}))
