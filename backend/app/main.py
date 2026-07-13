"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import documents, notifications, preferences, properties, surveys
from app.config import get_settings
from app.database import create_all

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For local/dev convenience. Production uses Alembic migrations instead.
    if settings.debug:
        create_all()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Land search and evaluation system for Vellore, Tamil Nadu",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(properties.router)
app.include_router(preferences.router)
app.include_router(surveys.router)
app.include_router(notifications.router)
app.include_router(documents.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": app.version}
