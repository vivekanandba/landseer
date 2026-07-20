"""Per-request context propagated via a context variable.

The request-ID is set by the HTTP middleware in :mod:`app.main` and read by the
logging filter (:mod:`app.logging_config`) and the exception handlers
(:mod:`app.errors`) so every log line and error envelope can be correlated to a
single request without threading the value through every call.
"""

import contextvars

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()
