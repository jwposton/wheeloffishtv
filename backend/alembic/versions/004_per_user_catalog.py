"""Per-user catalog cache and sync state."""

import sqlalchemy as sa

from alembic import op

revision = "004_per_user_catalog"
down_revision = "003_app_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Shared catalog rows cannot be attributed to a user; require a fresh sync per user.
    op.execute("DELETE FROM cached_series")
    op.execute("DELETE FROM catalog_sync_state")

    with op.batch_alter_table("cached_series") as batch:
        batch.add_column(sa.Column("app_user_id", sa.String(length=36), nullable=False))
        batch.drop_constraint("uq_cached_series_connection_native", type_="unique")
        batch.create_unique_constraint(
            "uq_cached_series_user_connection_native",
            ["app_user_id", "connection_id", "native_id"],
        )
        batch.create_foreign_key(
            "fk_cached_series_app_user_id",
            "app_users",
            ["app_user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.drop_table("catalog_sync_state")
    op.create_table(
        "catalog_sync_state",
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("app_user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="idle"),
        sa.Column("library_native_id", sa.String(length=128), nullable=True),
        sa.Column("page_cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_estimated", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["app_user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("connection_id", "app_user_id"),
    )


def downgrade() -> None:
    op.execute("DELETE FROM cached_series")
    op.execute("DELETE FROM catalog_sync_state")

    op.drop_table("catalog_sync_state")
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

    with op.batch_alter_table("cached_series") as batch:
        batch.drop_constraint("fk_cached_series_app_user_id", type_="foreignkey")
        batch.drop_constraint("uq_cached_series_user_connection_native", type_="unique")
        batch.drop_column("app_user_id")
        batch.create_unique_constraint(
            "uq_cached_series_connection_native",
            ["connection_id", "native_id"],
        )
