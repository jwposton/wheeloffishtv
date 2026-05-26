from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.playlist import Playlist


class RebuildRun(Base):
    __tablename__ = "rebuild_runs"
    __table_args__ = (
        Index("ix_rebuild_runs_playlist_started", "playlist_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    playlist_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    rebuild_seed: Mapped[str | None] = mapped_column(String(128), nullable=True)
    slots_requested: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slots_filled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_outcomes_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    writeback_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    writeback_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    writeback_warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    writeback_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    playlist: Mapped[Playlist] = relationship("Playlist", back_populates="rebuild_runs")
