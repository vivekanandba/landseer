"""Shared pytest fixtures: an isolated in-memory database session per test,
plus a reusable API client and a lightweight property factory."""

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture
def client():
    """A TestClient bound to the app, sharing the in-memory engine. Pair with the
    ``session`` fixture (which creates/drops tables) in endpoint tests."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def make_property(session):
    """Factory: create and persist a Property via the service layer."""
    from app.services import property_service as props

    def _make(name: str, **fields):
        return props.create_property(session, name=name, **fields)

    return _make
