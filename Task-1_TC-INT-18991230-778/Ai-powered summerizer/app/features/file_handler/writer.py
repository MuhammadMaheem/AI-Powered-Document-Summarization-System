"""
Summary export utilities.

Supports exporting to plain text (.txt) and PDF (.pdf).
The PDF is generated with reportlab using a clean, readable layout.
"""

import io
import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors


def export_txt(summary: str) -> bytes:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"TEYZIX Document Summary\nGenerated: {timestamp}\n{'='*60}\n\n{summary}\n"
    return content.encode("utf-8")


def export_pdf(summary: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#7c6aff"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
        alignment=TA_LEFT,
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story = [
        Paragraph("TEYZIX Document Summary", title_style),
        Paragraph(f"Generated: {timestamp}", meta_style),
        Spacer(1, 0.5 * cm),
        Paragraph(summary.replace("\n", "<br/>"), body_style),
    ]

    doc.build(story)
    return buffer.getvalue()


def export_summary(summary: str, fmt: str = "txt") -> tuple[bytes, str]:
    """Return (file_bytes, download_filename)."""
    slug = uuid.uuid4().hex[:10]
    filename = f"summary_{slug}.{fmt}"

    if fmt == "pdf":
        return export_pdf(summary), filename
    return export_txt(summary), filename
