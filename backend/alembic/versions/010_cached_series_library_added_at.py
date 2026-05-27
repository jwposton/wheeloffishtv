"""Add library_added_at for series browse sort by date added."""

import sqlalchemy as sa

from alembic import op

# revision id must fit Postgres alembic_version.version_num (varchar(32))
revision = "010_lib_added_at"
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
