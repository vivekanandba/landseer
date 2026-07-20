"""Auth tests: /api/v1 is open when no token is configured, and requires a
matching bearer token when one is set. /health and /ready stay open either way."""

import pytest

from app.config import get_settings


@pytest.fixture
def api_token(monkeypatch):
    """Configure a static API token on the cached settings for the test."""
    settings = get_settings()
    monkeypatch.setattr(settings, "api_token", "s3cret-token")
    return "s3cret-token"


def test_open_when_no_token_configured(client, session):
    # Default settings have api_token=None -> endpoints require no auth.
    assert client.get("/api/v1/properties").status_code == 200


def test_requires_token_when_configured(client, session, api_token):
    assert client.get("/api/v1/properties").status_code == 401


def test_rejects_wrong_token(client, session, api_token):
    resp = client.get("/api/v1/properties", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


def test_accepts_correct_token(client, session, api_token):
    resp = client.get("/api/v1/properties", headers={"Authorization": f"Bearer {api_token}"})
    assert resp.status_code == 200


def test_health_and_ready_stay_open_with_token(client, session, api_token):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


def test_auth_required_without_token_refuses_to_start(monkeypatch):
    """Fail-closed: LANDSEER_AUTH_REQUIRED + no token aborts startup (lifespan)."""
    from fastapi.testclient import TestClient

    from app.main import app

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "api_token", None)
    with pytest.raises(RuntimeError, match="refusing to start"):
        with TestClient(app):  # entering the context runs the lifespan
            pass
