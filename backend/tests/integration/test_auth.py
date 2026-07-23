"""Auth tests: Google-only login. /api/v1 is open when auth is disabled
(local/dev/test) and, when enforced, requires a valid session token minted from a
Google login for an allowlisted email. There is no static-token path."""

import pytest

from app import auth
from app.config import get_settings

ALLOWED = "owner@example.com"


@pytest.fixture
def enforced(monkeypatch):
    """Turn on Google-auth enforcement with a known session secret + allowlist."""
    s = get_settings()
    monkeypatch.setattr(s, "auth_required", True)
    monkeypatch.setattr(s, "google_client_id", "client-123.apps.googleusercontent.com")
    monkeypatch.setattr(s, "session_secret", "unit-test-secret")
    monkeypatch.setattr(s, "allowed_emails", ALLOWED)
    return s


def _session(email=ALLOWED, secret="unit-test-secret", ttl=1):
    return auth.issue_session(email, secret, ttl)


# ---- session-token primitives -------------------------------------------------
def test_session_roundtrip_and_tamper():
    tok = auth.issue_session(ALLOWED, "sekret", 1)
    assert auth.verify_session(tok, "sekret")["email"] == ALLOWED
    assert auth.verify_session(tok, "wrong-secret") is None  # bad key
    body, sig = tok.split(".", 1)
    assert auth.verify_session(f"{body}.{sig}x", "sekret") is None  # tampered sig


def test_session_expiry(monkeypatch):
    tok = auth.issue_session(ALLOWED, "sekret", ttl_hours=1)
    assert auth.verify_session(tok, "sekret") is not None
    monkeypatch.setattr(auth.time, "time", lambda: 10**11)  # jump far into the future
    assert auth.verify_session(tok, "sekret") is None


# ---- enforcement on /api/v1 ---------------------------------------------------
def test_open_when_auth_disabled(client, session):
    assert client.get("/api/v1/properties").status_code == 200


def test_requires_session_when_enforced(client, session, enforced):
    assert client.get("/api/v1/properties").status_code == 401


def test_valid_session_allows(client, session, enforced):
    resp = client.get("/api/v1/properties", headers={"Authorization": f"Bearer {_session()}"})
    assert resp.status_code == 200


def test_session_for_other_email_rejected(client, session, enforced):
    tok = _session(email="intruder@example.com")
    resp = client.get("/api/v1/properties", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 401


def test_health_and_ready_stay_open(client, session, enforced):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


# ---- login endpoints ----------------------------------------------------------
def test_auth_config_exposes_client_id(client, enforced):
    body = client.get("/api/v1/auth/config").json()
    assert body["google_client_id"] == "client-123.apps.googleusercontent.com"
    assert body["auth_required"] is True


def test_session_endpoint_issues_token_for_allowed_email(client, session, enforced, monkeypatch):
    monkeypatch.setattr(
        auth,
        "_google_verifier",
        lambda _cred: {
            "aud": "client-123.apps.googleusercontent.com",
            "email": ALLOWED,
            "email_verified": "true",
        },
    )
    resp = client.post("/api/v1/auth/session", json={"credential": "fake-google-jwt"})
    assert resp.status_code == 200, resp.text
    tok = resp.json()["session"]
    # the issued session actually works against a gated endpoint
    assert (
        client.get("/api/v1/properties", headers={"Authorization": f"Bearer {tok}"}).status_code
        == 200
    )


def test_session_endpoint_rejects_disallowed_email(client, enforced, monkeypatch):
    monkeypatch.setattr(
        auth,
        "_google_verifier",
        lambda _cred: {
            "aud": "client-123.apps.googleusercontent.com",
            "email": "nope@example.com",
            "email_verified": "true",
        },
    )
    resp = client.post("/api/v1/auth/session", json={"credential": "fake"})
    assert resp.status_code == 403


def test_session_endpoint_rejects_audience_mismatch(client, enforced, monkeypatch):
    monkeypatch.setattr(
        auth,
        "_google_verifier",
        lambda _cred: {"aud": "someone-else", "email": ALLOWED, "email_verified": "true"},
    )
    resp = client.post("/api/v1/auth/session", json={"credential": "fake"})
    assert resp.status_code == 401


def test_refuses_to_start_when_enforced_but_unconfigured(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    s = get_settings()
    monkeypatch.setattr(s, "auth_required", True)
    monkeypatch.setattr(s, "google_client_id", None)
    monkeypatch.setattr(s, "session_secret", None)
    monkeypatch.setattr(s, "allowed_emails", "")
    with pytest.raises(RuntimeError, match="Refusing to start"):
        with TestClient(app):
            pass
