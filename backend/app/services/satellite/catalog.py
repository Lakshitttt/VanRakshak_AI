"""
Sentinel-2 catalog search.

Queries the Copernicus Data Space Ecosystem's STAC-compliant Catalog
API to find which Sentinel-2 L2A acquisitions are available for a
given area and time window, so the exact best (least-cloudy) scene can
be requested from the Process API — instead of letting the Process API
pick one internally via `mosaickingOrder`.

This module does not perform authentication itself: it is handed an
already-obtained OAuth2 access token by its caller (SentinelProvider),
so token acquisition and caching stays in exactly one place.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Final, List, Optional

import requests

from app.core.logging import get_logger
from app.services.satellite.exceptions import (
    SatelliteImageRetrievalError,
    SatelliteQuotaError,
    SatelliteNetworkError,
)
logger = get_logger(__name__)

# --- Copernicus Data Space Catalog API (STAC) ---
CATALOG_URL: Final[str] = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"
CATALOG_COLLECTION: Final[str] = "sentinel-2-l2a"
CATALOG_SEARCH_LIMIT: Final[int] = 100
CATALOG_REQUEST_TIMEOUT_SECONDS: Final[int] = 30


@dataclass(frozen=True)
class CatalogScene:
    """
    A single Sentinel-2 L2A acquisition found via the Catalog API.

    Attributes:
        scene_id: The scene's STAC feature ID.
        acquisition_date: When the scene was acquired, if the Catalog
            API reported a parsable datetime.
        cloud_coverage: The scene's cloud cover percentage (0-100), if
            reported.
    """

    scene_id: str
    acquisition_date: Optional[datetime]
    cloud_coverage: Optional[float]


def find_best_scene(
    access_token: str,
    bbox: List[float],
    time_from: datetime,
    time_to: datetime,
) -> Optional[CatalogScene]:
    """
    Search the Catalog API for Sentinel-2 L2A acquisitions covering
    `bbox` within [time_from, time_to], and return the one with the
    lowest cloud coverage.

    Args:
        access_token: A valid Sentinel Hub / CDSE OAuth2 bearer token,
            obtained by the caller (SentinelProvider._get_access_token).
            This function does not authenticate on its own.
        bbox: [min_lon, min_lat, max_lon, max_lat]. The Catalog API's
            STAC bbox is always in (lon, lat) order, so this can be
            passed straight from `BoundingBox.as_list()`.
        time_from: Start of the search window (inclusive).
        time_to: End of the search window (inclusive).

    Returns:
        The best-matching CatalogScene (lowest cloud coverage), or
        None if no scenes were found.

    Raises:
        SatelliteImageRetrievalError: If the Catalog API is unreachable
            or returns an error response.
    """
    request_body: Dict[str, Any] = {
        "collections": [CATALOG_COLLECTION],
        "bbox": bbox,
        "datetime": f"{_to_iso(time_from)}/{_to_iso(time_to)}",
        "limit": CATALOG_SEARCH_LIMIT,
    }

    try:
        response = requests.post(
            CATALOG_URL,
            json=request_body,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=CATALOG_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise SatelliteNetworkError(
            "Unable to reach the Sentinel-2 Catalog API. Please check your internet connection and try again.",
            details=str(exc),
        ) from exc

    if response.status_code == 401:
        raise SatelliteAuthenticationError(
            "Sentinel Hub authentication was rejected while accessing the Catalog API."
        )

    if response.status_code == 403:
        raise SatelliteQuotaError(
            "Sentinel Hub quota or processing-unit limit has been reached. "
            "Please check your Sentinel Hub account quota or try again later."
        )

    if response.status_code >= 500:
        raise SatelliteServiceError(
            f"Sentinel Hub Catalog API is temporarily unavailable "
            f"(status {response.status_code}). Please try again later."
        )

    if response.status_code != 200:
        raise SatelliteImageRetrievalError(
            f"Catalog API returned status {response.status_code} while searching for scenes."
        )

    scenes = _parse_scenes(response.json())

    logger.info(
        "Catalog API returned %d scene(s) | bounding_box=%s | time_range=%s/%s",
        len(scenes),
        bbox,
        _to_iso(time_from),
        _to_iso(time_to),
    )

    if not scenes:
        logger.info("No scenes matched the search criteria; nothing to select.")
        return None

    # Sort locally to guarantee the least cloudy scene is first
    scenes.sort(key=_cloud_coverage_sort_key)
    best = scenes[0]

    # Warning for heavily clouded scenes (e.g., monsoon season)
    if best.cloud_coverage is not None and best.cloud_coverage > 50.0:
        logger.warning(
            "Best available scene still has %.2f%% cloud cover.",
            best.cloud_coverage,
        )

    logger.info(
        "Selected scene: %s | acquisition_date=%s | cloud_coverage=%s%% | bounding_box=%s",
        best.scene_id,
        best.acquisition_date,
        best.cloud_coverage,
        bbox,
    )
    
    return best


def _parse_scenes(payload: Dict[str, Any]) -> List[CatalogScene]:
    """
    Convert a STAC FeatureCollection response body into CatalogScene
    objects, skipping any feature that has no ID.
    """
    scenes: List[CatalogScene] = []

    for feature in payload.get("features", []):
        scene_id = feature.get("id")
        if not scene_id:
            continue

        properties = feature.get("properties", {})
        scenes.append(
            CatalogScene(
                scene_id=scene_id,
                acquisition_date=_parse_datetime(properties.get("datetime")),
                cloud_coverage=_as_float(properties.get("eo:cloud_cover")),
            )
        )

    return scenes


def _cloud_coverage_sort_key(scene: CatalogScene) -> float:
    """
    Sort key ranking scenes by ascending cloud coverage. Scenes with
    unknown cloud coverage sort last rather than raising.
    """
    return scene.cloud_coverage if scene.cloud_coverage is not None else 100.0


def _to_iso(value: datetime) -> str:
    """Format a datetime as the UTC 'Z' ISO 8601 string the Catalog API expects."""
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Best-effort parse of a STAC feature's datetime property."""
    if not value:
        return None

    try:
        # Sentinel/Copernicus timestamps use UTC "Z" and may contain
        # fractional seconds, for example:
        # 2025-10-15T05:31:45.53Z
        # 2025-11-15T05:31:45.4Z
        # 2025-12-15T05:31:45Z
        #
        # Python 3.10.4 does not reliably parse these after converting
        # "Z" to "+00:00", so parse them explicitly and attach UTC.
        if value.endswith("Z"):
            timestamp = value[:-1]

            if "." in timestamp:
                return datetime.strptime(
                    timestamp,
                    "%Y-%m-%dT%H:%M:%S.%f",
                ).replace(tzinfo=timezone.utc)

            return datetime.strptime(
                timestamp,
                "%Y-%m-%dT%H:%M:%S",
            ).replace(tzinfo=timezone.utc)

        # Fallback for timestamps containing an explicit UTC offset.
        return datetime.fromisoformat(value)

    except (TypeError, ValueError):
        logger.warning(
            "Could not parse an acquisition datetime from the Catalog API: %r",
            value,
        )
        return None


def _as_float(value: Any) -> Optional[float]:
    """Best-effort conversion of a cloud coverage value to float; None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None