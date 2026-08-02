"""
Application configuration module.

Centralizes all environment-driven configuration for the VanRakshak AI
backend using Pydantic Settings. No other module should read environment
variables directly; everything flows through this single Settings object.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines all configurable values for the VanRakshak AI backend.

    Values are read from environment variables (or a `.env` file) at
    process startup. Defaults below are for local development only;
    production deployments must override these via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application identity ---
    APP_NAME: str = Field(
        default="VanRakshak AI",
        description="Human-readable application name.",
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Current application version.",
    )
    APP_DESCRIPTION: str = Field(
        default="Protecting Forests Through Artificial Intelligence",
        description="Short application tagline/description.",
    )

    # --- Runtime environment ---
    ENVIRONMENT: str = Field(
        default="development",
        description="Deployment environment: development, staging, or production.",
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode (verbose errors, auto-reload friendly).",
    )

    # --- Server ---
    HOST: str = Field(
        default="0.0.0.0",
        description="Host interface the server binds to.",
    )
    PORT: int = Field(
        default=8000,
        description="Port the server listens on.",
    )

    # --- Logging ---
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    )
    LOG_DIR: str = Field(
        default="logs",
        description="Directory where log files are written, relative to backend/.",
    )
    LOG_FILE_NAME: str = Field(
        default="vanrakshak.log",
        description="Log file name.",
    )

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default=[
            # Local frontend (development)
            "http://localhost:5500",
            "http://127.0.0.1:5500",

            # Local backend docs/testing
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="List of origins allowed to access the API.",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached, singleton Settings instance.

    Using lru_cache ensures environment variables are parsed only once
    per process, and every module that needs configuration receives the
    same Settings object instead of re-reading the environment.

    Returns:
        The process-wide Settings singleton.
    """
    return Settings()


settings: Settings = get_settings()