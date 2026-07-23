"""Google-only authentication.

Flow: the SPA obtains a Google ID token (Google Identity Services), POSTs it to
``/api/v1/auth/session``; we verify the token with Google, check the email
against the allowlist, and issue a short-lived HMAC-signed session token that the
SPA sends as a bearer on later requests. There is no other way in — no static
token, no password.

The session token is a compact ``<base64url(payload)>.<base64url(hmac)>`` (stdlib
only). Google ID-token verification goes through Google's tokeninfo endpoint and
is isolated behind ``_google_verifier`` so tests can stub it.
"""

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("auth")
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


# --- session token (HMAC-signed; stdlib) ------------------------------------
def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64u_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(body: str, secret: str) -> str:
    return _b64u(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())


def issue_session(email: str, secret: str, ttl_hours: int) -> str:
    payload = {"email": email, "exp": int(time.time()) + ttl_hours * 3600}
    body = _b64u(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body, secret)}"


def verify_session(token: str, secret: str):
    """Return the payload dict if the token is authentic and unexpired, else None."""
    if not token or not secret or "." not in token:
        return None
    body, sig = token.split(".", 1)
    if not hmac.compare_digest(sig, _sign(body, secret)):
        return None
    try:
        payload = json.loads(_b64u_decode(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


# --- Google ID-token verification (isolated for testing) --------------------
def verify_google_id_token(id_token: str) -> dict:  # pragma: no cover - network
    url = f"{TOKENINFO_URL}?id_token={urllib.parse.quote(id_token)}"
    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310 (fixed https host)
        return json.loads(resp.read().decode())


_google_verifier = verify_google_id_token


# --- endpoints (NOT behind require_auth — this is how you log in) -----------
class SessionRequest(BaseModel):
    credential: str  # Google ID token from the "Sign in with Google" flow


class SessionResponse(BaseModel):
    session: str
    email: str
    expires_in: int


@router.get("/config")
def auth_config() -> dict:
    """Public: lets the SPA render the Google button. Exposes only the (public)
    client id and whether auth is enforced."""
    s = get_settings()
    return {"google_client_id": s.google_client_id, "auth_required": s.auth_required}


@router.post("/session", response_model=SessionResponse)
def create_session(req: SessionRequest) -> SessionResponse:
    s = get_settings()
    if not (s.session_secret and s.google_client_id):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication is not configured")
    try:
        claims = _google_verifier(req.credential)
    except Exception as exc:  # network / parse / invalid token
        logger.warning("google id-token verification failed: %s", exc)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token") from exc

    email = (claims.get("email") or "").lower()
    email_verified = str(claims.get("email_verified", "false")).lower() == "true"
    if claims.get("aud") != s.google_client_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token audience mismatch")
    if not email_verified or email not in s.allowed_email_list():
        logger.warning("login denied for email=%r", email)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not allowed")

    token = issue_session(email, s.session_secret, s.session_ttl_hours)
    return SessionResponse(session=token, email=email, expires_in=s.session_ttl_hours * 3600)
