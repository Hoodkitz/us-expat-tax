"""
Tests for Form 1040 — U.S. Individual Income Tax Return.
"""
import pytest
from decimal import Decimal
from app.modules.form1040 import (
    Form1040Input,
    Form1040Result,
    calculate_form1040,
    get_form1040_overview,
)


class TestCalculate:
    """Unit tests for Form 1040 calculation."""

    def test_basic_single_filer(self):
        """Test basic single filer with standard deduction."""
        inp = Form1040Input(
            wages=Decimal("50000"),
            interest_income=Decimal("1000"),
            standard_deduction=True,
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("37150")
        assert result.tax_liability > Decimal("0")
        assert result.effective_tax_rate > Decimal("0")

    def test_married_joint(self):
        """Test married filing jointly."""
        inp = Form1040Input(
            wages=Decimal("100000"),
            interest_income=Decimal("2000"),
            standard_deduction=True,
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("73300")
        assert result.tax_liability > Decimal("0")

    def test_head_of_household(self):
        """Test head of household filing status."""
        inp = Form1040Input(
            wages=Decimal("60000"),
            interest_income=Decimal("500"),
            standard_deduction=True,
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("40700")
        assert result.tax_liability > Decimal("0")

    def test_no_income(self):
        """Test with zero income."""
        inp = Form1040Input(
            wages=Decimal("0"),
            interest_income=Decimal("0"),
            standard_deduction=True,
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("0")
        assert result.tax_liability == Decimal("0")

    def test_high_income(self):
        """Test high income taxpayer."""
        inp = Form1040Input(
            wages=Decimal("500000"),
            interest_income=Decimal("10000"),
            standard_deduction=True,
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("496150")
        assert result.tax_liability > Decimal("100000")

    def test_itemized_deductions(self):
        """Test with itemized deductions."""
        inp = Form1040Input(
            wages=Decimal("100000"),
            interest_income=Decimal("5000"),
            standard_deduction=False,
            itemized_deductions=Decimal("30000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("75000")

        # Itemized should be higher than standard for this case
        inp_standard = Form1040Input(
            wages=Decimal("100000"),
            interest_income=Decimal("5000"),
            standard_deduction=True,
            filing_status="single",
            tax_year=2025,
        )
        result_standard = calculate_form1040(inp_standard)
        assert result.taxable_income < result_standard.taxable_income

    def test_capital_gains(self):
        """Test with capital gains income."""
        inp = Form1040Input(
            wages=Decimal("50000"),
            interest_income=Decimal("1000"),
            capital_gains=Decimal("10000"),
            standard_deduction=True,
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("47150")

    def test_tax_credits(self):
        """Test with tax credits."""
        inp = Form1040Input(
            wages=Decimal("50000"),
            interest_income=Decimal("1000"),
            standard_deduction=True,
            filing_status="single",
            tax_credits=Decimal("2000"),
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.tax_liability < Decimal("5000")

    def test_negative_tax_liability_capped_at_zero(self):
        """Test that tax liability cannot be negative."""
        inp = Form1040Input(
            wages=Decimal("50000"),
            interest_income=Decimal("1000"),
            standard_deduction=True,
            filing_status="single",
            tax_credits=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.tax_liability == Decimal("0")

    def test_married_separate(self):
        """Test married filing separately."""
        inp = Form1040Input(
            wages=Decimal("50000"),
            interest_income=Decimal("1000"),
            standard_deduction=True,
            filing_status="married_separate",
            tax_year=2025,
        )
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("37150")
        assert result.tax_liability > Decimal("0")


class TestOverview:
    """Test Form 1040 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form1040_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form1040_overview()
        assert overview["form"] == "Form 1040"
        assert "1040" in overview["title"]


class TestRouter:
    """Integration tests for Form 1040 API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        from app.auth.utils import create_access_token
        token = create_access_token(data={"sub": "test-user", "tenant_id": "test-tenant"})
        return {"Authorization": f"Bearer {token}"}

    def test_calculate_endpoint(self, client, auth_headers):
        """Test POST /api/v1/form1040/calculate."""
        response = client.post(
            "/api/v1/form1040/calculate",
            json={
                "wages": "50000",
                "interest_income": "1000",
                "standard_deduction": True,
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "taxable_income" in data
        assert "tax_liability" in data
        assert "effective_tax_rate" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form1040/overview."""
        response = client.get(
            "/api/v1/form1040/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 1040"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form1040/calculate",
            json={
                "wages": "50000",
                "interest_income": "1000",
                "standard_deduction": True,
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form1040/overview")
        assert response.status_code == 401
