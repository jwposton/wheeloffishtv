from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.connection import Connection


class CachedSeries(Base):
    __tablename__ = "cached_series"
    __table_args__ = (
        UniqueConstraint("connection_id", "native_id", name="uq_cached_series_connection_native"),
    )

    id: Mapped[str] = mapped_column(String(512), primary_key=True)
    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    library_native_id: Mapped[str] = mapped_column(String(128), nullable=False)
    native_id: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_sort: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    connection: Mapped[Connection] = relationship("Connection", back_populates="cached_series")
