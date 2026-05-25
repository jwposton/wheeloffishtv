from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.playlist import Playlist


class PlaylistSeriesRow(Base):
    __tablename__ = "playlist_series_rows"
    __table_args__ = (
        UniqueConstraint("playlist_id", "series_id", name="uq_playlist_series_row"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    playlist_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    series_id: Mapped[str] = mapped_column(String(512), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="ordered")
    completion_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, default="remove"
    )
    completion_event: Mapped[str] = mapped_column(
        String(32), nullable=False, default="series_complete"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    playlist: Mapped[Playlist] = relationship("Playlist", back_populates="rows")
