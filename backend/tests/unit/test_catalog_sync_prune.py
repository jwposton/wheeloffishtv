"""Integration tests: catalog sync drives prune evidence and failure resets."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from conftest import APP_USER_ID, seed_cached_libraries

from wheeloffish.core.catalog_prune import PRUNE_THRESHOLD
from wheeloffish.core.catalog_sync import run_chunked_sync
from wheeloffish.db.models.app_user import AppUser
from wheeloffish.db.models.cached_series import CachedSeries
from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.playlist_prune_event import PlaylistPruneEvent
from wheeloffish.db.models.playlist_series_row import PlaylistSeriesRow as PlaylistSeriesRowOrm
from wheeloffish.domain.dto import PagedSeries, Series
from wheeloffish.domain.ids import format_composite_id
from wheeloffish.integrations.errors import ProviderError


def _series_id(connection_id: str, native_id: str) -> str:
    return format_composite_id(connection_id, "plex", native_id)


def _seed_app_user(db_session) -> None:
    if (
        db_session.query(AppUser).filter(AppUser.id == APP_USER_ID).one_or_none()
        is not None
    ):
        return
    db_session.add(
        AppUser(
            id=APP_USER_ID,
            provider_user_id="catalog-prune-user",
            provider_username="viewer",
        )
    )
    db_session.commit()


def _seed_playlist(db_session, *, series_ids: list[str]) -> PlaylistOrm:
    playlist_id = str(uuid.uuid4())
    pl = PlaylistOrm(
        id=playlist_id,
        app_user_id=APP_USER_ID,
        name="Sync Prune Test",
        episode_count=4,
        slot_allocation="wild",
        default_completion_policy="remove",
        refresh_cadence="daily",
        refresh_day_of_week=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(pl)
    for i, sid in enumerate(series_ids):
        db_session.add(
            PlaylistSeriesRowOrm(
                id=str(uuid.uuid4()),
                playlist_id=playlist_id,
                series_id=sid,
                mode="ordered",
                completion_policy="remove",
                completion_event="series_complete",
                sort_order=i,
            )
        )
    db_session.commit()
    db_session.refresh(pl)
    return pl


def _seed_cached_series_row(
    db_session,
    *,
    connection_id: str,
    series_id: str,
    native_id: str,
    library_native_id: str = "1",
    synced_at: datetime | None = None,
) -> None:
    when = synced_at or datetime.now(UTC) - timedelta(hours=1)
    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=APP_USER_ID,
            connection_id=connection_id,
            library_native_id=library_native_id,
            native_id=native_id,
            title=f"Cached {native_id}",
            synced_at=when,
        )
    )
    db_session.commit()


def _mock_provider(connection_id: str, *, synced_native_ids: list[str]) -> MagicMock:
    provider = MagicMock()

    async def list_series(
        library_native_id: str, *, page: int, limit: int, q: str | None
    ) -> PagedSeries:
        items = [
            Series(
                id=_series_id(connection_id, native_id),
                title=f"Synced {native_id}",
                native_id=native_id,
                library_native_id=library_native_id,
                connection_id=connection_id,
                provider="plex",
            )
            for native_id in synced_native_ids
        ]
        return PagedSeries(
            items=items,
            page=page,
            limit=limit,
            total=len(items),
        )

    provider.list_series = AsyncMock(side_effect=list_series)
    return provider


def _row(
    db_session, playlist_id: str, series_id: str
) -> PlaylistSeriesRowOrm:
    return (
        db_session.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == playlist_id,
            PlaylistSeriesRowOrm.series_id == series_id,
        )
        .one()
    )


async def _run_sync(
    db_session,
    connection,
    *,
    synced_native_ids: list[str],
    ensure_raises: Exception | None = None,
) -> None:
    libs = seed_cached_libraries(
        db_session,
        connection.id,
        [{"native_id": "1", "title": "TV Shows", "in_scope": True}],
    )
    provider = _mock_provider(connection.id, synced_native_ids=synced_native_ids)

    ensure_mock = AsyncMock(return_value=libs)
    if ensure_raises is not None:
        ensure_mock = AsyncMock(side_effect=ensure_raises)

    def noop_create_task(coro):
        coro.close()

    with (
        patch(
            "wheeloffish.core.catalog_sync.ensure_libraries_cached",
            new=ensure_mock,
        ),
        patch(
            "wheeloffish.core.catalog_sync.get_in_scope_libraries",
            return_value=libs,
        ),
        patch(
            "wheeloffish.core.catalog_sync._build_provider",
            return_value=provider,
        ),
        patch("wheeloffish.core.catalog_sync.asyncio.create_task", noop_create_task),
    ):
        await run_chunked_sync(connection.id, APP_USER_ID)


@pytest.mark.asyncio
async def test_sync_absence_then_prune(
    connection_factory, db_session
) -> None:
    _seed_app_user(db_session)
    connection = await connection_factory()
    present_id = _series_id(connection.id, "show-present")
    absent_id = _series_id(connection.id, "show-absent")
    pl = _seed_playlist(db_session, series_ids=[present_id, absent_id])

    _seed_cached_series_row(
        db_session,
        connection_id=connection.id,
        series_id=present_id,
        native_id="show-present",
    )
    _seed_cached_series_row(
        db_session,
        connection_id=connection.id,
        series_id=absent_id,
        native_id="show-absent",
    )

    absent_row = _row(db_session, pl.id, absent_id)
    absent_row.absence_count = PRUNE_THRESHOLD - 1
    db_session.commit()

    await _run_sync(
        db_session,
        connection,
        synced_native_ids=["show-present"],
    )

    db_session.expire_all()
    assert (
        db_session.query(PlaylistSeriesRowOrm)
        .filter(
            PlaylistSeriesRowOrm.playlist_id == pl.id,
            PlaylistSeriesRowOrm.series_id == absent_id,
        )
        .count()
        == 0
    )
    events = (
        db_session.query(PlaylistPruneEvent)
        .filter(
            PlaylistPruneEvent.playlist_id == pl.id,
            PlaylistPruneEvent.series_id == absent_id,
            PlaylistPruneEvent.event_type == "auto_pruned",
        )
        .all()
    )
    assert len(events) == 1
    assert events[0].reason == "catalog_sync"
    assert _row(db_session, pl.id, present_id).absence_count == 0


@pytest.mark.asyncio
async def test_sync_recovery_clears_counter(
    connection_factory, db_session
) -> None:
    _seed_app_user(db_session)
    connection = await connection_factory()
    series_id = _series_id(connection.id, "show-recovered")
    pl = _seed_playlist(db_session, series_ids=[series_id])

    _seed_cached_series_row(
        db_session,
        connection_id=connection.id,
        series_id=series_id,
        native_id="show-recovered",
    )

    row = _row(db_session, pl.id, series_id)
    row.absence_count = 2
    db_session.commit()

    await _run_sync(
        db_session,
        connection,
        synced_native_ids=["show-recovered"],
    )

    db_session.expire_all()
    assert _row(db_session, pl.id, series_id).absence_count == 0


@pytest.mark.asyncio
async def test_failed_sync_resets_counters(
    connection_factory, db_session
) -> None:
    _seed_app_user(db_session)
    connection = await connection_factory()
    series_id = _series_id(connection.id, "show-stale")
    pl = _seed_playlist(db_session, series_ids=[series_id])

    row = _row(db_session, pl.id, series_id)
    row.absence_count = 2
    db_session.commit()

    await _run_sync(
        db_session,
        connection,
        synced_native_ids=[],
        ensure_raises=ProviderError("provider unavailable"),
    )

    db_session.expire_all()
    assert _row(db_session, pl.id, series_id).absence_count == 0
