"""Shared pytest fixtures: an isolated in-memory database session per test."""
import pytest

from app.database import create_all, drop_all, get_sessionmaker, init_engine


@pytest.fixture(scope="session", autouse=True)
def _engine():
    init_engine("sqlite+pysqlite:///:memory:")
    yield


@pytest.fixture
def session():
    create_all()
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
        drop_all()
