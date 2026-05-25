from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.app_user import AppUser
    from wheeloffish.db.models.connection import Connection


class CatalogSyncState(Base):
    __tablename__ = "catalog_sync_state"

    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("connections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    app_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="idle")
    library_native_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page_cursor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_estimated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    connection: Mapped[Connection] = relationship("Connection", back_populates="sync_states")
    app_user: Mapped[AppUser] = relationship("AppUser")
