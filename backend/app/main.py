"""FastAPI application entrypoint."""

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import (
    brokers,
    comparisons,
    documents,
    imports,
    notifications,
    preferences,
    properties,
    surveys,
)
from app.config import get_settings
from app.database import create_all, get_engine
from app.errors import error_response, register_exception_handlers
from app.logging_config import configure_logging, get_logger
from app.request_context import set_request_id
from app.security import require_auth

settings = get_settings()

# Configure logging at import time so log lines are structured even before the
# lifespan runs (e.g. under the test client, which may not enter the lifespan).
configure_logging(settings.log_level)
logger = get_logger("app")
request_logger = get_logger("request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.api_token:
        logger.warning(
            "No LANDSEER_API_TOKEN set: the /api/v1 surface is UNAUTHENTICATED. "
            "Set a token in any non-local environment."
        )
    # For local/dev convenience. Production uses Alembic migrations instead.
    if settings.debug:
        logger.warning(
            "DEBUG mode is on: auto-creating tables via create_all(). "
            "Do NOT enable LANDSEER_DEBUG in production — use Alembic migrations."
        )
        create_all()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Land search and evaluation system for Vellore, Tamil Nadu",
    version="0.1.0",
    lifespan=lifespan,
)

# A wildcard origin cannot be combined with credentials (browsers/Starlette
# refuse to emit `Access-Control-Allow-Origin: *` alongside credentials), so we
# drop credentials in that case rather than silently rejecting every request.
_cors_allow_credentials = "*" not in settings.cors_origins
if not _cors_allow_credentials:
    logger.warning("CORS origins include '*'; disabling allow_credentials for compatibility.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=_cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Assign/propagate a request-ID and log each request with its duration."""
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    set_request_id(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        request_logger.exception(
            "request failed method=%s path=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    request_logger.info(
        "method=%s path=%s status=%s duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


# All /api/v1 routers are gated by the bearer-token dependency (a no-op when no
# token is configured). /health, /ready and /docs stay open.
_v1_auth = [Depends(require_auth)]
app.include_router(properties.router, dependencies=_v1_auth)
app.include_router(preferences.router, dependencies=_v1_auth)
app.include_router(surveys.router, dependencies=_v1_auth)
app.include_router(notifications.router, dependencies=_v1_auth)
app.include_router(documents.router, dependencies=_v1_auth)
app.include_router(brokers.router, dependencies=_v1_auth)
app.include_router(comparisons.router, dependencies=_v1_auth)
app.include_router(imports.router, dependencies=_v1_auth)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness: the process is up and serving. Does not touch the database."""
    return {"status": "ok", "app": settings.app_name, "version": app.version}


@app.get("/ready", tags=["meta"])
def ready() -> dict:
    """Readiness: verifies the database is reachable. Returns 503 if not.

    Probes on a dedicated short-lived connection rather than the request-scoped
    ``get_db`` session, whose post-request ``commit()`` would itself fail on a
    broken transaction and mask the 503 as a 500.
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("readiness check failed: %s", exc)
        return error_response(503, "DatabaseUnavailable", "The database is not reachable.")
    return {"status": "ready"}
