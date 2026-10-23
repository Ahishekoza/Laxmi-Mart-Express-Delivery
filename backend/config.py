"""
Centralized, environment-based application configuration.

All database connection parameters are sourced exclusively from environment
variables (via `.env` in development, real environment variables in
production). Nothing here is hard-coded. `get_settings()` is cached so the
environment is parsed and validated exactly once per process, and fails
fast — at import/startup time — if a required variable is missing or
malformed, rather than failing later on first query.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database connection ---
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- Connection pool tuning ---
    db_pool_size: int = Field(10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(1800, alias="DB_POOL_RECYCLE")

    # --- Behavior toggles ---
    db_echo: bool = Field(False, alias="DB_ECHO")
    environment: str = Field("development", alias="ENVIRONMENT")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql://' or "
                "'postgresql+psycopg2://' scheme."
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Return a process-wide cached Settings instance.

    Raises a pydantic ValidationError immediately (at first call, which
    happens at import time of database/db.py) if required environment
    variables are missing or invalid — this is the "fail fast at startup"
    behavior required by the specification.
    """
    return Settings()
