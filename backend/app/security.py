"""API authentication.

A single static bearer token (``LANDSEER_API_TOKEN``) gates the ``/api/v1``
surface. When no token is configured the dependency is a no-op so local/dev/test
runs stay open; production is expected to set the token. The comparison is
constant-time to avoid leaking the token via response timing.
"""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

# auto_error=False so we can allow anonymous access when auth is disabled and
# emit our own 401 (with WWW-Authenticate) when it's enabled.
_bearer = HTTPBearer(auto_error=False)


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    expected = get_settings().api_token
    if not expected:
        return  # auth disabled
    if credentials is None or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
