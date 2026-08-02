"""
Coordinate validation for the location service.

Contains the sole validation logic for latitude/longitude values used
by POST /api/v1/location. Kept as plain Python with no FastAPI or HTTP
knowledge, so the API layer stays thin and this logic is independently
testable and reusable.
"""

from dataclasses import dataclass
from typing import Final, Optional

# --- Valid coordinate ranges (WGS 84) ---
MIN_LATITUDE: Final[float] = -90.0
MAX_LATITUDE: Final[float] = 90.0
MIN_LONGITUDE: Final[float] = -180.0
MAX_LONGITUDE: Final[float] = 180.0


@dataclass(frozen=True)
class CoordinateValidationResult:
    """
    Outcome of validating a latitude/longitude pair.

    Attributes:
        is_valid: True if both coordinates fall within valid ranges.
        error: A human-readable explanation of the first validation
            failure encountered, or None if `is_valid` is True.
    """

    is_valid: bool
    error: Optional[str] = None


def validate_coordinates(latitude: float, longitude: float) -> CoordinateValidationResult:
    """
    Validate that a latitude/longitude pair falls within valid ranges.

    Latitude must be between -90 and 90 degrees; longitude must be
    between -180 and 180 degrees. Latitude is checked first, so a pair
    invalid in both fields reports the latitude error.

    Args:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.

    Returns:
        A CoordinateValidationResult describing whether the pair is
        valid and, if not, why.
    """
    if not (MIN_LATITUDE <= latitude <= MAX_LATITUDE):
        return CoordinateValidationResult(
            is_valid=False,
            error=f"Latitude must be between {MIN_LATITUDE} and {MAX_LATITUDE} degrees.",
        )

    if not (MIN_LONGITUDE <= longitude <= MAX_LONGITUDE):
        return CoordinateValidationResult(
            is_valid=False,
            error=f"Longitude must be between {MIN_LONGITUDE} and {MAX_LONGITUDE} degrees.",
        )

    return CoordinateValidationResult(is_valid=True)
