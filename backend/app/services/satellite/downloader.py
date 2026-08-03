"""
Satellite image downloader.

Coordinates the download process:

    (future API) -> Downloader -> Satellite Provider -> Image

This module owns persistence (saving the provider's raw bytes to a
temporary file) and provider selection. It does not know Sentinel Hub's
request format — that stays entirely inside sentinel.py — and it does
not touch the prediction pipeline. Swapping the default provider later
(Google Earth Engine, Planet, Mapbox) means changing only
`get_default_provider` below.
"""

import uuid
from pathlib import Path
from typing import Dict, Final, Optional

from app.core.logging import get_logger
from app.core.satellite_settings import satellite_settings
from app.services.satellite.models import SatelliteImageRequest, SatelliteImageResult
from app.services.satellite.provider import SatelliteProvider
from app.services.satellite.sentinel import SentinelProvider

logger = get_logger(__name__)

# backend/app/services/satellite/downloader.py -> satellite -> services
# -> app -> backend (project's backend/ root).
BACKEND_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_TEMP_DIR: Final[Path] = BACKEND_ROOT / "temp" / "satellite"

DEFAULT_FILE_EXTENSION: Final[str] = "png"

_EXTENSION_BY_CONTENT_TYPE: Final[Dict[str, str]] = {
    "image/png": "png",
    "image/tiff": "tiff",
    "image/jpeg": "jpg",
}


def get_default_provider() -> SatelliteProvider:
    """
    Return the satellite provider to use when the caller does not
    supply one explicitly.

    Currently always Sentinel Hub. This is the single point of change
    for introducing a future provider (Google Earth Engine, Planet,
    Mapbox): implement `SatelliteProvider` and return an instance of it
    here — no other function in this module, or in the prediction
    pipeline, needs to change.

    Returns:
        A SatelliteProvider instance.
    """
    return SentinelProvider()


def download_satellite_image(
    request: SatelliteImageRequest,
    provider: Optional[SatelliteProvider] = None,
) -> SatelliteImageResult:
    """
    Retrieve a satellite image for the given coordinates and save it to
    a temporary file.

    Args:
        request: The coordinates, buffer, size, and lookback window
            describing the image to retrieve.
        provider: The satellite provider to use. Defaults to
            `get_default_provider()`. Accepting an explicit provider
            here (rather than importing SentinelProvider directly at
            every call site) is what lets a future provider be swapped
            in without touching any calling code.

    Returns:
        A SatelliteImageResult pointing at the saved temporary image
        file, along with retrieval metadata.

    Raises:
        SatelliteAuthenticationError: If the provider's authentication
            fails.
        SatelliteImageRetrievalError: If the image could not be
            retrieved.
    """
    active_provider = provider or get_default_provider()

    raw_image = active_provider.fetch_image(request)
    image_path = _save_to_temp_file(raw_image.content, raw_image.content_type)

    logger.info(
        "Saved satellite image | provider=%s | path=%s | bytes=%d",
        raw_image.provider_name,
        image_path,
        len(raw_image.content),
    )

    return SatelliteImageResult(
        image_path=image_path,
        provider=raw_image.provider_name,
        latitude=request.latitude,
        longitude=request.longitude,
        bounding_box=request.bounding_box(),
        acquisition_date=raw_image.acquisition_date,
        file_size_bytes=len(raw_image.content),
    )


def _save_to_temp_file(content: bytes, content_type: str) -> Path:
    """
    Write image bytes to a uniquely named temporary file.

    Args:
        content: Raw image bytes returned by a provider.
        content_type: The image's MIME type, used to choose a file
            extension.

    Returns:
        The path to the saved temporary file.
    """
    temp_dir = _resolve_temp_dir()
    extension = _EXTENSION_BY_CONTENT_TYPE.get(content_type, DEFAULT_FILE_EXTENSION)
    file_path = temp_dir / f"{uuid.uuid4().hex}.{extension}"

    file_path.write_bytes(content)

    return file_path


def _resolve_temp_dir() -> Path:
    """
    Return the directory temporary satellite images are saved to,
    creating it if it does not already exist.

    Uses `satellite_settings.SATELLITE_TEMP_DIR` if explicitly
    configured, otherwise defaults to `backend/temp/satellite/`.

    Returns:
        The resolved, existing temporary directory path.
    """
    configured_dir = satellite_settings.SATELLITE_TEMP_DIR
    temp_dir = Path(configured_dir) if configured_dir else DEFAULT_TEMP_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir
