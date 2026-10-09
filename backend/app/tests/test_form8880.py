"""
Tests for Form 8880 — Credit for Retirement Savings (Saver's Credit).

Covers:
- Credit rate determination by filing status and AGI
- 50%, 20%, 10%, 0% rate tiers
- Maximum contribution cap ($2,000)
- Boundary conditions at AGI thresholds
- Overview endpoint
- API endpoints (calculate, overview)
- Edge cases: zero contributions, very high AGI
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import get_current_tenant
from app.modules.form8880 import (
    Form8880Input,
    Form8880Result,
    calculate_form8880,
    get_form8880_overview,
    MAX_CONTRIBUTION_FOR_CREDIT,
    SAVERS_CREDIT_RATES,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    """Override get_current_tenant for all tests."""
    async def mock_get_current_tenant():
        return {
            "tenant_id": "test-tenant-123",
            "email": "test@example.com",
            "tenant_name": "Test Tenant",
        }
    app.dependency_overrides[get_current_tenant] = mock_get_current_tenant
    yield
    app.dependency_overrides.clear()


# ========================================================================
# Module-level tests (calculate_form8880)
# ========================================================================

class TestCalculateForm8880:
    """Tests for the calculate_form8880 function."""

    def test_single_50_percent_rate(self):
        """Single filer with AGI below $21,750 → 50% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.50")
        assert result.credit_amount == Decimal("1000.00")

    def test_single_20_percent_rate(self):
        """Single filer with AGI between $21,750 and $23,625 → 20% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("22000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.20")
        assert result.credit_amount == Decimal("400.00")

    def test_single_10_percent_rate(self):
        """Single filer with AGI between $23,625 and $36,500 → 10% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("30000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.10")
        assert result.credit_amount == Decimal("200.00")

    def test_single_zero_rate(self):
        """Single filer with AGI above $36,500 → 0% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("40000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0")
        assert result.credit_amount == Decimal("0.00")

    def test_married_joint_50_percent_rate(self):
        """Married filing jointly with AGI below $43,500 → 50% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("40000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.50")
        assert result.credit_amount == Decimal("1000.00")

    def test_married_joint_20_percent_rate(self):
        """Married filing jointly with AGI between $43,500 and $47,250 → 20%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("45000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.20")
        assert result.credit_amount == Decimal("400.00")

    def test_married_joint_10_percent_rate(self):
        """Married filing jointly with AGI between $47,250 and $73,000 → 10%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("60000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.10")
        assert result.credit_amount == Decimal("200.00")

    def test_married_joint_zero_rate(self):
        """Married filing jointly with AGI above $73,000 → 0%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("80000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0")
        assert result.credit_amount == Decimal("0.00")

    def test_head_of_household_50_percent_rate(self):
        """Head of household with AGI below $32,625 → 50% credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("30000"),
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.50")
        assert result.credit_amount == Decimal("1000.00")

    def test_head_of_household_20_percent_rate(self):
        """Head of household with AGI between $32,625 and $35,438 → 20%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("34000"),
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.20")
        assert result.credit_amount == Decimal("400.00")

    def test_head_of_household_10_percent_rate(self):
        """Head of household with AGI between $35,438 and $54,750 → 10%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("50000"),
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.10")
        assert result.credit_amount == Decimal("200.00")

    def test_head_of_household_zero_rate(self):
        """Head of household with AGI above $54,750 → 0%."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("60000"),
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0")
        assert result.credit_amount == Decimal("0.00")

    def test_max_contribution_cap(self):
        """Contributions above $2,000 are capped at $2,000 for credit calculation."""
        inp = Form8880Input(
            retirement_contributions=Decimal("5000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        # Credit should be based on $2,000 (max), not $5,000
        assert result.credit_amount == Decimal("1000.00")

    def test_zero_contributions(self):
        """Zero contributions → zero credit."""
        inp = Form8880Input(
            retirement_contributions=Decimal("0"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_amount == Decimal("0.00")

    def test_partial_contributions(self):
        """Contributions below $2,000 → credit based on actual amount."""
        inp = Form8880Input(
            retirement_contributions=Decimal("1000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_amount == Decimal("500.00")

    def test_boundary_single_21750(self):
        """Boundary: single filer at exactly $21,750 → 20% rate (not 50%)."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("21750"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.20")

    def test_boundary_single_23625(self):
        """Boundary: single filer at exactly $23,625 → 10% rate (not 20%)."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("23625"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.10")

    def test_boundary_single_36500(self):
        """Boundary: single filer at exactly $36,500 → 0% rate (not 10%)."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("36500"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0")

    def test_unknown_filing_status_defaults_to_single(self):
        """Unknown filing status defaults to single rates."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("20000"),
            filing_status="unknown_status",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        # Should use single rates
        assert result.credit_rate == Decimal("0.50")

    def test_explanation_contains_credit_amount(self):
        """Explanation should contain the credit amount."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert "1,000" in result.explanation or "1000" in result.explanation

    def test_explanation_contains_rate(self):
        """Explanation should contain the credit rate."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert "50%" in result.explanation


# ========================================================================
# Overview tests
# ========================================================================

class TestGetForm8880Overview:
    """Tests for the get_form8880_overview function."""

    def test_overview_structure(self):
        """Overview should include all required fields."""
        result = get_form8880_overview()
        assert result["form"] == "Form 8880"
        assert result["title"]
        assert result["purpose"]
        assert len(result["who_must_file"]) > 0
        assert len(result["key_rules"]) > 0
        assert len(result["statutory_references"]) > 0
        assert len(result["related_forms"]) > 0
        assert result["irs_reference"]

    def test_overview_key_rules(self):
        """Overview key rules should mention credit rates and limits."""
        result = get_form8880_overview()
        rules_text = " ".join(result["key_rules"])
        assert "50%" in rules_text or "50" in rules_text
        assert "20%" in rules_text or "20" in rules_text
        assert "10%" in rules_text or "10" in rules_text

    def test_overview_statutory_references(self):
        """Overview should reference IRC §25B."""
        result = get_form8880_overview()
        assert "IRC §25B" in result["statutory_references"]

    def test_overview_related_forms(self):
        """Overview should list related forms."""
        result = get_form8880_overview()
        assert "Form 1040" in result["related_forms"]


# ========================================================================
# API endpoint tests
# ========================================================================

class TestAPIEndpoints:
    """Tests for the Form 8880 API endpoints."""

    def test_api_calculate_endpoint(self):
        """Test /calculate endpoint."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "2000",
                "agi": "20000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credit_rate"] == "0.50"
        assert data["credit_amount"] == "1000.00"
        assert "explanation" in data

    def test_api_calculate_married_joint(self):
        """Test /calculate endpoint with married filing jointly."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "2000",
                "agi": "40000",
                "filing_status": "married_joint",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credit_rate"] == "0.50"
        assert data["credit_amount"] == "1000.00"

    def test_api_calculate_zero_credit(self):
        """Test /calculate endpoint with high AGI (zero credit)."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "2000",
                "agi": "50000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credit_rate"] == "0"
        assert data["credit_amount"] == "0.00"

    def test_api_overview_endpoint(self):
        """Test /overview endpoint."""
        response = client.get("/api/v1/form8880/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8880"
        assert "title" in data
        assert "purpose" in data
        assert "key_rules" in data

    def test_api_calculate_invalid_input(self):
        """Test /calculate endpoint with invalid input returns 422."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "invalid",
                "agi": "20000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 422


# ========================================================================
# Constants tests
# ========================================================================

class TestConstants:
    """Tests for module constants."""

    def test_max_contribution_for_credit(self):
        """MAX_CONTRIBUTION_FOR_CREDIT should be $2,000."""
        assert MAX_CONTRIBUTION_FOR_CREDIT == Decimal("2000")

    def test_savers_credit_rates_structure(self):
        """SAVERS_CREDIT_RATES should have all filing statuses."""
        assert "single" in SAVERS_CREDIT_RATES
        assert "married_joint" in SAVERS_CREDIT_RATES
        assert "head_of_household" in SAVERS_CREDIT_RATES

    def test_savers_credit_rates_tiers(self):
        """Each filing status should have 4 rate tiers."""
        for status in ["single", "married_joint", "head_of_household"]:
            assert len(SAVERS_CREDIT_RATES[status]) == 4

    def test_savers_credit_rates_values(self):
        """Rate tiers should have correct values."""
        single_rates = SAVERS_CREDIT_RATES["single"]
        assert single_rates[0][2] == Decimal("0.50")  # 50%
        assert single_rates[1][2] == Decimal("0.20")  # 20%
        assert single_rates[2][2] == Decimal("0.10")  # 10%
        assert single_rates[3][2] == Decimal("0")     # 0%
