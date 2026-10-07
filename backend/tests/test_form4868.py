"""
Tests for Form 4868 — Application for Automatic Extension of Time to File.

Tests cover:
- Extension deadline calculation
- Penalty calculations (failure to file, failure to pay)
- Interest calculation
- Abroad extension eligibility
- Extension status tracking
"""
import uuid
import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_access_token
from app.modules.form4868 import (
    ExtensionInput,
    calculate_extension,
    get_extension_status,
    check_abroad_extension_eligible,
    get_form4868_overview,
    ORIGINAL_DEADLINES,
    EXTENDED_DEADLINES,
    STANDARD_EXTENSION_MONTHS,
    FAILURE_TO_FILE_RATE,
    FAILURE_TO_PAY_RATE,
)

client = TestClient(app)

BASE = "/api/v1/form4868"


@pytest.fixture()
def auth_token() -> str:
    return create_access_token({
        "sub": f"form4868-test-{uuid.uuid4().hex[:8]}@example.com",
        "tenant_id": str(uuid.uuid4()),
    })


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------

class TestExtensionModule:
    """Tests for extension calculation."""

    def test_basic_extension_calculation(self):
        """Basic extension calculation should return extended deadline."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("15000"),
            amount_paid=Decimal("5000"),
        )
        result = calculate_extension(inp)

        assert result.extended_deadline == date(2025, 10, 15)
        assert result.days_extended == 183
        assert result.extension_granted is True

    def test_extension_deadline_calculation(self):
        """Extended deadline should be 6 months from original."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("0"),
            amount_paid=Decimal("0"),
        )
        result = calculate_extension(inp)

        assert result.extended_deadline == date(2025, 10, 15)

    def test_balance_due_calculation(self):
        """Balance due should be tax liability minus amount paid."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("15000"),
            amount_paid=Decimal("5000"),
        )
        result = calculate_extension(inp)

        assert result.balance_due == Decimal("10000")

    def test_payment_deadline_is_original(self):
        """Payment deadline should always be the original deadline."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("15000"),
            amount_paid=Decimal("0"),
        )
        result = calculate_extension(inp)

        assert result.payment_deadline == date(2025, 4, 15)

    def test_failure_to_file_penalty_calculation(self):
        """Failure to file penalty should be 5% per month, max 25%."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("10000"),
            amount_paid=Decimal("0"),
        )
        result = calculate_extension(inp)

        # 6 months * 5% = 30%, but max is 25%
        expected_penalty = Decimal("10000") * Decimal("0.25")
        assert result.penalty_if_not_filed == expected_penalty

    def test_interest_calculation(self):
        """Interest should be calculated on unpaid balance."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("10000"),
            amount_paid=Decimal("0"),
        )
        result = calculate_extension(inp)

        assert result.interest_if_not_paid > 0

    def test_no_balance_due_when_fully_paid(self):
        """No balance due when tax is fully paid."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("10000"),
            amount_paid=Decimal("10000"),
        )
        result = calculate_extension(inp)

        assert result.balance_due == Decimal("0")

    def test_extension_granted_automatically(self):
        """Extension should be automatically granted."""
        inp = ExtensionInput(
            filing_status="single",
            tax_year=2025,
            original_deadline=date(2025, 4, 15),
            extension_months=6,
            estimated_tax_liability=Decimal("0"),
            amount_paid=Decimal("0"),
        )
        result = calculate_extension(inp)

        assert result.extension_granted is True

    def test_different_tax_years(self):
        """Extension should work for different tax years."""
        for year in [2023, 2024, 2025]:
            inp = ExtensionInput(
                filing_status="single",
                tax_year=year,
                original_deadline=ORIGINAL_DEADLINES[year],
                extension_months=6,
                estimated_tax_liability=Decimal("10000"),
                amount_paid=Decimal("0"),
            )
            result = calculate_extension(inp)

            assert result.extended_deadline == EXTENDED_DEADLINES[year]


class TestExtensionStatusModule:
    """Tests for extension status tracking."""

    def test_extension_status_filed(self):
        """Extension status should show filed status."""
        result = get_extension_status(
            extension_filed=True,
            tax_year=2025,
            today=date(2025, 5, 1),
        )

        assert result.extension_filed is True
        assert result.filing_status == "Extension filed"
        assert result.days_remaining > 0

    def test_extension_status_not_filed(self):
        """Extension status should show not filed status."""
        result = get_extension_status(
            extension_filed=False,
            tax_year=2025,
            today=date(2025, 3, 1),
        )

        assert result.extension_filed is False
        assert result.filing_status == "No extension filed"
        assert result.days_remaining > 0

    def test_extension_status_expired(self):
        """Extension status should show expired when past deadline."""
        result = get_extension_status(
            extension_filed=True,
            tax_year=2025,
            today=date(2025, 11, 1),
        )

        assert result.filing_status == "Extension expired"
        assert result.days_remaining < 0

    def test_extension_status_payment_overdue(self):
        """Payment status should show overdue when past original deadline."""
        result = get_extension_status(
            extension_filed=False,
            tax_year=2025,
            today=date(2025, 5, 1),
        )

        assert result.payment_status == "Payment overdue"


class TestAbroadExtensionModule:
    """Tests for abroad extension eligibility."""

    def test_abroad_extension_eligible(self):
        """Taxpayer living abroad should be eligible for extension."""
        result = check_abroad_extension_eligible(
            country="Germany",
            tax_year=2025,
            living_abroad=True,
        )

        assert result["eligible"] is True
        assert "automatic_extension" in result
        assert result["automatic_extension"]["deadline"] == "2025-06-15"

    def test_abroad_extension_not_eligible(self):
        """Taxpayer not living abroad should not be eligible."""
        result = check_abroad_extension_eligible(
            country="Germany",
            tax_year=2025,
            living_abroad=False,
        )

        assert result["eligible"] is False

    def test_abroad_extension_extended_deadline(self):
        """Abroad extension should show October 15 extended deadline."""
        result = check_abroad_extension_eligible(
            country="Germany",
            tax_year=2025,
            living_abroad=True,
        )

        assert result["extended_deadline"] == "2025-10-15"

    def test_abroad_extension_requirements(self):
        """Abroad extension should list requirements."""
        result = check_abroad_extension_eligible(
            country="Germany",
            tax_year=2025,
            living_abroad=True,
        )

        assert "requirements" in result
        assert len(result["requirements"]) > 0


class TestForm4868Overview:
    """Tests for Form 4868 overview."""

    def test_overview_contains_required_fields(self):
        """Overview should contain all required fields."""
        overview = get_form4868_overview()

        assert overview["form"] == "Form 4868"
        assert "title" in overview
        assert "purpose" in overview
        assert "key_facts" in overview
        assert "deadlines" in overview
        assert "penalties" in overview
        assert "special_rules" in overview
        assert "how_to_file" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_deadlines(self):
        """Deadlines should be documented."""
        overview = get_form4868_overview()

        assert "original" in overview["deadlines"]
        assert "extended" in overview["deadlines"]
        assert "abroad_automatic" in overview["deadlines"]

    def test_overview_penalties(self):
        """Penalties should be documented."""
        overview = get_form4868_overview()

        assert "failure_to_file" in overview["penalties"]
        assert "failure_to_pay" in overview["penalties"]
        assert "interest" in overview["penalties"]


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestExtensionCalculateEndpoint:
    """Tests for /api/v1/form4868/calculate endpoint."""

    def test_calculate_endpoint_basic(self, auth_token):
        """Test basic extension calculation endpoint."""
        resp = client.post(
            "/api/v1/form4868/calculate",
            json={
                "filing_status": "single",
                "tax_year": 2025,
                "original_deadline": "2025-04-15",
                "extension_months": 6,
                "estimated_tax_liability": "15000.00",
                "amount_paid": "5000.00",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["extended_deadline"] == "2025-10-15"
        assert data["extension_granted"] is True
        assert data["balance_due"] == "10000.00"
        assert data["payment_deadline"] == "2025-04-15"

    def test_calculate_endpoint_no_balance(self, auth_token):
        """Test endpoint with no balance due."""
        resp = client.post(
            "/api/v1/form4868/calculate",
            json={
                "filing_status": "single",
                "tax_year": 2025,
                "original_deadline": "2025-04-15",
                "extension_months": 6,
                "estimated_tax_liability": "10000.00",
                "amount_paid": "10000.00",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["balance_due"] == "0"

    def test_calculate_endpoint_invalid_date(self, auth_token):
        """Test endpoint with invalid date format."""
        resp = client.post(
            "/api/v1/form4868/calculate",
            json={
                "filing_status": "single",
                "tax_year": 2025,
                "original_deadline": "invalid-date",
                "extension_months": 6,
                "estimated_tax_liability": "10000.00",
                "amount_paid": "0",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_calculate_endpoint_requires_auth(self):
        """Test endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form4868/calculate",
            json={
                "filing_status": "single",
                "tax_year": 2025,
                "original_deadline": "2025-04-15",
                "extension_months": 6,
                "estimated_tax_liability": "10000.00",
                "amount_paid": "0",
            },
        )

        assert resp.status_code == 401


