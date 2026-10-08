"""
Tests for Form 8990 — Business Interest Expense Limitation.
"""
import pytest
from decimal import Decimal
from app.modules.form8990 import (
    Form8990Input,
    Form8990Result,
    calculate_form8990,
    get_form8990_overview,
    ATI_PERCENTAGE,
    SMALL_BUSINESS_THRESHOLD,
)


class TestCalculate:
    """Unit tests for Form 8990 calculation."""

    def test_basic_30_percent_ati(self):
        """Test basic 30% ATI limitation."""
        inp = Form8990Input(
            business_interest_expense=Decimal("50000"),
            adjusted_taxable_income=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 100000 * 0.30 = 30000
        assert result.limitation == Decimal("30000.00")
        assert result.deductible_interest == Decimal("30000.00")
        assert result.excess_interest == Decimal("20000.00")
        assert result.carryforward == Decimal("20000.00")

    def test_small_business_exception(self):
        """Test small business exception — full deduction."""
        inp = Form8990Input(
            business_interest_expense=Decimal("50000"),
            adjusted_taxable_income=Decimal("100000"),
            small_business_exception=True,
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = business_interest_expense = 50000
        assert result.limitation == Decimal("50000.00")
        assert result.deductible_interest == Decimal("50000.00")
        assert result.excess_interest == Decimal("0.00")
        assert result.carryforward == Decimal("0.00")

    def test_floor_plan_financing_interest(self):
        """Test floor plan financing interest added to limitation."""
        inp = Form8990Input(
            business_interest_expense=Decimal("50000"),
            adjusted_taxable_income=Decimal("100000"),
            floor_plan_financing_interest=Decimal("5000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 30000 + 5000 = 35000
        assert result.limitation == Decimal("35000.00")
        assert result.deductible_interest == Decimal("35000.00")
        assert result.excess_interest == Decimal("15000.00")
        assert result.carryforward == Decimal("15000.00")

    def test_excess_interest_carryforward(self):
        """Test excess interest carryforward."""
        inp = Form8990Input(
            business_interest_expense=Decimal("100000"),
            adjusted_taxable_income=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 30000, deductible = 30000, excess = 70000
        assert result.deductible_interest == Decimal("30000.00")
        assert result.excess_interest == Decimal("70000.00")
        assert result.carryforward == Decimal("70000.00")

    def test_no_excess_interest(self):
        """Test when interest expense is below limitation."""
        inp = Form8990Input(
            business_interest_expense=Decimal("20000"),
            adjusted_taxable_income=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 30000, deductible = 20000, excess = 0
        assert result.deductible_interest == Decimal("20000.00")
        assert result.excess_interest == Decimal("0.00")
        assert result.carryforward == Decimal("0.00")

    def test_zero_ati(self):
        """Test with zero ATI — no deduction."""
        inp = Form8990Input(
            business_interest_expense=Decimal("50000"),
            adjusted_taxable_income=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 0, deductible = 0, excess = 50000
        assert result.limitation == Decimal("0.00")
        assert result.deductible_interest == Decimal("0.00")
        assert result.excess_interest == Decimal("50000.00")
        assert result.carryforward == Decimal("50000.00")

    def test_zero_interest_expense(self):
        """Test with zero interest expense."""
        inp = Form8990Input(
            business_interest_expense=Decimal("0"),
            adjusted_taxable_income=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        assert result.limitation == Decimal("30000.00")
        assert result.deductible_interest == Decimal("0.00")
        assert result.excess_interest == Decimal("0.00")
        assert result.carryforward == Decimal("0.00")

    def test_small_business_with_floor_plan(self):
        """Test small business exception with floor plan financing."""
        inp = Form8990Input(
            business_interest_expense=Decimal("50000"),
            adjusted_taxable_income=Decimal("100000"),
            floor_plan_financing_interest=Decimal("5000"),
            small_business_exception=True,
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 50000 + 5000 = 55000
        assert result.limitation == Decimal("55000.00")
        assert result.deductible_interest == Decimal("50000.00")
        assert result.excess_interest == Decimal("0.00")

    def test_large_ati(self):
        """Test with large ATI — high limitation."""
        inp = Form8990Input(
            business_interest_expense=Decimal("500000"),
            adjusted_taxable_income=Decimal("2000000"),
            tax_year=2025,
        )
        result = calculate_form8990(inp)
        # limitation = 2000000 * 0.30 = 600000
        assert result.limitation == Decimal("600000.00")
        assert result.deductible_interest == Decimal("500000.00")
        assert result.excess_interest == Decimal("0.00")


class TestOverview:
    """Test Form 8990 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8990_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8990_overview()
        assert overview["form"] == "Form 8990"
        assert "8990" in overview["title"] or "Business Interest" in overview["title"]


class TestRouter:
    """Integration tests for Form 8990 API endpoints."""

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
        """Test POST /api/v1/form8990/calculate."""
        response = client.post(
            "/api/v1/form8990/calculate",
            json={
                "business_interest_expense": "50000",
                "adjusted_taxable_income": "100000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "limitation" in data
        assert "deductible_interest" in data
        assert "excess_interest" in data
        assert "carryforward" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8990/overview."""
        response = client.get(
            "/api/v1/form8990/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8990"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8990/calculate",
            json={
                "business_interest_expense": "50000",
                "adjusted_taxable_income": "100000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8990/overview")
        assert response.status_code == 401

    def test_calculate_small_business_exception(self, client, auth_headers):
        """Test calculate endpoint with small business exception."""
        response = client.post(
            "/api/v1/form8990/calculate",
            json={
                "business_interest_expense": "50000",
                "adjusted_taxable_income": "100000",
                "small_business_exception": True,
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["deductible_interest"]) == 50000.0
        assert float(data["excess_interest"]) == 0.0
