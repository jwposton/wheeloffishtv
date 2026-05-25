"""Playlists, playlist series rows, and rebuild runs tables."""

import sqlalchemy as sa

from alembic import op

revision = "008_playlists_rebuilds"
down_revision = "007_cached_series_composite_pk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "app_user_id",
            sa.String(36),
            sa.ForeignKey("app_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("episode_count", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("slot_allocation", sa.String(32), nullable=False, server_default="wild"),
        sa.Column(
            "default_completion_policy", sa.String(32), nullable=False, server_default="remove"
        ),
        sa.Column("refresh_cadence", sa.String(16), nullable=False, server_default="daily"),
        sa.Column("refresh_day_of_week", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_playlists_app_user_id", "playlists", ["app_user_id"])

    op.create_table(
        "playlist_series_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "playlist_id",
            sa.String(36),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("series_id", sa.String(512), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False, server_default="ordered"),
        sa.Column(
            "completion_policy", sa.String(32), nullable=False, server_default="remove"
        ),
        sa.Column(
            "completion_event", sa.String(32), nullable=False, server_default="series_complete"
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("playlist_id", "series_id", name="uq_playlist_series_row"),
    )

    op.create_table(
        "rebuild_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "playlist_id",
            sa.String(36),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("rebuild_seed", sa.String(128), nullable=True),
        sa.Column("slots_requested", sa.Integer(), nullable=True),
        sa.Column("slots_filled", sa.Integer(), nullable=True),
        sa.Column("row_outcomes_json", sa.JSON(), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_rebuild_runs_playlist_started",
        "rebuild_runs",
        ["playlist_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rebuild_runs_playlist_started", table_name="rebuild_runs")
    op.drop_table("rebuild_runs")
    op.drop_table("playlist_series_rows")
    op.drop_index("ix_playlists_app_user_id", table_name="playlists")
    op.drop_table("playlists")
