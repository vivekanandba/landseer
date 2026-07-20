"""Integration tests for meta endpoints and cross-cutting middleware:
readiness, request-ID propagation, and CORS wiring."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_static_liveness():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_checks_database(session):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_response_carries_request_id_header():
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_request_id_is_echoed_when_supplied():
    resp = client.get("/health", headers={"X-Request-ID": "trace-42"})
    assert resp.headers.get("X-Request-ID") == "trace-42"


def test_cors_middleware_is_installed():
    assert any(m.cls is CORSMiddleware for m in app.user_middleware)
