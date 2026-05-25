from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.connection import Connection


class UserMediaLink(Base):
    __tablename__ = "user_media_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    connection: Mapped[Connection] = relationship("Connection", back_populates="user_media_links")
