"""
FastAPI router for downloading a year-comparison PDF report.

This endpoint performs NO new satellite download and NO new ML
inference. It only resolves two already-saved satellite images (by
their opaque `image_reference`, previously returned from
/satellite-predict/) and renders a PDF from data the client already
has (predictions, acquisition metadata). See
`app.services.report.pdf_generator` for the scientific-honesty
constraints this enforces (no confidence anywhere, no landscape-change
percentage).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.schemas.report import SatelliteReportRequest
from app.services.satellite.downloader import resolve_satellite_image_path
from app.services.report.pdf_generator import generate_comparison_report_pdf

router = APIRouter()


@router.post("/")
def download_comparison_report(report_request: SatelliteReportRequest):
    """
    Generate and stream back a PDF comparing two years' satellite-based
    land-cover classifications.

    Resolves both `image_reference` values to real files on disk
    (rejecting anything that isn't an exact, existing, previously-saved
    image reference), then builds the PDF and returns it as a file
    download.
    """
    try:
        image_path_a = resolve_satellite_image_path(report_request.year_a.image_reference)
        image_path_b = resolve_satellite_image_path(report_request.year_b.image_reference)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_IMAGE_REFERENCE",
                "message": str(e),
            },
        ) from e

    try:
        pdf_bytes = generate_comparison_report_pdf(
            report_request, image_path_a, image_path_b,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "REPORT_GENERATION_ERROR",
                "message": "An unexpected error occurred while generating the PDF report.",
            },
        ) from e

    filename = (
        f"vanrakshak-comparison-"
        f"{report_request.year_a.requested_year}-"
        f"{report_request.year_b.requested_year}.pdf"
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
