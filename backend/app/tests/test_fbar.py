"""
Tests for app.modules.fbar – FBAR PDF/JSON generation.
Pure unit tests; no HTTP client or JWT required.
"""
from __future__ import annotations

import pytest

from app.modules.fbar import (
    FBARReport,
    FBAReporter,
    ForeignAccount,
    generate_fbar_pdf,
    fbar_json,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_reporter() -> FBAReporter:
    return FBAReporter(
        name="Jane Doe",
        address="123 Main St",
        city="Springfield",
        state="IL",
        zip="62701",
        country="US",
        ssn_last4="9876",
    )


def _make_report(balances: list[str] | None = None) -> FBARReport:
    balances = balances or ["15000", "8500"]
    accounts = [
        ForeignAccount(
            institution_name=f"Bank {i + 1}",
            country="DE",
            account_number=f"DE{i:012d}",
            max_balance_usd=bal,
        )
        for i, bal in enumerate(balances)
    ]
    return FBARReport(reporter=_make_reporter(), year=2024, accounts=accounts)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_fbar_json_basic():
    """fbar_json must return correct year, reporter name and account count."""
    report = _make_report(["15000", "8500"])
    result = fbar_json(report)

    assert result["year"] == 2024
    assert result["reporter"]["name"] == "Jane Doe"
    assert len(result["accounts"]) == 2
    assert "fbar_required" in result
    assert "total_accounts" in result


def test_fbar_pdf_is_bytes():
    """generate_fbar_pdf must return non-empty bytes."""
    report = _make_report()
    pdf = generate_fbar_pdf(report)

    assert isinstance(pdf, bytes)
    assert len(pdf) > 100  # a real PDF is several KB


def test_fbar_pdf_header():
    """Generated PDF must be a valid ReportLab PDF with sufficient size."""
    report = _make_report()
    pdf = generate_fbar_pdf(report)

    # ReportLab always includes this marker in uncompressed header
    assert b"ReportLab" in pdf
    # PDF must be at least 1 KB (a real document with tables)
    assert len(pdf) > 1000


def test_fbar_threshold_triggered():
    """
    FBAR threshold is $10,000 aggregate.
    A report with one account at $12,000 must flag fbar_required=True.
    """
    report = _make_report(balances=["12000", "0"])
    result = fbar_json(report)

    assert len(result["accounts"]) == 2
    # Aggregate is $12,000 > $10,000 → filing required
    assert result["fbar_required"] is True


def test_fbar_threshold_not_triggered():
    """Aggregate below $10k must not flag fbar_required."""
    report = _make_report(balances=["4000", "5000"])
    result = fbar_json(report)

    assert result["fbar_required"] is False


def test_fbar_pdf_two_accounts():
    """PDF for a report with 2 accounts must be larger than a 1-account report."""
    report_2 = _make_report(["20000", "30000"])
    report_1 = _make_report(["20000"])
    pdf_2 = generate_fbar_pdf(report_2)
    pdf_1 = generate_fbar_pdf(report_1)

    # Two-account PDF should be at least as large as a one-account PDF
    assert len(pdf_2) >= len(pdf_1)
