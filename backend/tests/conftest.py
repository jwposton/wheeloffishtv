import pytest
from alembic.config import Config

from alembic import command
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.db.session import get_engine, reset_session_state

# Valid 32-byte hex key for all tests
TEST_SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure WOF_SECRET_KEY is set for every test."""
    monkeypatch.setenv("WOF_SECRET_KEY", TEST_SECRET_KEY)
    get_settings.cache_clear()
    reset_session_state()


@pytest.fixture
def settings() -> Settings:
    """Settings loaded with test secret key."""
    get_settings.cache_clear()
    return Settings(WOF_SECRET_KEY=TEST_SECRET_KEY)


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
