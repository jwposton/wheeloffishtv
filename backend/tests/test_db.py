from datetime import UTC, datetime

from sqlalchemy import inspect, text

from wheeloffish.db.models.app_metadata import AppMetadata


def test_wal_mode_enabled(db_engine) -> None:
    with db_engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert str(result).lower() == "wal"


def test_migration_creates_tables(db_engine) -> None:
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())
    assert "app_metadata" in tables
    assert "secrets" in tables


def test_app_metadata_round_trip(db_session) -> None:
    row = AppMetadata(
        schema_version="test",
        install_id="00000000-0000-0000-0000-000000000099",
        created_at=datetime.now(UTC),
    )
    db_session.add(row)
    db_session.commit()

    fetched = db_session.query(AppMetadata).filter_by(install_id=row.install_id).one()
    assert fetched.schema_version == "test"
