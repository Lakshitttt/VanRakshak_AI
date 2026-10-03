"""
PDF generation for the satellite year-comparison report.

Builds a PDF from data the caller already has in hand: two already
-downloaded satellite images and their already-computed ML
predictions. This module performs NO satellite download and NO model
inference — it is pure presentation over existing results.

Scientific-honesty rule (do not relax this): the report never displays
or derives a "landscape change percentage." Model confidence is not a
measurement of how much the landscape changed, so confidence is never
read, passed in, or shown anywhere in this module. The only comparison
statement made is a plain description of the classification label
transition (e.g. "changed from Forest to AnnualCrop" or "no change in
predicted classification").
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    HRFlowable,
)

from app.schemas.report import SatelliteReportRequest


def generate_comparison_report_pdf(
    report_request: SatelliteReportRequest,
    image_path_a: Path,
    image_path_b: Path,
) -> bytes:
    """
    Build a PDF comparing two years' satellite-derived classifications.

    Args:
        report_request: Validated request data (locations, years,
            predictions, acquisition metadata). Contains no confidence
            values by construction (see `app.schemas.report`).
        image_path_a: Filesystem path to year A's already-downloaded
            satellite image.
        image_path_b: Filesystem path to year B's already-downloaded
            satellite image.

    Returns:
        The generated PDF file's raw bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="VanRakshak AI - Land Cover Comparison Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=20, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=10,
        textColor=colors.grey, spaceAfter=16,
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], spaceBefore=12, spaceAfter=8,
    )
    body_style = styles["Normal"]
    note_style = ParagraphStyle(
        "Note", parent=styles["Normal"], fontSize=9, textColor=colors.grey,
        spaceBefore=4,
    )

    elements = []

    elements.append(Paragraph("VanRakshak AI", title_style))
    elements.append(
        Paragraph(
            "Satellite Land-Cover Classification Comparison Report",
            subtitle_style,
        )
    )
    elements.append(HRFlowable(width="100%", color=colors.lightgrey))
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"Location: {report_request.latitude:.5f}, "
            f"{report_request.longitude:.5f}",
            body_style,
        )
    )
    elements.append(Spacer(1, 12))

    elements.append(_build_year_section(
        "Year A", report_request.year_a, image_path_a, heading_style, body_style, note_style,
    ))
    elements.append(Spacer(1, 10))
    elements.append(_build_year_section(
        "Year B", report_request.year_b, image_path_b, heading_style, body_style, note_style,
    ))

    elements.append(Spacer(1, 16))
    elements.append(_build_comparison_section(
        report_request, heading_style, body_style,
    ))

    doc.build(elements)
    return buffer.getvalue()


def _build_year_section(label, entry, image_path, heading_style, body_style, note_style):
    """Build the flowables for a single year's section of the report."""
    from reportlab.platypus import KeepTogether

    flowables = [Paragraph(f"{label}: Requested {entry.requested_year}", heading_style)]

    rows = [
        ["Requested year", str(entry.requested_year)],
        ["Actual acquisition date", entry.acquisition_date or "Unknown"],
        ["Satellite provider", entry.provider],
        ["Predicted land-cover class", entry.prediction],
    ]
    table = Table(rows, colWidths=[5.5 * cm, 9 * cm])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.whitesmoke),
    ]))
    flowables.append(table)
    flowables.append(Spacer(1, 8))

    acquisition_year = _extract_year(entry.acquisition_date)
    if acquisition_year is not None and acquisition_year != entry.requested_year:
        flowables.append(Paragraph(
            f"Note: {entry.requested_year} imagery for this season was not yet "
            f"available, so the most recent completed season "
            f"({acquisition_year}) is shown instead.",
            note_style,
        ))
        flowables.append(Spacer(1, 6))

    if image_path and Path(image_path).exists():
        try:
            img = RLImage(str(image_path), width=7 * cm, height=7 * cm)
            flowables.append(img)
        except Exception:
            flowables.append(Paragraph("(Image could not be embedded.)", note_style))

    return KeepTogether(flowables)


def _build_comparison_section(report_request, heading_style, body_style):
    """
    Build the comparison statement. Strictly a plain-language
    description of the classification label transition — never a
    computed percentage, and never derived from confidence.
    """
    pred_a = report_request.year_a.prediction
    pred_b = report_request.year_b.prediction

    if pred_a == pred_b:
        statement = (
            f"The predicted land-cover classification did not change between "
            f"{report_request.year_a.requested_year} and "
            f"{report_request.year_b.requested_year}. Both years were "
            f"classified as \"{pred_a}\"."
        )
    else:
        statement = (
            f"The predicted land-cover classification changed from "
            f"\"{pred_a}\" ({report_request.year_a.requested_year}) to "
            f"\"{pred_b}\" ({report_request.year_b.requested_year})."
        )

    disclaimer = (
        "This statement reflects the model's predicted classification label "
        "only. It is not a measurement of the extent, area, or percentage of "
        "landscape change, and model confidence values are not used to "
        "quantify change of any kind."
    )

    return Table(
        [[Paragraph("Comparison Summary", heading_style)],
         [Paragraph(statement, body_style)],
         [Spacer(1, 6)],
         [Paragraph(disclaimer, ParameterNoteStyle(body_style))]],
        colWidths=[16.5 * cm],
    )


def ParameterNoteStyle(base_style):
    """Small helper returning a dimmer variant of a given paragraph style."""
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle(
        "Disclaimer", parent=base_style, fontSize=8, textColor=colors.grey,
    )


def _extract_year(acquisition_date_str):
    """Best-effort extraction of a 4-digit year from an ISO-ish date string."""
    if not acquisition_date_str:
        return None
    try:
        return int(acquisition_date_str[:4])
    except (ValueError, TypeError):
        return None
