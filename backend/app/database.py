"""Database engine and session management."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.models.base import Base

_engine: Engine = None
_SessionLocal: sessionmaker = None


def _connect_args(database_url: str) -> dict:
    # SQLite needs this flag to be shared across the threads FastAPI uses.
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _engine_kwargs(url: str) -> dict:
    """Build create_engine keyword arguments for a database URL.

    SQLite gets the single-connection handling the test/dev path needs; a real
    server database gets pool_pre_ping plus configurable pool sizing.
    """
    kwargs = {"future": True, "connect_args": _connect_args(url)}
    if url.startswith("sqlite"):
        # An in-memory SQLite database lives inside a single connection; force
        # all sessions (including FastAPI's threadpool workers) to share it.
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        return kwargs
    settings = get_settings()
    kwargs.update(
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
    )
    return kwargs


def init_engine(database_url: str = None) -> Engine:
    """(Re)initialise the global engine and session factory.

    Passing an explicit ``database_url`` is how the test suite swaps in an
    in-memory SQLite database.
    """
    global _engine, _SessionLocal
    url = database_url or get_settings().database_url
    _engine = create_engine(url, **_engine_kwargs(url))
    if url.startswith("sqlite"):
        _enable_sqlite_fk(_engine)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)
    return _engine


def _enable_sqlite_fk(engine: Engine) -> None:
    """SQLite ships with foreign-key enforcement OFF per connection. Turn it on
    so cascade deletes and FK constraints behave the same as in PostgreSQL
    (otherwise deleting a parent silently leaves orphaned children)."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine() -> Engine:
    if _engine is None:
        init_engine()
    return _engine


def create_all() -> None:
    """Create every table. Used in tests and first-run bootstrapping."""
    Base.metadata.create_all(bind=get_engine())


def drop_all() -> None:
    Base.metadata.drop_all(bind=get_engine())


def get_sessionmaker() -> sessionmaker:
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session context: commit on success, rollback on error."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
