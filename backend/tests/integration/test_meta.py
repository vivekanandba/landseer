"""Integration tests for meta endpoints and cross-cutting middleware:
readiness, request-ID propagation, and CORS wiring.

Uses the shared ``client`` fixture (see tests/conftest.py); ``test_ready`` also
takes ``session`` because it touches the database."""

from fastapi.middleware.cors import CORSMiddleware

from app.main import app


def test_health_is_static_liveness(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_checks_database(client, session):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_response_carries_request_id_header(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_echoed_when_supplied(client):
    resp = client.get("/health", headers={"X-Request-ID": "trace-42"})
    assert resp.headers.get("X-Request-ID") == "trace-42"


def test_cors_middleware_is_installed():
    assert any(m.cls is CORSMiddleware for m in app.user_middleware)
