import json
import os
from pathlib import Path

import httpx
import pytest
from alembic.config import Config
from httpx import ASGITransport

from alembic import command
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.session import get_engine, reset_session_state

# Valid 32-byte hex key for all tests
TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
APP_USER_ID = "00000000-0000-4000-8000-000000000001"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

os.environ.setdefault("WOF_SECRET_KEY", TEST_SECRET_KEY)
os.environ.setdefault("WOF_PROVIDER", "plex")
os.environ.setdefault("WOF_MEDIA_SERVER_URL", "https://plex.example.com")
os.environ.setdefault("ENVIRONMENT", "development")

from wheeloffish.main import app  # noqa: E402


def load_fixture(name: str) -> dict:
    """Load sanitized JSON fixture from tests/fixtures/{plex|jellyfin}/."""
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text())


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure WOF_SECRET_KEY is set for every test."""
    monkeypatch.setenv("WOF_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("WOF_PROVIDER", "plex")
    monkeypatch.setenv("WOF_MEDIA_SERVER_URL", "https://plex.example.com")
    get_settings.cache_clear()
    reset_session_state()


@pytest.fixture
def settings() -> Settings:
    """Settings loaded with test secret key and in-memory database."""
    get_settings.cache_clear()
    return Settings(
        WOF_SECRET_KEY=TEST_SECRET_KEY,
        DATABASE_URL="sqlite:///:memory:",
    )


@pytest.fixture
async def async_client():
    """Async HTTP client wired to the FastAPI ASGI app."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def vault(db_session, settings: Settings) -> SecretsVault:
    """SecretsVault backed by the test database session."""
    return SecretsVault(db_session, settings)


@pytest.fixture
def app_user_id() -> str:
    """Constant app user UUID for per-user token tests."""
    return APP_USER_ID


@pytest.fixture
def db_engine(settings: Settings, tmp_path, monkeypatch: pytest.MonkeyPatch):
    """SQLite engine with migrations applied."""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    reset_session_state()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")

    test_settings = settings.model_copy(update={"DATABASE_URL": database_url})
    engine = get_engine(test_settings)
    yield engine
    engine.dispose()
    reset_session_state()


@pytest.fixture
def db_session(db_engine):
    from wheeloffish.db.session import get_session_factory

    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def connection_factory(db_session, settings, vault, app_user_id):
    from unittest.mock import AsyncMock, MagicMock, patch

    from wheeloffish.core.connections import create_connection

    async def _factory(**overrides):
        defaults = {
            "provider_type": "plex",
            "display_name": "Test Plex",
            "base_url": "https://plex.example.com",
            "verify_ssl": True,
            "token": "test-token",
        }
        params = {**defaults, **overrides}
        provider = MagicMock()
        provider.ping = AsyncMock(return_value=None)
        provider.provider_user_id = "test-provider-user"
        provider.provider_username = None
        with patch(
            "wheeloffish.core.connections.build_provider_for_connection",
            return_value=provider,
        ):
            connection = await create_connection(
                db_session,
                vault,
                settings,
                app_user_id=app_user_id,
                **params,
            )
        return connection

    return _factory


def seed_cached_libraries(
    db_session,
    connection_id: str,
    libraries: list[dict],
    *,
    app_user_id: str = APP_USER_ID,
) -> list:
    """Seed cached_libraries rows. Each dict: native_id, title, in_scope."""
    from datetime import UTC, datetime

    from wheeloffish.db.models.cached_library import CachedLibrary
    from wheeloffish.db.models.connection import Connection

    in_scope_ids = [spec["native_id"] for spec in libraries if spec.get("in_scope")]
    if in_scope_ids:
        connection = (
            db_session.query(Connection).filter(Connection.id == connection_id).one()
        )
        connection.library_allowlist_native_ids = in_scope_ids

    now = datetime.now(UTC)
    rows = []
    for spec in libraries:
        row = CachedLibrary(
            app_user_id=app_user_id,
            connection_id=connection_id,
            native_id=spec["native_id"],
            title=spec["title"],
            in_scope=spec.get("in_scope", False),
            synced_at=now,
        )
        db_session.add(row)
        rows.append(row)
    db_session.commit()
    for row in rows:
        db_session.refresh(row)
    return rows


def seed_cached_series(
    db_session,
    connection_id: str,
    count: int,
    *,
    app_user_id: str = APP_USER_ID,
    provider: str = "plex",
    library_native_id: str = "1",
    title_prefix: str = "Series",
    start_index: int = 0,
) -> list:
    """Seed cached_series rows for browse/sync tests."""
    from datetime import UTC, datetime

    from wheeloffish.db.models.cached_series import CachedSeries
    from wheeloffish.domain.ids import format_composite_id

    now = datetime.now(UTC)
    rows = []
    for offset in range(count):
        index = start_index + offset
        native_id = f"guid-{index}"
        row = CachedSeries(
            id=format_composite_id(connection_id, provider, native_id),
            app_user_id=app_user_id,
            connection_id=connection_id,
            library_native_id=library_native_id,
            native_id=native_id,
            title=f"{title_prefix} {index}",
            synced_at=now,
        )
        db_session.add(row)
        rows.append(row)
    db_session.commit()
    for row in rows:
        db_session.refresh(row)
    return rows


def seed_series_in_scope(
    db_session,
    connection_id: str,
    series_id: str,
    *,
    app_user_id: str = APP_USER_ID,
    library_native_id: str = "1",
    native_id: str = "guid-123",
    title: str = "Cached Show",
    provider_metadata: dict | None = None,
) -> None:
    """Seed in-scope library + cached series for detail/resume/episodes routes."""
    seed_cached_libraries(
        db_session,
        connection_id,
        [{"native_id": library_native_id, "title": "TV Shows", "in_scope": True}],
        app_user_id=app_user_id,
    )
    from datetime import UTC, datetime

    from wheeloffish.db.models.cached_series import CachedSeries

    db_session.add(
        CachedSeries(
            id=series_id,
            app_user_id=app_user_id,
            connection_id=connection_id,
            library_native_id=library_native_id,
            native_id=native_id,
            title=title,
            provider_metadata=provider_metadata,
            synced_at=datetime.now(UTC),
        )
    )
    db_session.commit()
