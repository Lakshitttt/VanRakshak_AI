"""
Reusable data models for the satellite subsystem.

These are plain, framework-free dataclasses shared by every provider
implementation and the downloader — not FastAPI/Pydantic schemas (those
belong in app/schemas/ if this subsystem ever gains its own API route).
Keeping them here, in one place, is what lets `provider.py`,
`sentinel.py`, and `downloader.py` all agree on the same shapes without
duplicating field definitions or bounding-box math.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Final, List, Optional

# --- Defaults for an unspecified SatelliteImageRequest ---
# 224x224 pixels at Sentinel-2's native 10m/pixel resolution for the
# true-color bands (B02/B03/B04) gives a 2240m x 2240m ground footprint
# — a small, deliberately-sized crop, never a full ~110km Sentinel tile.
DEFAULT_IMAGE_SIZE_PX: Final[int] = 224
DEFAULT_BUFFER_METERS: Final[float] = DEFAULT_IMAGE_SIZE_PX * 10.0
DEFAULT_DAYS_BACK: Final[int] = 90

# Earliest year exposed for year-specific satellite search (the year
# comparison feature). This is an application/UI support boundary for
# this feature, not a scientific claim that Sentinel-2 has no usable
# imagery before this year.
MIN_SUPPORTED_YEAR: Final[int] = 2019

# --- Standardized seasonal comparison window (Version 1) ---
# When a specific year is requested, the satellite search is limited to
# this same month/day window every year, rather than the full calendar
# year, so a year-over-year comparison observes the same part of the
# seasonal cycle instead of comparing, say, a July scene against a
# December one. This reduces (does not eliminate) confounding from
# ordinary seasonal vegetation change — it is not a claim that this
# window is universally optimal for every location, and it does not
# guarantee maximum vegetation greenness or maximum model accuracy.
# Kept as named constants (not inline dates in sentinel.py) so this
# window can be changed later without touching the search logic itself.
COMPARISON_WINDOW_START_MONTH: Final[int] = 10  # October
COMPARISON_WINDOW_START_DAY: Final[int] = 1
COMPARISON_WINDOW_END_MONTH: Final[int] = 12  # December
COMPARISON_WINDOW_END_DAY: Final[int] = 15

# Approximate meters per degree of latitude (WGS 84, good enough for the
# small bounding boxes this subsystem requests).
METERS_PER_DEGREE_LATITUDE: Final[float] = 111_320.0


@dataclass(frozen=True)
class BoundingBox:
    """A geographic bounding box in decimal degrees (EPSG:4326)."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def as_list(self) -> List[float]:
        """
        Returns:
            The bounding box as `[min_lon, min_lat, max_lon, max_lat]`,
            the order Sentinel Hub (and most geospatial APIs) expect.
        """
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]


def compute_bounding_box(latitude: float, longitude: float, buffer_meters: float) -> BoundingBox:
    """
    Compute a square bounding box of the given side length, centered on
    a latitude/longitude point.

    Uses a standard equirectangular approximation, which is accurate
    enough for the small areas (a few kilometers) this subsystem
    requests. Not suitable for very large boxes or near the poles.

    Args:
        latitude: Center latitude, in decimal degrees.
        longitude: Center longitude, in decimal degrees.
        buffer_meters: The bounding box's side length, in meters.

    Returns:
        A BoundingBox centered on the given point.
    """
    half_buffer = buffer_meters / 2.0

    delta_lat = half_buffer / METERS_PER_DEGREE_LATITUDE

    meters_per_degree_longitude = METERS_PER_DEGREE_LATITUDE * math.cos(math.radians(latitude))
    # Guard against a division by zero directly at the poles.
    meters_per_degree_longitude = meters_per_degree_longitude or 1e-9
    delta_lon = half_buffer / meters_per_degree_longitude

    return BoundingBox(
        min_lon=longitude - delta_lon,
        min_lat=latitude - delta_lat,
        max_lon=longitude + delta_lon,
        max_lat=latitude + delta_lat,
    )


@dataclass(frozen=True)
class SatelliteImageRequest:
    """
    Describes a single satellite image to retrieve.

    Coordinates are assumed to already be validated (the existing
    location service, app/services/location/validator.py, is the single
    place range validation happens — this request model does not repeat
    that check).
    """

    latitude: float
    longitude: float
    buffer_meters: float = DEFAULT_BUFFER_METERS
    width_px: int = DEFAULT_IMAGE_SIZE_PX
    height_px: int = DEFAULT_IMAGE_SIZE_PX
    days_back: int = DEFAULT_DAYS_BACK
    # If set, search is limited to the standardized seasonal comparison
    # window (see COMPARISON_WINDOW_* above) within this calendar year,
    # instead of the default rolling `days_back`-day window. Used by the
    # year-comparison feature; leave unset for the existing behavior.
    year: Optional[int] = None

    def bounding_box(self) -> BoundingBox:
        """
        Returns:
            The BoundingBox this request covers, derived from its
            center point and buffer.
        """
        return compute_bounding_box(self.latitude, self.longitude, self.buffer_meters)


@dataclass(frozen=True)
class RawSatelliteImage:
    """
    The raw result of a provider fetching imagery, before it has been
    saved to disk. Providers return this; the downloader persists it.
    """

    content: bytes
    content_type: str
    provider_name: str
    acquisition_date: Optional[datetime] = field(default=None)


@dataclass(frozen=True)
class SatelliteImageResult:
    """
    The final, saved result of a satellite image download — what the
    rest of the application (eventually the prediction pipeline) works
    with instead of raw bytes.
    """

    image_path: Path
    provider: str
    latitude: float
    longitude: float
    bounding_box: BoundingBox
    acquisition_date: Optional[datetime]
    file_size_bytes: int
