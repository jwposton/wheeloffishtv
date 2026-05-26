from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wheeloffish.db.models.base import Base

if TYPE_CHECKING:
    from wheeloffish.db.models.cached_library import CachedLibrary
    from wheeloffish.db.models.cached_series import CachedSeries
    from wheeloffish.db.models.catalog_sync_state import CatalogSyncState
    from wheeloffish.db.models.user_media_link import UserMediaLink


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (UniqueConstraint("provider_type", name="uq_connections_provider_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_type: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    plex_client_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    library_allowlist_native_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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

    user_media_links: Mapped[list[UserMediaLink]] = relationship(
        "UserMediaLink",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    cached_libraries: Mapped[list[CachedLibrary]] = relationship(
        "CachedLibrary",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    cached_series: Mapped[list[CachedSeries]] = relationship(
        "CachedSeries",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    sync_states: Mapped[list[CatalogSyncState]] = relationship(
        "CatalogSyncState",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
