"""Provider playlist link and rebuild writeback audit columns."""

import sqlalchemy as sa

from alembic import op

revision = "009_provider_playlist_writeback"
down_revision = "008_playlists_rebuilds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "playlists",
        sa.Column("provider_playlist_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "playlists",
        sa.Column("provider_kind", sa.String(16), nullable=True),
    )
    op.add_column(
        "rebuild_runs",
        sa.Column("writeback_status", sa.String(16), nullable=True),
    )
    op.add_column(
        "rebuild_runs",
        sa.Column("writeback_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "rebuild_runs",
        sa.Column("writeback_warnings", sa.JSON(), nullable=True),
    )
    op.add_column(
        "rebuild_runs",
        sa.Column("writeback_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("rebuild_runs", "writeback_at")
    op.drop_column("rebuild_runs", "writeback_warnings")
    op.drop_column("rebuild_runs", "writeback_error")
    op.drop_column("rebuild_runs", "writeback_status")
    op.drop_column("playlists", "provider_kind")
    op.drop_column("playlists", "provider_playlist_id")
