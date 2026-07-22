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

    # --- Authentication (Google Sign-In only) ---
    # /api/v1 is gated by a Google-issued login: the SPA signs in with Google,
    # the backend verifies the ID token, checks the email allowlist, and issues a
    # short-lived HMAC session token. There is no static-token fallback.
    auth_required: bool = False  # when true, enforce login (and fail closed if unconfigured)
    google_client_id: Optional[str] = None  # OAuth 2.0 Web client id (public)
    session_secret: Optional[str] = None  # HMAC key for signing session tokens
    session_ttl_hours: int = 12
    # Comma-separated allowlist of Google emails permitted to sign in.
    allowed_emails: str = ""

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

    def allowed_email_list(self) -> List[str]:
        return [e.strip().lower() for e in self.allowed_emails.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
