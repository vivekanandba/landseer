"""Global exception handling.

Registers app-wide handlers so that any domain exception, database integrity
error, or otherwise-uncaught error is rendered as a consistent JSON envelope:

    {"error": {"type": "...", "message": "...", "request_id": "..."}}

Routers still convert domain exceptions to ``HTTPException`` for precise,
per-endpoint status codes; these handlers are the safety net that (a) keeps any
domain exception that slips through mapped to the right status, (b) turns a DB
``IntegrityError`` into a 409 instead of a 500, and (c) ensures a truly
unexpected error is logged with its traceback and returned as a generic 500 that
never leaks internals to the client.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.logging_config import get_logger
from app.request_context import get_request_id
from app.services.broker_service import BrokerNotFound
from app.services.comparison_service import DuplicateComparison
from app.services.matching_service import (
    DuplicatePreference,
    InvalidPreference,
    PreferenceNotFound,
)
from app.services.property_service import DuplicateProperty, PropertyNotFound
from app.services.survey_service import InvalidBoundary

logger = get_logger("errors")

# Domain exception -> HTTP status. Mirrors the per-router mapping so behaviour is
# identical whether a router catches the exception or it reaches the net.
_DOMAIN_STATUS = (
    (PropertyNotFound, 404),
    (BrokerNotFound, 404),
    (PreferenceNotFound, 404),
    (DuplicateProperty, 409),
    (DuplicatePreference, 409),
    (DuplicateComparison, 409),
    (InvalidPreference, 422),
    (InvalidBoundary, 422),
)


def _envelope(status_code: int, type_name: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": type_name,
                "message": message,
                "request_id": get_request_id() or None,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    def _make_domain_handler(status_code: int):
        async def handler(request: Request, exc: Exception) -> JSONResponse:
            return _envelope(status_code, type(exc).__name__, str(exc))

        return handler

    for exc_type, status_code in _DOMAIN_STATUS:
        app.add_exception_handler(exc_type, _make_domain_handler(status_code))

    async def integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("integrity error on %s %s: %s", request.method, request.url.path, exc)
        return _envelope(409, "IntegrityError", "The request conflicts with existing data.")

    app.add_exception_handler(IntegrityError, integrity_handler)

    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return _envelope(500, "InternalServerError", "An internal error occurred.")

    app.add_exception_handler(Exception, unhandled_handler)
