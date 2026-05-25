import json
from pathlib import Path

import httpx
import pytest
from alembic.config import Config
from httpx import ASGITransport

from alembic import command
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.session import get_engine, reset_session_state
from wheeloffish.main import app

# Valid 32-byte hex key for all tests
TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
APP_USER_ID = "00000000-0000-4000-8000-000000000001"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
    """Create a test connection with mocked provider ping."""
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
        with patch("wheeloffish.core.connections.build_ephemeral_provider", return_value=provider):
            return await create_connection(
                db_session,
                vault,
                settings,
                app_user_id=app_user_id,
                **params,
            )

    return _factory
