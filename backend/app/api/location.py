"""
Location endpoint.

Accepts a latitude/longitude pair selected on the map, validates it via
the location service, and echoes it back in a structured response. This
module contains no validation logic itself — it only orchestrates the
request/response cycle around app/services/location/validator.py.

Does not trigger AI inference or imagery retrieval.
"""

from typing import Final

from fastapi import APIRouter, HTTPException, status

from app.schemas.location import LocationData, LocationRequest, LocationResponse
from app.services.location.validator import validate_coordinates

router: Final[APIRouter] = APIRouter(tags=["Location"])


@router.post(
    "/location/select",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a selected map location",
)
async def submit_location(payload: LocationRequest) -> LocationResponse:
    """
    Validate and acknowledge a selected map location.

    Args:
        payload: The submitted latitude/longitude pair.

    Returns:
        A LocationResponse confirming the coordinates were received.

    Raises:
        HTTPException: 400 if latitude or longitude falls outside its
            valid range.
    """
    result = validate_coordinates(payload.latitude, payload.longitude)

    if not result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return LocationResponse(
        status="success",
        location=LocationData(latitude=payload.latitude, longitude=payload.longitude),
        message="Coordinates received successfully.",
    )
