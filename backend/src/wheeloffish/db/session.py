from collections.abc import Generator

from sqlalchemy import Engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from wheeloffish.core.config import Settings, get_settings
from wheeloffish.db.models.base import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _configure_sqlite_wal(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    settings = settings or get_settings()
    from sqlalchemy import create_engine

    connect_args: dict = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    _engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

    if settings.DATABASE_URL.startswith("sqlite"):
        event.listen(_engine, "connect", _configure_sqlite_wal)

    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal

    engine = get_engine(settings)
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def reset_session_state() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_database(session: Session) -> bool:
    session.execute(text("SELECT 1"))
    return True


__all__ = [
    "Base",
    "check_database",
    "get_db",
    "get_engine",
    "get_session_factory",
    "reset_session_state",
]
