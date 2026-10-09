
"""Tests for FBAR (FinCEN Form 114) module."""
import pytest
from app.modules.fbar import FBAReporter, ForeignAccount, FBARReport, fbar_json, generate_fbar_pdf


class TestFBARModels:
    """Test FBAR data models."""

    def test_fbar_reporter_creation(self):
        reporter = FBAReporter(
            name="John Doe",
            address="123 Main St",
            city="Berlin",
            state="BE",
            zip="10115",
            country="DE",
            ssn_last4="6789",
        )
        assert reporter.name == "John Doe"
        assert reporter.country == "DE"
        assert reporter.ssn_last4 == "6789"

    def test_foreign_account_creation(self):
        account = ForeignAccount(
            institution_name="Deutsche Bank",
            country="DE",
            account_number="DE89370400440532013000",
            max_balance_usd="50000",
        )
        assert account.institution_name == "Deutsche Bank"
        assert account.max_balance_usd == "50000"

    def test_fbar_report_creation(self):
        reporter = FBAReporter(
            name="Jane Doe", address="456 Oak Ave", city="Munich",
            state="BY", zip="80331", country="DE", ssn_last4="4321",
        )
        accounts = [
            ForeignAccount(institution_name="Sparkasse", country="DE", account_number="DE123", max_balance_usd="25000"),
            ForeignAccount(institution_name="ING", country="DE", account_number="DE456", max_balance_usd="15000"),
        ]
        report = FBARReport(reporter=reporter, year=2025, accounts=accounts)
        assert report.reporter.name == "Jane Doe"
        assert len(report.accounts) == 2
        assert report.year == 2025


class TestFBARFunctions:
    """Test FBAR utility functions."""

    def test_fbar_json_output(self):
        reporter = FBAReporter(
            name="Test User", address="1 Test St", city="Hamburg",
            state="HH", zip="20095", country="DE", ssn_last4="3333",
        )
        accounts = [ForeignAccount(institution_name="Test Bank", country="DE", account_number="DE999", max_balance_usd="10000")]
        report = FBARReport(reporter=reporter, year=2025, accounts=accounts)
        result = fbar_json(report)
        assert isinstance(result, dict)
        assert "reporter" in result
        assert "accounts" in result
        assert result["year"] == 2025

    def test_generate_fbar_pdf(self):
        reporter = FBAReporter(
            name="PDF Test", address="789 Pdf Rd", city="Frankfurt",
            state="HE", zip="60311", country="DE", ssn_last4="6666",
        )
        accounts = [ForeignAccount(institution_name="Pdf Bank", country="DE", account_number="DE777", max_balance_usd="5000")]
        report = FBARReport(reporter=reporter, year=2025, accounts=accounts)
        pdf_bytes = generate_fbar_pdf(report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
