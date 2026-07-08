"""FastAPI application entrypoint."""
from fastapi import FastAPI

from app.api.v1 import properties
from app.config import get_settings
from app.database import create_all

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Land search and evaluation system for Vellore, Tamil Nadu",
    version="0.1.0",
)

app.include_router(properties.router)


@app.on_event("startup")
def _startup() -> None:
    # For local/dev convenience. Production uses Alembic migrations instead.
    if settings.debug:
        create_all()


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": app.version}
