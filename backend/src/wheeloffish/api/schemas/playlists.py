"""Pydantic request/response schemas for playlist CRUD + rebuild API (Phase 05 Plan 04)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    RowMode,
    SlotAllocation,
)


class PlaylistSeriesRowRequest(BaseModel):
    series_id: str
    mode: RowMode = RowMode.ORDERED
    completion_policy: CompletionPolicy = CompletionPolicy.REMOVE
    completion_event: CompletionEvent = CompletionEvent.SERIES_COMPLETE


class PlaylistCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    episode_count: int = Field(default=20, ge=1)
    slot_allocation: SlotAllocation = SlotAllocation.WILD
    default_completion_policy: CompletionPolicy = CompletionPolicy.REMOVE
    refresh_cadence: str = Field(default="daily", pattern=r"^(daily|weekly)$")
    refresh_day_of_week: int | None = Field(default=None, ge=0, le=6)
    rows: list[PlaylistSeriesRowRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def weekly_requires_day(self) -> "PlaylistCreateRequest":
        if self.refresh_cadence == "weekly" and self.refresh_day_of_week is None:
            raise ValueError("refresh_day_of_week required when refresh_cadence is weekly")
        return self


class PlaylistUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    episode_count: int | None = Field(default=None, ge=1)
    slot_allocation: SlotAllocation | None = None
    default_completion_policy: CompletionPolicy | None = None
    refresh_cadence: str | None = Field(default=None, pattern=r"^(daily|weekly)$")
    refresh_day_of_week: int | None = Field(default=None, ge=0, le=6)
    rows: list[PlaylistSeriesRowRequest] | None = None

    @model_validator(mode="after")
    def weekly_requires_day(self) -> "PlaylistUpdateRequest":
        if self.refresh_cadence == "weekly" and self.refresh_day_of_week is None:
            raise ValueError("refresh_day_of_week required when refresh_cadence is weekly")
        return self


class RebuildRunSummary(BaseModel):
    id: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None = None
    slots_filled: int | None = None
    slots_requested: int | None = None


class SnapshotEpisode(BaseModel):
    episode_id: str
    title: str
    series_id: str
    series_title: str | None = None
    slot_index: int
    row_mode: str


class PlaylistSeriesRowResponse(BaseModel):
    series_id: str
    mode: str
    completion_policy: str
    completion_event: str
    series_title: str | None = None


class PlaylistDetailResponse(BaseModel):
    id: str
    name: str
    episode_count: int
    slot_allocation: str
    default_completion_policy: str
    refresh_cadence: str
    refresh_day_of_week: int | None
    rows: list[PlaylistSeriesRowResponse]
    current_snapshot: list[SnapshotEpisode]
    last_rebuild: RebuildRunSummary | None
    recent_runs: list[RebuildRunSummary]


class PlaylistListItem(BaseModel):
    id: str
    name: str
    refresh_cadence: str
    refresh_day_of_week: int | None
    last_rebuild_status: str | None
    last_rebuild_at: datetime | None
