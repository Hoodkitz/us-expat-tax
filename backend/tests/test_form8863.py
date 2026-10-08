"""
Tests for Form 8863 — Education Credits.
"""
import pytest
from decimal import Decimal
from app.modules.form8863 import (
    Form8863Input,
    Form8863Result,
    calculate_form8863,
    get_form8863_overview,
)


class TestCalculate:
    """Unit tests for Form 8863 calculation."""

    def test_basic_american_opportunity_credit(self):
        """Test basic American Opportunity Tax Credit."""
        inp = Form8863Input(
            credit_type="aotc",
            qualified_expenses=Decimal("4000"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8863(inp)
        assert result.credit_amount == Decimal("2500")
        assert result.refundable_amount == Decimal("1000")
        assert result.nonrefundable_amount == Decimal("1500")

    def test_lifetime_learning_credit(self):
        """Test Lifetime Learning Credit."""
        inp = Form8863Input(
            credit_type="llc",
            qualified_expenses=Decimal("10000"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8863(inp)
        assert result.credit_amount == Decimal("2000")
        assert result.refundable_amount == Decimal("0")
        assert result.nonrefundable_amount == Decimal("2000")

    def test_high_agi_reduces_credit(self):
        """Test high AGI reduces education credit."""
        inp = Form8863Input(
            credit_type="aotc",
            qualified_expenses=Decimal("4000"),
            agi=Decimal("90000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8863(inp)
        assert result.credit_amount < Decimal("2500")

    def test_no_qualified_expenses(self):
        """Test with no qualified expenses."""
        inp = Form8863Input(
            credit_type="aotc",
            qualified_expenses=Decimal("0"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8863(inp)
        assert result.credit_amount == Decimal("0")

    def test_married_filing_jointly(self):
        """Test education credit for married filing jointly."""
        inp = Form8863Input(
            credit_type="aotc",
            qualified_expenses=Decimal("4000"),
            agi=Decimal("100000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8863(inp)
        assert result.credit_amount == Decimal("2500")


class TestOverview:
    """Test Form 8863 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8863_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8863_overview()
        assert overview["form"] == "Form 8863"
        assert "8863" in overview["title"]


class TestRouter:
    """Integration tests for Form 8863 API endpoints."""

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
        """Test POST /api/v1/form8863/calculate."""
        response = client.post(
            "/api/v1/form8863/calculate",
            json={
                "credit_type": "aotc",
                "qualified_expenses": "4000",
                "agi": "50000",
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "credit_amount" in data
        assert "refundable_amount" in data
        assert "nonrefundable_amount" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8863/overview."""
        response = client.get(
            "/api/v1/form8863/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8863"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8863/calculate",
            json={
                "credit_type": "aotc",
                "qualified_expenses": "4000",
                "agi": "50000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8863/overview")
        assert response.status_code == 401
