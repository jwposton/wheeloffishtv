"""Per-user cached libraries and install-level library allowlist (Option B)."""

import sqlalchemy as sa

from alembic import op

revision = "006_per_user_libraries"
down_revision = "005_cached_series_browse_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "connections",
        sa.Column("library_allowlist_native_ids", sa.JSON(), nullable=True),
    )
    op.execute("DELETE FROM cached_libraries")

    with op.batch_alter_table("cached_libraries") as batch:
        batch.add_column(sa.Column("app_user_id", sa.String(length=36), nullable=False))
        batch.create_foreign_key(
            "fk_cached_libraries_app_user_id",
            "app_users",
            ["app_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_unique_constraint(
            "uq_cached_libraries_user_connection_native",
            ["app_user_id", "connection_id", "native_id"],
        )


def downgrade() -> None:
    op.execute("DELETE FROM cached_libraries")

    with op.batch_alter_table("cached_libraries") as batch:
        batch.drop_constraint(
            "uq_cached_libraries_user_connection_native",
            type_="unique",
        )
        batch.drop_constraint(
            "fk_cached_libraries_app_user_id",
            type_="foreignkey",
        )
        batch.drop_column("app_user_id")

    op.drop_column("connections", "library_allowlist_native_ids")
