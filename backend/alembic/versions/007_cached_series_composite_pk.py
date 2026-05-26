"""Composite primary key on cached_series for per-user rows sharing series ids."""


from alembic import op

revision = "007_cached_series_composite_pk"
down_revision = "006_per_user_libraries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cached_series", recreate="always") as batch:
        batch.create_primary_key(
            "pk_cached_series_app_user_id",
            ["app_user_id", "id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("cached_series", recreate="always") as batch:
        batch.create_primary_key("pk_cached_series", ["id"])
