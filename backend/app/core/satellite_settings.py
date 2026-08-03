"""
Satellite configuration module.

Centralizes Sentinel Hub credentials and satellite image storage
configuration, kept separate from the application's general settings
(app/core/settings.py). Mirrors that module's pattern exactly — same
Pydantic Settings mechanism, same singleton caching — so this is a
relocation of values, not a new configuration approach.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SatelliteSettings(BaseSettings):
    """
    Defines Sentinel Hub credentials and satellite storage configuration.

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

    # --- Sentinel Hub credentials ---
    SENTINEL_HUB_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Sentinel Hub OAuth2 client ID. Required to retrieve satellite imagery.",
    )
    SENTINEL_HUB_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="Sentinel Hub OAuth2 client secret. Required to retrieve satellite imagery.",
    )

    # --- Satellite image storage ---
    SATELLITE_TEMP_DIR: Optional[str] = Field(
        default=None,
        description=(
            "Directory downloaded satellite images are saved to. "
            "Defaults to backend/temp/satellite/ if not set."
        ),
    )


@lru_cache
def get_satellite_settings() -> SatelliteSettings:
    """
    Return a cached, singleton SatelliteSettings instance.

    Using lru_cache ensures environment variables are parsed only once
    per process, and every module that needs satellite configuration
    receives the same SatelliteSettings object instead of re-reading
    the environment.

    Returns:
        The process-wide SatelliteSettings singleton.
    """
    return SatelliteSettings()


satellite_settings: SatelliteSettings = get_satellite_settings()