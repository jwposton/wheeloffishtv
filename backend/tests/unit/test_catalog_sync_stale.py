from datetime import UTC, datetime, timedelta

from wheeloffish.core.catalog_sync import (
    SYNC_RUNNING_STALE_SECONDS,
    _get_or_create_sync_state,
    get_sync_status,
    trigger_sync,
)
from wheeloffish.db.models.catalog_sync_state import CatalogSyncState


def test_get_sync_status_marks_stale_running_as_failed(db_session) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    stale_at = datetime.now(UTC) - timedelta(seconds=SYNC_RUNNING_STALE_SECONDS + 1)

    db_session.add(
        CatalogSyncState(
            connection_id=connection_id,
            app_user_id=app_user_id,
            status="running",
            page_cursor=50,
            total_estimated=200,
            updated_at=stale_at,
            started_at=stale_at,
        )
    )
    db_session.commit()

    status = get_sync_status(db_session, connection_id, app_user_id)

    assert status["status"] == "failed"
    assert "stalled" in (status["error_message"] or "").lower()

    db_session.refresh(
        db_session.query(CatalogSyncState)
        .filter(
            CatalogSyncState.connection_id == connection_id,
            CatalogSyncState.app_user_id == app_user_id,
        )
        .one()
    )
    persisted = (
        db_session.query(CatalogSyncState)
        .filter(
            CatalogSyncState.connection_id == connection_id,
            CatalogSyncState.app_user_id == app_user_id,
        )
        .one()
    )
    assert persisted.status == "failed"


def test_trigger_sync_restarts_stale_running(db_session, monkeypatch) -> None:
    connection_id = "conn-1"
    app_user_id = "user-1"
    stale_at = datetime.now(UTC) - timedelta(seconds=SYNC_RUNNING_STALE_SECONDS + 1)

    db_session.add(
        CatalogSyncState(
            connection_id=connection_id,
            app_user_id=app_user_id,
            status="running",
            updated_at=stale_at,
            started_at=stale_at,
        )
    )
    db_session.commit()

    spawned: list[tuple[str, str]] = []

    def fake_create_task(coro):
        spawned.append(("would_spawn", coro.__name__ if hasattr(coro, "__name__") else "coro"))
        coro.close()

    monkeypatch.setattr("wheeloffish.core.catalog_sync.asyncio.create_task", fake_create_task)

    trigger_sync(db_session, connection_id, app_user_id)

    assert len(spawned) == 1
    state = _get_or_create_sync_state(db_session, connection_id, app_user_id)
    assert state.status == "running"
