"""Connections and catalog cache tables."""

import sqlalchemy as sa

from alembic import op

revision = "002_connections_catalog"
down_revision = "001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider_type", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("plex_client_identifier", sa.String(length=64), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_type", name="uq_connections_provider_type"),
    )
    op.create_table(
        "user_media_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("app_user_id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("provider_user_id", sa.String(length=128), nullable=False),
        sa.Column("provider_username", sa.String(length=255), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cached_libraries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("native_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("in_scope", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cached_series",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("library_native_id", sa.String(length=128), nullable=False),
        sa.Column("native_id", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("title_sort", sa.String(length=512), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("thumb_url", sa.String(length=1024), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "connection_id", "native_id", name="uq_cached_series_connection_native"
        ),
    )
    op.create_table(
        "catalog_sync_state",
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="idle"),
        sa.Column("library_native_id", sa.String(length=128), nullable=True),
        sa.Column("page_cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_estimated", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("connection_id"),
    )


def downgrade() -> None:
    op.drop_table("catalog_sync_state")
    op.drop_table("cached_series")
    op.drop_table("cached_libraries")
    op.drop_table("user_media_links")
    op.drop_table("connections")
