"""Prune-state columns on playlist_series_rows and playlist_prune_events audit table."""

import sqlalchemy as sa

from alembic import op

revision = "011_prune_state_audit"
down_revision = "010_lib_added_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "playlist_series_rows",
        sa.Column("absence_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "playlist_series_rows",
        sa.Column("first_absence_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "playlist_series_rows",
        sa.Column("last_absence_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "playlist_series_rows",
        sa.Column("last_evidence_source", sa.String(32), nullable=True),
    )

    op.create_table(
        "playlist_prune_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "playlist_id",
            sa.String(36),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("series_id", sa.String(512), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_prune_events_playlist_ts",
        "playlist_prune_events",
        ["playlist_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_prune_events_playlist_ts", table_name="playlist_prune_events")
    op.drop_table("playlist_prune_events")
    op.drop_column("playlist_series_rows", "last_evidence_source")
    op.drop_column("playlist_series_rows", "last_absence_at")
    op.drop_column("playlist_series_rows", "first_absence_at")
    op.drop_column("playlist_series_rows", "absence_count")
