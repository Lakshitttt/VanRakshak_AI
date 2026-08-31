"""
Pydantic schemas for the location endpoint.

Defines the request and response contracts for POST /api/v1/location.
Range validation (-90..90 / -180..180) is intentionally NOT performed
here — it lives in app/services/location/validator.py so it exists in
exactly one place. These schemas only enforce that latitude/longitude
are present and numeric.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LocationRequest(BaseModel):
    """Request body for POST /api/v1/location and POST /api/v1/satellite-predict/."""

    latitude: float = Field(description="Latitude in decimal degrees.")
    longitude: float = Field(description="Longitude in decimal degrees.")
    year: Optional[int] = Field(
        default=None,
        description=(
            "Optional calendar year for the year-comparison feature. When set, "
            "satellite search is limited to the standardized seasonal comparison "
            "window (October 1 - December 15) within that year. When omitted, "
            "the default rolling 90-day search window is used unchanged."
        ),
    )


class LocationData(BaseModel):
    """The coordinate pair echoed back in a successful response."""

    latitude: float = Field(description="Latitude in decimal degrees.")
    longitude: float = Field(description="Longitude in decimal degrees.")


class LocationResponse(BaseModel):
    """Response body for a successfully validated location submission."""

    status: str = Field(description='Always "success" for a 200 response.')
    location: LocationData = Field(description="The validated coordinate pair.")
    message: str = Field(description="Human-readable confirmation message.")
