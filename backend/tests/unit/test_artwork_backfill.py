from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from wheeloffish.core.catalog_sync import backfill_artwork_for_connection
from wheeloffish.core.config import Settings
from wheeloffish.core.media_artwork import artwork_cache_path, write_cached_artwork
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.integrations.plex.client import PlexProvider
from conftest import seed_cached_libraries


@pytest.mark.asyncio
async def test_backfill_downloads_missing_posters(
    db_session,
    tmp_path,
    connection_factory,
) -> None:
    connection = await connection_factory()
    seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV", "in_scope": True}],
    )
    now = datetime.now(UTC)
    series_ids = []
    for index in range(3):
        series_id = f"{connection.id}:plex:guid-{index}"
        series_ids.append(series_id)
        db_session.add(
            CachedSeries(
                id=series_id,
                connection_id=connection.id,
                library_native_id="1",
                native_id=f"guid-{index}",
                title=f"Show {index}",
                thumb_url=f"/library/metadata/{index}/thumb/x",
                synced_at=now,
            )
        )
    db_session.commit()

    settings = Settings(
        WOF_SECRET_KEY="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        WOF_ARTWORK_CACHE_DIR=str(tmp_path),
    )
    write_cached_artwork(
        artwork_cache_path(str(tmp_path), connection.id, series_ids[0]),
        b"already",
    )

    provider = PlexProvider(
        base_url="https://plex.example.com",
        token="sync-token",
        client_identifier="test-client",
        connection_id=connection.id,
        verify_ssl=True,
    )
    provider.fetch_artwork = AsyncMock(return_value=(b"poster", "image/jpeg"))

    cached, failed = await backfill_artwork_for_connection(
        db_session,
        provider,
        connection.id,
        settings,
    )

    assert cached == 3
    assert failed == 0
    assert provider.fetch_artwork.await_count == 2
