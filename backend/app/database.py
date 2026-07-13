"""Database engine and session management."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
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


def init_engine(database_url: str = None) -> Engine:
    """(Re)initialise the global engine and session factory.

    Passing an explicit ``database_url`` is how the test suite swaps in an
    in-memory SQLite database.
    """
    global _engine, _SessionLocal
    url = database_url or get_settings().database_url
    kwargs = {"future": True, "connect_args": _connect_args(url)}
    # An in-memory SQLite database lives inside a single connection; force all
    # sessions (including FastAPI's threadpool workers) to share one connection.
    if url.startswith("sqlite") and ":memory:" in url:
        kwargs["poolclass"] = StaticPool
    _engine = create_engine(url, **kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)
    return _engine


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
