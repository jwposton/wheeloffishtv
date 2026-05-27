from datetime import UTC, datetime

from wheeloffish.core.catalog_sync import _upsert_series_page
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.domain.dto import Series
from wheeloffish.domain.ids import format_composite_id


def _series(
    connection_id: str,
    guid: str,
    *,
    library: str = "5",
    provider_metadata: dict | None = None,
    library_added_at: int | None = None,
) -> Series:
    return Series(
        id=format_composite_id(connection_id, "plex", guid),
        title="Test Show",
        native_id=guid,
        library_native_id=library,
        connection_id=connection_id,
        provider="plex",
        library_added_at=library_added_at,
        provider_metadata=provider_metadata,
    )


def test_upsert_series_page_dedupes_same_guid_in_one_batch(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)

    duplicate_a = _series(connection_id, guid)
    duplicate_b = _series(connection_id, guid)
    duplicate_b.title = "Updated Title"

    _upsert_series_page(
        db_session,
        [duplicate_a, duplicate_b],
        app_user_id,
        synced_at,
    )
    db_session.commit()

    rows = (
        db_session.query(CachedSeries)
        .filter(
            CachedSeries.app_user_id == app_user_id,
            CachedSeries.connection_id == connection_id,
        )
        .all()
    )
    assert len(rows) == 1
    assert rows[0].title == "Updated Title"


def test_upsert_series_page_updates_existing_row_by_composite_id(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)
    series_id = format_composite_id(connection_id, "plex", guid)

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=app_user_id,
            connection_id=connection_id,
            library_native_id="4",
            native_id=guid,
            title="Old Title",
            synced_at=synced_at,
        )
    )
    db_session.commit()

    incoming = _series(connection_id, guid, library="5")
    incoming.title = "New Title"
    _upsert_series_page(db_session, [incoming], app_user_id, synced_at)
    db_session.commit()

    row = (
        db_session.query(CachedSeries)
        .filter(
            CachedSeries.id == series_id,
            CachedSeries.app_user_id == app_user_id,
        )
        .one()
    )
    assert row.title == "New Title"
    assert row.library_native_id == "5"


def test_upsert_series_page_allows_same_series_id_for_different_users(db_session) -> None:
    connection_id = "conn-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)
    series_id = format_composite_id(connection_id, "plex", guid)
    series = _series(connection_id, guid)

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id="admin-user",
            connection_id=connection_id,
            library_native_id="5",
            native_id=guid,
            title="Admin Copy",
            synced_at=synced_at,
        )
    )
    db_session.commit()

    _upsert_series_page(db_session, [series], "home-user", synced_at)
    db_session.commit()

    rows = (
        db_session.query(CachedSeries)
        .filter(CachedSeries.id == series_id)
        .order_by(CachedSeries.app_user_id)
        .all()
    )
    assert len(rows) == 2
    assert {row.app_user_id for row in rows} == {"admin-user", "home-user"}


def test_upsert_series_page_persists_enriched_provider_metadata(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)
    provider_metadata = {
        "ratingKey": "12",
        "summary": "A spy show",
        "genres": ["Action", "Drama"],
        "contentRating": "TV-MA",
        "studio": "HBO",
    }

    series = _series(connection_id, guid, provider_metadata=provider_metadata)
    _upsert_series_page(db_session, [series], app_user_id, synced_at)
    db_session.commit()

    row = (
        db_session.query(CachedSeries)
        .filter(
            CachedSeries.app_user_id == app_user_id,
            CachedSeries.connection_id == connection_id,
            CachedSeries.native_id == guid,
        )
        .one()
    )
    assert row.provider_metadata == provider_metadata


def test_upsert_series_page_stores_library_added_at(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)
    series = _series(connection_id, guid, library_added_at=42)
    _upsert_series_page(db_session, [series], app_user_id, synced_at)
    db_session.commit()

    row = (
        db_session.query(CachedSeries)
        .filter(
            CachedSeries.app_user_id == app_user_id,
            CachedSeries.connection_id == connection_id,
            CachedSeries.native_id == guid,
        )
        .one()
    )
    assert row.library_added_at == 42


def test_upsert_series_page_overwrites_provider_metadata_on_resync(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    guid = "plex://show/abc123"
    synced_at = datetime.now(UTC)
    series_id = format_composite_id(connection_id, "plex", guid)

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=app_user_id,
            connection_id=connection_id,
            library_native_id="5",
            native_id=guid,
            title="Test Show",
            provider_metadata={"summary": "old", "genres": ["Drama"]},
            synced_at=synced_at,
        )
    )
    db_session.commit()

    updated_metadata = {
        "ratingKey": "12",
        "summary": "new",
        "genres": ["Comedy"],
        "contentRating": None,
        "studio": None,
    }
    incoming = _series(connection_id, guid, provider_metadata=updated_metadata)
    _upsert_series_page(db_session, [incoming], app_user_id, synced_at)
    db_session.commit()

    row = (
        db_session.query(CachedSeries)
        .filter(
            CachedSeries.id == series_id,
            CachedSeries.app_user_id == app_user_id,
        )
        .one()
    )
    assert row.provider_metadata["summary"] == "new"
    assert row.provider_metadata["genres"] == ["Comedy"]

