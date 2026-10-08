"""
Tests for Form 8880 — Credit for Retirement Savings Contributions.
"""
import pytest
from decimal import Decimal
from app.modules.form8880 import (
    Form8880Input,
    Form8880Result,
    calculate_form8880,
    get_form8880_overview,
)


class TestCalculate:
    """Unit tests for Form 8880 calculation."""

    def test_basic_retirement_savings_credit(self):
        """Test basic retirement savings credit."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("30000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.5")
        assert result.credit_amount == Decimal("1000")

    def test_married_filing_jointly(self):
        """Test retirement savings credit for married filing jointly."""
        inp = Form8880Input(
            retirement_contributions=Decimal("4000"),
            agi=Decimal("40000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_rate == Decimal("0.5")
        assert result.credit_amount == Decimal("2000")

    def test_high_agi_no_credit(self):
        """Test high AGI results in no credit."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_amount == Decimal("0")

    def test_no_contributions(self):
        """Test with no contributions."""
        inp = Form8880Input(
            retirement_contributions=Decimal("0"),
            agi=Decimal("30000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_amount == Decimal("0")

    def test_maximum_credit(self):
        """Test maximum credit amount."""
        inp = Form8880Input(
            retirement_contributions=Decimal("2000"),
            agi=Decimal("20000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8880(inp)
        assert result.credit_amount == Decimal("1000")


class TestOverview:
    """Test Form 8880 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8880_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8880_overview()
        assert overview["form"] == "Form 8880"
        assert "8880" in overview["title"]


class TestRouter:
    """Integration tests for Form 8880 API endpoints."""

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
        """Test POST /api/v1/form8880/calculate."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "2000",
                "agi": "30000",
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "credit_rate" in data
        assert "credit_amount" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8880/overview."""
        response = client.get(
            "/api/v1/form8880/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8880"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8880/calculate",
            json={
                "retirement_contributions": "2000",
                "agi": "30000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8880/overview")
        assert response.status_code == 401
