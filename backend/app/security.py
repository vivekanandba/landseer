"""API authorization: every ``/api/v1`` route (except ``/api/v1/auth/*``) requires
a valid Google-issued **session token** — see :mod:`app.auth` for how login mints
it. There is no static-token or anonymous path when auth is enforced.

When ``auth_required`` is false (local/dev/test), the dependency is a no-op so the
suite and local runs stay open.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import verify_session
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("auth")
_bearer = HTTPBearer(auto_error=False)


def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    settings = get_settings()
    if not settings.auth_required:
        return  # auth disabled (local/dev/test)

    payload = verify_session(
        credentials.credentials if credentials else "", settings.session_secret or ""
    )
    if payload is None or payload.get("email", "").lower() not in settings.allowed_email_list():
        logger.warning("auth rejected method=%s path=%s", request.method, request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with Google to continue",
            headers={"WWW-Authenticate": "Bearer"},
        )
