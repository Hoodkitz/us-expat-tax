"""
FBAR (FinCEN 114) – Report of Foreign Bank and Financial Accounts.

Provides Pydantic models, a JSON export helper, and a PDF generator
using reportlab.
"""
from __future__ import annotations

import io
from typing import List

from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FBAReporter(BaseModel):
    name: str
    address: str
    city: str
    state: str
    zip: str
    country: str
    ssn_last4: str


class ForeignAccount(BaseModel):
    institution_name: str
    country: str
    account_number: str
    max_balance_usd: str


class FBARReport(BaseModel):
    reporter: FBAReporter
    year: int
    accounts: List[ForeignAccount]


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


def fbar_json(report: FBARReport) -> dict:
    """Return the report as a plain dict (serialisable to JSON)."""
    return {
        "year": report.year,
        "reporter": {
            "name": report.reporter.name,
            "address": report.reporter.address,
            "city": report.reporter.city,
            "state": report.reporter.state,
            "zip": report.reporter.zip,
            "country": report.reporter.country,
            "ssn_last4": report.reporter.ssn_last4,
        },
        "accounts": [
            {
                "institution_name": acc.institution_name,
                "country": acc.country,
                "account_number": acc.account_number,
                "max_balance_usd": acc.max_balance_usd,
            }
            for acc in report.accounts
        ],
        "fbar_required": any(
            _safe_float(acc.max_balance_usd) > 10_000
            for acc in report.accounts
        ),
        "total_accounts": len(report.accounts),
    }


# ---------------------------------------------------------------------------
# PDF generator
# ---------------------------------------------------------------------------


def _safe_float(value: str) -> float:
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def generate_fbar_pdf(report: FBARReport) -> bytes:
    """
    Generate a FinCEN 114 summary PDF and return it as bytes.
    Uses reportlab platypus for structured layout.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FBARTitle",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=4,
        textColor=colors.HexColor("#003366"),
    )
    sub_style = ParagraphStyle(
        "FBARSub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#444444"),
        spaceAfter=2,
    )
    footer_style = ParagraphStyle(
        "FBARFooter",
        parent=styles["Italic"],
        fontSize=8,
        textColor=colors.HexColor("#666666"),
    )

    story = []

    # --- Header ---
    story.append(
        Paragraph(
            "FinCEN 114 \u2013 Report of Foreign Bank and Financial Accounts (FBAR)",
            title_style,
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    # --- Tax year ---
    story.append(Paragraph(f"<b>Tax Year:</b> {report.year}", sub_style))
    story.append(Spacer(1, 0.05 * inch))

    # --- Filer info ---
    r = report.reporter
    story.append(Paragraph("<b>Filer Information</b>", styles["Heading2"]))
    filer_data = [
        ["Name", r.name],
        ["Address", r.address],
        ["City / State / ZIP", f"{r.city}, {r.state} {r.zip}"],
        ["Country", r.country],
        ["SSN (last 4)", f"XXX-XX-{r.ssn_last4}"],
    ]
    filer_table = Table(filer_data, colWidths=[2 * inch, 4.5 * inch])
    filer_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(filer_table)
    story.append(Spacer(1, 0.15 * inch))

    # --- Accounts table ---
    story.append(Paragraph("<b>Foreign Financial Accounts</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.05 * inch))

    header_row = ["Institution", "Country", "Account #", "Max Balance (USD)"]
    account_rows = [header_row] + [
        [
            acc.institution_name,
            acc.country,
            acc.account_number,
            f"${_safe_float(acc.max_balance_usd):,.2f}",
        ]
        for acc in report.accounts
    ]

    acc_table = Table(
        account_rows,
        colWidths=[2.0 * inch, 1.3 * inch, 1.8 * inch, 1.4 * inch],
    )
    acc_table.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                # Body rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f9")]),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(acc_table)
    story.append(Spacer(1, 0.2 * inch))

    # --- FBAR threshold notice ---
    aggregate = sum(_safe_float(acc.max_balance_usd) for acc in report.accounts)
    threshold_text = (
        f"<b>Aggregate Maximum Value of All Accounts:</b> ${aggregate:,.2f}  "
        + (
            "&#x26A0; FBAR filing required (aggregate exceeds $10,000)."
            if aggregate > 10_000
            else "Below $10,000 aggregate threshold."
        )
    )
    story.append(Paragraph(threshold_text, sub_style))
    story.append(Spacer(1, 0.3 * inch))

    # --- Footer ---
    story.append(
        Paragraph(
            "This is an informational summary. File electronically at "
            "bsaefiling.fincen.treas.gov",
            footer_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
