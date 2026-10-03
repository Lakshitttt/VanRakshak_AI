"""
Pydantic schemas for the satellite comparison PDF report endpoint.

These schemas intentionally carry NO confidence field anywhere. The
report is built strictly from classification labels, acquisition
metadata, and already-downloaded images; confidence percentages are a
model-certainty signal, not a landscape-change measurement, and must
never appear in or be computable from this report's inputs. Even if a
client sends extra fields (such as confidence) in the request body,
Pydantic silently discards anything not declared here.
"""

from typing import Optional

from pydantic import BaseModel, Field


class YearComparisonEntry(BaseModel):
    """
    One side (year A or year B) of a comparison report request.

    Attributes:
        requested_year: The year the user selected in the UI.
        acquisition_date: The real acquisition date of the image that
            was actually used (may differ from requested_year if the
            seasonal current-year fallback applied).
        provider: The satellite provider name (e.g. "sentinel-hub").
        prediction: The predicted land-cover class label for this
            year's image.
        image_reference: Opaque reference to the already-downloaded
            image backing this prediction, resolved via
            `resolve_satellite_image_path`. No new satellite download
            or ML inference happens as part of report generation.
    """

    requested_year: int
    acquisition_date: Optional[str] = None
    provider: str
    prediction: str
    image_reference: str = Field(
        description="Opaque filename reference to an already-saved satellite image."
    )


class SatelliteReportRequest(BaseModel):
    """
    Request body for POST /api/v1/satellite-report/.

    Attributes:
        latitude: Latitude of the compared location.
        longitude: Longitude of the compared location.
        year_a: The first (earlier, by convention) year's comparison data.
        year_b: The second (later, by convention) year's comparison data.
    """

    latitude: float
    longitude: float
    year_a: YearComparisonEntry
    year_b: YearComparisonEntry
