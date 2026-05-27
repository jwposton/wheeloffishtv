"""Add library_added_at for series browse sort by date added."""

import sqlalchemy as sa

from alembic import op

revision = "010_cached_series_library_added_at"
down_revision = "009_provider_playlist_writeback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cached_series",
        sa.Column("library_added_at", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cached_series", "library_added_at")
