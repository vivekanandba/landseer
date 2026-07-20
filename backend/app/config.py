"""Application configuration.

Settings are loaded from environment variables (and an optional ``.env`` file).
Tests override ``database_url`` to point at an in-memory SQLite database so the
suite runs without a live PostgreSQL/PostGIS instance.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LANDSEER_", extra="ignore")

    app_name: str = "Landseer"
    debug: bool = False

    # Application log level (LANDSEER_LOG_LEVEL). Standard names: DEBUG/INFO/...
    log_level: str = "INFO"

    # Cross-origin origins allowed to call the API. Empty by default (no
    # cross-origin access). Set LANDSEER_CORS_ORIGINS to a JSON list, e.g.
    # '["https://app.example.com"]'.
    cors_origins: List[str] = []

    # Default to local PostgreSQL; tests inject an SQLite URL instead.
    database_url: str = "postgresql+psycopg2://localhost/landseer"

    # Storage roots (relative to repo root by default).
    data_dir: str = "data"
    onedrive_root: str = "data/imports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