class TestExtensionStatusEndpoint:
    """Tests for /api/v1/form4868/status endpoint."""

    def test_status_endpoint_filed(self, auth_token):
        """Test status endpoint with extension filed."""
        resp = client.post(
            "/api/v1/form4868/status",
            json={
                "extension_filed": True,
                "tax_year": 2025,
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["extension_filed"] is True
        assert "days_remaining" in data
        assert "filing_status" in data

    def test_status_endpoint_not_filed(self, auth_token):
        """Test status endpoint with no extension filed."""
        resp = client.post(
            "/api/v1/form4868/status",
            json={
                "extension_filed": False,
                "tax_year": 2025,
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["extension_filed"] is False

    def test_status_endpoint_requires_auth(self):
        """Test endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form4868/status",
            json={
                "extension_filed": True,
                "tax_year": 2025,
            },
        )

        assert resp.status_code == 401


class TestAbroadCheckEndpoint:
    """Tests for /api/v1/form4868/abroad-check endpoint."""

    def test_abroad_check_endpoint_eligible(self, auth_token):
        """Test abroad check endpoint with eligible taxpayer."""
        resp = client.post(
            "/api/v1/form4868/abroad-check",
            json={
                "country": "Germany",
                "tax_year": 2025,
                "living_abroad": True,
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert "automatic_extension" in data

    def test_abroad_check_endpoint_not_eligible(self, auth_token):
        """Test abroad check endpoint with ineligible taxpayer."""
        resp = client.post(
            "/api/v1/form4868/abroad-check",
            json={
                "country": "Germany",
                "tax_year": 2025,
                "living_abroad": False,
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False

    def test_abroad_check_endpoint_requires_auth(self):
        """Test endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form4868/abroad-check",
            json={
                "country": "Germany",
                "tax_year": 2025,
                "living_abroad": True,
            },
        )

        assert resp.status_code == 401


class TestOverviewEndpoint:
    """Tests for /api/v1/form4868/overview endpoint."""

    def test_overview_endpoint_no_auth_required(self):
        """Test overview endpoint (no authentication required)."""
        resp = client.get("/api/v1/form4868/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["form"] == "Form 4868"
        assert "deadlines" in data
        assert "penalties" in data
        assert "special_rules" in data
