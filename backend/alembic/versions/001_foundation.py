"""Foundation tables: app_metadata and secrets."""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision = "001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("install_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=512), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace", "key", name="uq_secrets_namespace_key"),
    )
    op.create_index("ix_secrets_namespace", "secrets", ["namespace"], unique=False)

    install_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO app_metadata (schema_version, install_id, created_at) "
            "VALUES (:schema_version, :install_id, :created_at)"
        ),
        {"schema_version": "001", "install_id": install_id, "created_at": now},
    )


def downgrade() -> None:
    op.drop_index("ix_secrets_namespace", table_name="secrets")
    op.drop_table("secrets")
    op.drop_table("app_metadata")
