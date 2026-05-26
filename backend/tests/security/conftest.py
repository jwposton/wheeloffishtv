"""Shared DB for auth guard tests — one migration per session, not per parametrized case."""

from __future__ import annotations

from collections.abc import Iterable

import pytest
from alembic.config import Config
from starlette.testclient import TestClient

from alembic import command
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.db.session import reset_session_state
from wheeloffish.main import create_app

TEST_SECRET_KEY = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)


def _create_guard_app(database_url: str):
    get_settings.cache_clear()
    reset_session_state()
    settings = Settings(WOF_SECRET_KEY=TEST_SECRET_KEY, DATABASE_URL=database_url)
    return create_app(settings)


@pytest.fixture(scope="session")
def guard_database_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("guard") / "guard.db"
    database_url = f"sqlite:///{db_path}"
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")
    return database_url


@pytest.fixture
def guard_client(
    monkeypatch: pytest.MonkeyPatch,
    guard_database_url: str,
) -> Iterable[TestClient]:
    monkeypatch.setenv("WOF_SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setenv("DATABASE_URL", guard_database_url)
    with TestClient(_create_guard_app(guard_database_url)) as client:
        yield client
