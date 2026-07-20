"""FastAPI application entrypoint."""

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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
from app.database import create_all, get_db
from app.errors import register_exception_handlers
from app.logging_config import configure_logging, get_logger
from app.request_context import set_request_id

settings = get_settings()

# Configure logging at import time so log lines are structured even before the
# lifespan runs (e.g. under the test client, which may not enter the lifespan).
configure_logging(settings.log_level)
logger = get_logger("app")
request_logger = get_logger("request")


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
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


app.include_router(properties.router)
app.include_router(preferences.router)
app.include_router(surveys.router)
app.include_router(notifications.router)
app.include_router(documents.router)
app.include_router(brokers.router)
app.include_router(comparisons.router)
app.include_router(imports.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness: the process is up and serving. Does not touch the database."""
    return {"status": "ok", "app": settings.app_name, "version": app.version}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)) -> dict:
    """Readiness: verifies the database is reachable. Returns 503 if not."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": "database unavailable"},
        )
    return {"status": "ready"}
