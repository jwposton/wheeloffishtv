"""Add browse index on cached_series for per-user catalog queries."""

from alembic import op

revision = "005_cached_series_browse_idx"
down_revision = "004_per_user_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_cached_series_user_connection_title",
        "cached_series",
        ["app_user_id", "connection_id", "title"],
    )


def downgrade() -> None:
    op.drop_index("ix_cached_series_user_connection_title", table_name="cached_series")
