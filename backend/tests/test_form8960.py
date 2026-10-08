"""
Tests for Form 8960 — Net Investment Income Tax.
"""
import pytest
from decimal import Decimal
from app.modules.form8960 import (
    Form8960Input,
    Form8960Result,
    calculate_form8960,
    get_form8960_overview,
)


class TestCalculate:
    """Unit tests for Form 8960 calculation."""

    def test_basic_niit(self):
        """Test basic Net Investment Income Tax."""
        inp = Form8960Input(
            filing_status="single",
            magi=Decimal("200000"),
            net_investment_income=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8960(inp)
        assert result.niit == Decimal("0")
        assert result.threshold == Decimal("200000")
        assert result.excess_magi == Decimal("0")

    def test_high_magi_niit(self):
        """Test NIIT for high MAGI."""
        inp = Form8960Input(
            filing_status="single",
            magi=Decimal("300000"),
            net_investment_income=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8960(inp)
        assert result.niit > Decimal("0")
        assert result.excess_magi == Decimal("100000")

    def test_no_net_investment_income(self):
        """Test with no net investment income."""
        inp = Form8960Input(
            filing_status="single",
            magi=Decimal("300000"),
            net_investment_income=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8960(inp)
        assert result.niit == Decimal("0")

    def test_married_filing_jointly(self):
        """Test NIIT for married filing jointly."""
        inp = Form8960Input(
            filing_status="married_joint",
            magi=Decimal("300000"),
            net_investment_income=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8960(inp)
        assert result.niit == Decimal("0")
        assert result.threshold == Decimal("250000")

    def test_threshold_amount(self):
        """Test threshold amount calculation."""
        inp = Form8960Input(
            filing_status="single",
            magi=Decimal("250000"),
            net_investment_income=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8960(inp)
        assert result.threshold == Decimal("200000")
        assert result.excess_magi == Decimal("50000")


class TestOverview:
    """Test Form 8960 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8960_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8960_overview()
        assert overview["form"] == "Form 8960"
        assert "8960" in overview["title"]


class TestRouter:
    """Integration tests for Form 8960 API endpoints."""

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
        """Test POST /api/v1/form8960/calculate."""
        response = client.post(
            "/api/v1/form8960/calculate",
            json={
                "filing_status": "single",
                "magi": "200000",
                "net_investment_income": "50000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "niit" in data
        assert "threshold" in data
        assert "excess_magi" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8960/overview."""
        response = client.get(
            "/api/v1/form8960/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8960"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8960/calculate",
            json={
                "filing_status": "single",
                "magi": "200000",
                "net_investment_income": "50000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8960/overview")
        assert response.status_code == 401
