"""
Tests for Form 8283 — Noncash Charitable Contributions.
"""
import pytest
from decimal import Decimal
from app.modules.form8283 import (
    Form8283Input,
    Form8283Result,
    calculate_form8283,
    get_form8283_overview,
)


class TestCalculate:
    """Unit tests for Form 8283 calculation."""

    def test_basic_noncash_contribution(self):
        """Test basic noncash charitable contribution."""
        inp = Form8283Input(
            property_type="stock",
            fair_market_value=Decimal("10000"),
            cost_basis=Decimal("5000"),
            appraisal_required=False,
            tax_year=2025,
        )
        result = calculate_form8283(inp)
        assert result.deductible_amount == Decimal("10000")
        assert result.appraisal_required is False

    def test_appraisal_required(self):
        """Test when appraisal is required."""
        inp = Form8283Input(
            property_type="art",
            fair_market_value=Decimal("100000"),
            cost_basis=Decimal("50000"),
            appraisal_required=True,
            tax_year=2025,
        )
        result = calculate_form8283(inp)
        assert result.appraisal_required is True
        assert result.deductible_amount == Decimal("100000")

    def test_cost_basis_higher_than_fmv(self):
        """Test when cost basis is higher than fair market value."""
        inp = Form8283Input(
            property_type="stock",
            fair_market_value=Decimal("5000"),
            cost_basis=Decimal("10000"),
            appraisal_required=False,
            tax_year=2025,
        )
        result = calculate_form8283(inp)
        assert result.deductible_amount == Decimal("5000")

    def test_vehicle_donation(self):
        """Test vehicle donation."""
        inp = Form8283Input(
            property_type="vehicle",
            fair_market_value=Decimal("5000"),
            cost_basis=Decimal("10000"),
            appraisal_required=False,
            tax_year=2025,
        )
        result = calculate_form8283(inp)
        assert result.deductible_amount == Decimal("5000")


class TestOverview:
    """Test Form 8283 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8283_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8283_overview()
        assert overview["form"] == "Form 8283"
        assert "8283" in overview["title"]


class TestRouter:
    """Integration tests for Form 8283 API endpoints."""

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
        """Test POST /api/v1/form8283/calculate."""
        response = client.post(
            "/api/v1/form8283/calculate",
            json={
                "property_type": "stock",
                "fair_market_value": "10000",
                "cost_basis": "5000",
                "appraisal_required": False,
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "deductible_amount" in data
        assert "appraisal_required" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8283/overview."""
        response = client.get(
            "/api/v1/form8283/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8283"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8283/calculate",
            json={
                "property_type": "stock",
                "fair_market_value": "10000",
                "cost_basis": "5000",
                "appraisal_required": False,
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8283/overview")
        assert response.status_code == 401
