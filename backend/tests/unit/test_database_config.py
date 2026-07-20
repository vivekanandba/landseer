"""Unit tests for engine keyword construction (connection pooling)."""

from sqlalchemy.pool import StaticPool

from app.database import _engine_kwargs


def test_sqlite_memory_uses_static_pool_no_server_pooling():
    kwargs = _engine_kwargs("sqlite+pysqlite:///:memory:")
    assert kwargs["poolclass"] is StaticPool
    assert kwargs["connect_args"] == {"check_same_thread": False}
    # Server pool tuning must not leak onto SQLite.
    assert "pool_pre_ping" not in kwargs
    assert "pool_size" not in kwargs


def test_sqlite_file_has_no_server_pool_settings():
    kwargs = _engine_kwargs("sqlite+pysqlite:///./data.db")
    assert "poolclass" not in kwargs  # file-backed: default pool is fine
    assert "pool_pre_ping" not in kwargs


def test_postgres_enables_pre_ping_and_pool_sizing():
    kwargs = _engine_kwargs("postgresql+psycopg2://user:pass@host/db")
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_size"] == 5
    assert kwargs["max_overflow"] == 10
    assert kwargs["pool_recycle"] == 1800
    assert kwargs["connect_args"] == {}
