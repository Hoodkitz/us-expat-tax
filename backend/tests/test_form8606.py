"""
Tests for Form 8606 — Nondeductible IRAs.
"""
import pytest
from decimal import Decimal
from app.modules.form8606 import (
    Form8606Input,
    Form8606Result,
    calculate_form8606,
    get_form8606_overview,
)


class TestCalculate:
    """Unit tests for Form 8606 calculation."""

    def test_basic_nondeductible_ira(self):
        """Test basic nondeductible IRA distribution."""
        inp = Form8606Input(
            nondeductible_contributions=Decimal("6000"),
            traditional_ira_basis=Decimal("6000"),
            distributions=Decimal("10000"),
            ira_balance=Decimal("20000"),
            tax_year=2025,
        )
        result = calculate_form8606(inp)
        assert result.total_basis == Decimal("12000")
        assert result.taxable_distribution > Decimal("0")
        assert result.nontaxable_distribution > Decimal("0")

    def test_fully_taxable_distribution(self):
        """Test fully taxable distribution."""
        inp = Form8606Input(
            nondeductible_contributions=Decimal("0"),
            traditional_ira_basis=Decimal("0"),
            distributions=Decimal("10000"),
            ira_balance=Decimal("20000"),
            tax_year=2025,
        )
        result = calculate_form8606(inp)
        assert result.taxable_distribution == Decimal("10000")
        assert result.nontaxable_distribution == Decimal("0")

    def test_fully_nontaxable_distribution(self):
        """Test fully nontaxable distribution."""
        inp = Form8606Input(
            nondeductible_contributions=Decimal("20000"),
            traditional_ira_basis=Decimal("20000"),
            distributions=Decimal("10000"),
            ira_balance=Decimal("20000"),
            tax_year=2025,
        )
        result = calculate_form8606(inp)
        assert result.taxable_distribution == Decimal("0")
        assert result.nontaxable_distribution == Decimal("10000")

    def test_no_distributions(self):
        """Test with no distributions."""
        inp = Form8606Input(
            nondeductible_contributions=Decimal("6000"),
            traditional_ira_basis=Decimal("6000"),
            distributions=Decimal("0"),
            ira_balance=Decimal("20000"),
            tax_year=2025,
        )
        result = calculate_form8606(inp)
        assert result.taxable_distribution == Decimal("0")
        assert result.nontaxable_distribution == Decimal("0")
        assert result.remaining_basis == Decimal("12000")


class TestOverview:
    """Test Form 8606 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8606_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8606_overview()
        assert overview["form"] == "Form 8606"
        assert "8606" in overview["title"]


class TestRouter:
    """Integration tests for Form 8606 API endpoints."""

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
        """Test POST /api/v1/form8606/calculate."""
        response = client.post(
            "/api/v1/form8606/calculate",
            json={
                "nondeductible_contributions": "6000",
                "traditional_ira_basis": "6000",
                "distributions": "10000",
                "ira_balance": "20000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_basis" in data
        assert "taxable_distribution" in data
        assert "nontaxable_distribution" in data
        assert "remaining_basis" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8606/overview."""
        response = client.get(
            "/api/v1/form8606/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8606"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8606/calculate",
            json={
                "nondeductible_contributions": "6000",
                "traditional_ira_basis": "6000",
                "distributions": "10000",
                "ira_balance": "20000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8606/overview")
        assert response.status_code == 401
