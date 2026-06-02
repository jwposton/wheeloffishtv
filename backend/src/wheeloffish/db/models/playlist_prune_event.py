from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from wheeloffish.db.models.base import Base


class PlaylistPruneEvent(Base):
    __tablename__ = "playlist_prune_events"
    __table_args__ = (Index("ix_prune_events_playlist_ts", "playlist_id", "timestamp"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    playlist_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    series_id: Mapped[str] = mapped_column(String(512), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
