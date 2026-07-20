"""Integration tests: /api/v1 rate limiting is off by default and enforced when
configured."""

import pytest

from app import rate_limit as rl
from app.config import get_settings


@pytest.fixture
def limited(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_per_minute", 3)
    rl._limiter.reset()
    yield
    rl._limiter.reset()


def test_disabled_by_default(client, session):
    for _ in range(15):
        assert client.get("/api/v1/properties").status_code == 200


def test_enforced_when_configured(client, session, limited):
    for _ in range(3):
        assert client.get("/api/v1/properties").status_code == 200
    resp = client.get("/api/v1/properties")
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After")
