from io import BytesIO
from datetime import datetime
import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe_text(value, default="Not available"):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _format_currency(value):
    if value in (None, ""):
        return "Not available"
    try:
        return f"NGN {float(value):,.2f}"
    except (TypeError, ValueError):
        return _safe_text(value)


def _format_date(value):
    if not value:
        return "Not available"
    try:
        return value.strftime("%d %b %Y, %I:%M %p")
    except (AttributeError, ValueError):
        return _safe_text(value)


def _get_score(prediction):
    if not prediction:
        return None

    score = getattr(prediction, "probability_score", None)
    if score is not None:
        try:
            return round(float(score) * 100, 1)
        except (TypeError, ValueError):
            pass

    alt_score = getattr(prediction, "eligibility_percentage", None)
    if alt_score is not None:
        try:
            return round(float(alt_score), 1)
        except (TypeError, ValueError):
            pass

    return None


def _get_decision(prediction):
    if not prediction:
        return "Pending"

    decision = getattr(prediction, "predicted_class", None)
    if not decision:
        return "Pending"

    return str(decision).strip() or "Pending"


def _get_estimated_loan(prediction):
    if not prediction:
        return None

    value = getattr(prediction, "estimated_loan_amount", None)
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_key_factors(key_factors=None, prediction=None):
    factors = key_factors

    if factors is None and prediction is not None:
        raw = getattr(prediction, "key_factors", None)
        if raw:
            try:
                factors = json.loads(raw)
            except (TypeError, ValueError):
                factors = []

    if factors is None:
        factors = []

    if isinstance(factors, dict):
        factors = list(factors.values())

    if isinstance(factors, str):
        factors = [factors]

    cleaned = []
    for item in factors:
        text = str(item).strip()
        if text:
            cleaned.append(text)

    return cleaned


def generate_application_pdf(application, prediction=None, key_factors=None):
    """
    Returns a BytesIO object containing the generated PDF.
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        "BrandStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#C49A1A"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E2028"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#6B6E7A"),
        alignment=TA_LEFT,
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#1A1C22"),
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#3A3D48"),
        alignment=TA_LEFT,
    )

    body_bold_style = ParagraphStyle(
        "BodyBoldStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#1A1C22"),
        alignment=TA_LEFT,
    )

    center_note_style = ParagraphStyle(
        "CenterNoteStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        textColor=colors.HexColor("#6B6E7A"),
        alignment=TA_CENTER,
    )

    story = []

    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    story.append(Paragraph("Loan Eligibility Prediction System", brand_style))
    story.append(Paragraph("Application Assessment Report", title_style))
    story.append(
        Paragraph(
            f"Generated on {escape(generated_at)}",
            subtitle_style,
        )
    )

    story.append(Spacer(1, 6))

    reference_id = _safe_text(getattr(application, "reference_id", None))
    applicant_name = _safe_text(getattr(application, "full_name", None))
    application_date = _format_date(getattr(application, "application_date", None))
    requested_amount = _format_currency(getattr(application, "loan_amount_requested", None))
    current_status = _safe_text(getattr(application, "status", None))

    summary_rows = [
        [Paragraph("<b>Applicant Name</b>", body_style), Paragraph(escape(applicant_name), body_bold_style)],
        [Paragraph("<b>Reference ID</b>", body_style), Paragraph(escape(reference_id), body_bold_style)],
        [Paragraph("<b>Submitted</b>", body_style), Paragraph(escape(application_date), body_bold_style)],
        [Paragraph("<b>Requested Amount</b>", body_style), Paragraph(escape(requested_amount), body_bold_style)],
        [Paragraph("<b>Current Status</b>", body_style), Paragraph(escape(current_status), body_bold_style)],
    ]

    application_table = Table(summary_rows, colWidths=[52 * mm, 108 * mm])
    application_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8F5EE")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1C22")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#EAE4D4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAE4D4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(application_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Assessment Summary", section_style))

    score = _get_score(prediction)
    decision = _get_decision(prediction)
    estimated_loan = _get_estimated_loan(prediction)

    if score is None:
        score_text = "Not available"
    else:
        score_text = f"{score}%"

    if estimated_loan is None:
        estimated_loan_text = "Not available"
    else:
        estimated_loan_text = f"NGN {estimated_loan:,.2f} (based on income and score, not a final offer)"

    assessment_rows = [
        [Paragraph("<b>Eligibility Score</b>", body_style), Paragraph(escape(score_text), body_bold_style)],
        [Paragraph("<b>Decision</b>", body_style), Paragraph(escape(decision), body_bold_style)],
        [Paragraph("<b>Estimated Loan</b>", body_style), Paragraph(escape(estimated_loan_text), body_bold_style)],
    ]

    assessment_table = Table(assessment_rows, colWidths=[52 * mm, 108 * mm])
    assessment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8F5EE")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1C22")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#EAE4D4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAE4D4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(assessment_table)

    factors = _normalize_key_factors(key_factors=key_factors, prediction=prediction)
    if factors:
        story.append(Paragraph("Key Factors", section_style))
        for factor in factors:
            story.append(Paragraph(f"&bull; {escape(factor)}", body_style))
            story.append(Spacer(1, 2))

    story.append(Paragraph("Disclaimer", section_style))
    story.append(
        Paragraph(
            "This document is generated from the information submitted to LEPS and the resulting model output. "
            "It is provided for reference and does not replace formal institutional review.",
            body_style,
        )
    )

    story.append(Spacer(1, 8))
    story.append(Paragraph("Loan Eligibility Prediction System", center_note_style))
    story.append(
        Paragraph(
            "Developed for internal application review and applicant reference.",
            center_note_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer