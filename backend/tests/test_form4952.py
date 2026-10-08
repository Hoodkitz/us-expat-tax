"""
Tests for Form 4952 — Investment Interest Expense Deduction.
"""
import pytest
from decimal import Decimal
from app.modules.form4952 import (
    Form4952Input,
    Form4952Result,
    calculate_form4952,
    get_form4952_overview,
)


class TestCalculate:
    """Unit tests for Form 4952 calculation."""

    def test_basic_investment_interest(self):
        """Test basic investment interest deduction."""
        inp = Form4952Input(
            investment_interest_expense=Decimal("5000"),
            investment_income=Decimal("3000"),
            tax_year=2025,
        )
        result = calculate_form4952(inp)
        assert result.deductible_interest == Decimal("3000")
        assert result.disallowed_interest == Decimal("2000")
        assert result.carryforward == Decimal("2000")

    def test_no_carryforward(self):
        """Test when investment income exceeds interest expense."""
        inp = Form4952Input(
            investment_interest_expense=Decimal("3000"),
            investment_income=Decimal("5000"),
            tax_year=2025,
        )
        result = calculate_form4952(inp)
        assert result.deductible_interest == Decimal("3000")
        assert result.disallowed_interest == Decimal("0")
        assert result.carryforward == Decimal("0")

    def test_no_investment_income(self):
        """Test with no investment income."""
        inp = Form4952Input(
            investment_interest_expense=Decimal("5000"),
            investment_income=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form4952(inp)
        assert result.deductible_interest == Decimal("0")
        assert result.disallowed_interest == Decimal("5000")
        assert result.carryforward == Decimal("5000")

    def test_no_interest_expense(self):
        """Test with no investment interest expense."""
        inp = Form4952Input(
            investment_interest_expense=Decimal("0"),
            investment_income=Decimal("5000"),
            tax_year=2025,
        )
        result = calculate_form4952(inp)
        assert result.deductible_interest == Decimal("0")
        assert result.disallowed_interest == Decimal("0")
        assert result.carryforward == Decimal("0")

    def test_carryforward_from_prior_year(self):
        """Test with carryforward from prior year."""
        inp = Form4952Input(
            investment_interest_expense=Decimal("5000"),
            investment_income=Decimal("3000"),
            disallowed_interest_carryforward=Decimal("1000"),
            tax_year=2025,
        )
        result = calculate_form4952(inp)
        assert result.deductible_interest == Decimal("3000")
        assert result.disallowed_interest == Decimal("2000")
        assert result.carryforward == Decimal("3000")


class TestOverview:
    """Test Form 4952 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form4952_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form4952_overview()
        assert overview["form"] == "Form 4952"
        assert "4952" in overview["title"]


class TestRouter:
    """Integration tests for Form 4952 API endpoints."""

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
        """Test POST /api/v1/form4952/calculate."""
        response = client.post(
            "/api/v1/form4952/calculate",
            json={
                "investment_interest_expense": "5000",
                "investment_income": "3000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "deductible_interest" in data
        assert "disallowed_interest" in data
        assert "carryforward" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form4952/overview."""
        response = client.get(
            "/api/v1/form4952/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 4952"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form4952/calculate",
            json={
                "investment_interest_expense": "5000",
                "investment_income": "3000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form4952/overview")
        assert response.status_code == 401
