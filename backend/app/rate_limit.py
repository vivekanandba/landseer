"""Lightweight in-process rate limiting.

A fixed-window per-client limiter, gated by ``LANDSEER_RATE_LIMIT_PER_MINUTE``
(0 = disabled, the default). Deliberately dependency-free and in-memory: it
suits a single-process deployment. A multi-process/replicated deployment would
need a shared store (e.g. Redis) instead — this is the seam for that.

Clients are keyed by peer IP. Behind a proxy that terminates the connection you
would key on a validated ``X-Forwarded-For`` instead; not done here to avoid
trusting a spoofable header by default.
"""

import threading
import time
from typing import Dict, List, Tuple

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("ratelimit")

_WINDOW_SECONDS = 60.0


class _FixedWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: Dict[str, List[float]] = {}  # key -> [window_start, count]

    def check(self, key: str, limit: int, now: float) -> Tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        with self._lock:
            entry = self._hits.get(key)
            if entry is None or now - entry[0] >= _WINDOW_SECONDS:
                self._hits[key] = [now, 1]
                return True, 0
            entry[1] += 1
            if entry[1] > limit:
                return False, int(_WINDOW_SECONDS - (now - entry[0])) + 1
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_limiter = _FixedWindowLimiter()


def rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_minute
    if not limit or limit <= 0:
        return  # disabled
    key = request.client.host if request.client else "anonymous"
    allowed, retry_after = _limiter.check(key, limit, time.monotonic())
    if not allowed:
        logger.warning("rate limited key=%s path=%s", key, request.url.path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
