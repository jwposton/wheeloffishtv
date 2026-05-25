from enum import StrEnum

from pydantic import BaseModel, Field

from wheeloffish.domain.dto import Episode


class RowMode(StrEnum):
    ORDERED = "ordered"
    DISORDERED = "disordered"


class CompletionPolicy(StrEnum):
    REMOVE = "remove"
    RESTART = "restart"
    DISORDERED = "disordered"


class CompletionEvent(StrEnum):
    SERIES_COMPLETE = "series_complete"
    SEASON_COMPLETE = "season_complete"


class PlaylistSeriesRow(BaseModel):
    series_id: str
    mode: RowMode = RowMode.ORDERED
    completion_policy: CompletionPolicy = CompletionPolicy.REMOVE
    completion_event: CompletionEvent = CompletionEvent.SERIES_COMPLETE


class Playlist(BaseModel):
    id: str
    name: str
    episode_count: int = Field(ge=1)
    rows: list[PlaylistSeriesRow]


class SeriesRebuildInput(BaseModel):
    series_id: str
    episodes: list[Episode]
    on_deck: Episode | None = None


class BuiltEpisode(BaseModel):
    episode: Episode
    series_id: str
    row_mode: RowMode
    slot_index: int


class RowBuildOutcome(BaseModel):
    series_id: str
    effective_mode: RowMode
    excluded: bool = False
    policy_applied: CompletionPolicy | None = None


class PlaylistBuildResult(BaseModel):
    episodes: list[BuiltEpisode]
    row_outcomes: list[RowBuildOutcome]
    day_key: str
    slots_requested: int
    slots_filled: int
