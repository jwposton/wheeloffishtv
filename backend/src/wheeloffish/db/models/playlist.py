from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow
    from wheeloffish.db.models.rebuild_run import RebuildRun


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    app_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    slot_allocation: Mapped[str] = mapped_column(String(32), nullable=False, default="wild")
    default_completion_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, default="remove"
    )
    refresh_cadence: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    refresh_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    rows: Mapped[list[PlaylistSeriesRow]] = relationship(
        "PlaylistSeriesRow",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistSeriesRow.sort_order",
    )
    rebuild_runs: Mapped[list[RebuildRun]] = relationship(
        "RebuildRun",
        back_populates="playlist",
        cascade="all, delete-orphan",
    )
