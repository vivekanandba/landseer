"""Application configuration.

Settings are loaded from environment variables (and an optional ``.env`` file).
Tests override ``database_url`` to point at an in-memory SQLite database so the
suite runs without a live PostgreSQL/PostGIS instance.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LANDSEER_", extra="ignore")

    app_name: str = "Landseer"
    debug: bool = False

    # Static bearer token that gates all /api/v1 endpoints. When unset (the
    # default), the API is open — intended only for local/dev/test. Production
    # must set LANDSEER_API_TOKEN.
    api_token: Optional[str] = None

    # Fail-closed guard: when true, the app refuses to start unless api_token is
    # set. Set LANDSEER_AUTH_REQUIRED=true in any environment that must be
    # authenticated, so a missing token is a boot failure rather than a silently
    # open API.
    auth_required: bool = False

    # Per-client (per-IP) request cap for /api/v1, per 60s window. 0 disables
    # rate limiting (the default).
    rate_limit_per_minute: int = 0

    # Application log level (LANDSEER_LOG_LEVEL). Standard names: DEBUG/INFO/...
    log_level: str = "INFO"

    # Cross-origin origins allowed to call the API. Empty by default (no
    # cross-origin access). Set LANDSEER_CORS_ORIGINS to a JSON list, e.g.
    # '["https://app.example.com"]'.
    cors_origins: List[str] = []

    # Default to local PostgreSQL; tests inject an SQLite URL instead.
    database_url: str = "postgresql+psycopg2://localhost/landseer"

    # Connection-pool tuning (ignored for SQLite). pool_pre_ping is always on for
    # server databases so a stale/dropped connection is detected and replaced
    # rather than surfacing as an error on the next query.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800

    # Storage roots (relative to repo root by default).
    data_dir: str = "data"
    onedrive_root: str = "data/imports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
