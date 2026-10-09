"""
Tests for Form 8919 — Uncollected Social Security and Medicare Tax on Wages.
"""
import pytest
from decimal import Decimal
from app.modules.form8919 import (
    Form8919Input,
    Form8919Result,
    calculate_form8919,
    get_form8919_overview,
)


class TestCalculate:
    """Unit tests for Form 8919 calculation."""

    def test_basic_calculation(self):
        """Test basic FICA calculation."""
        inp = Form8919Input(
            wages=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        # SS: 50000 * 0.062 = 3100
        # Medicare: 50000 * 0.0145 = 725
        # Total: 3825
        assert result.social_security_tax == Decimal("3100.00")
        assert result.medicare_tax == Decimal("725.00")
        assert result.total_tax == Decimal("3825.00")

    def test_wages_at_ss_wage_base(self):
        """Test wages exactly at the Social Security wage base."""
        inp = Form8919Input(
            wages=Decimal("176100"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        # SS: 176100 * 0.062 = 10918.20
        # Medicare: 176100 * 0.0145 = 2553.45
        assert result.social_security_tax == Decimal("10918.20")
        assert result.medicare_tax == Decimal("2553.45")
        assert result.total_tax == Decimal("13471.65")

    def test_wages_above_ss_wage_base(self):
        """Test wages above the Social Security wage base — SS capped, Medicare not."""
        inp = Form8919Input(
            wages=Decimal("200000"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        # SS: 176100 * 0.062 = 10918.20 (capped at wage base)
        # Medicare: 200000 * 0.0145 = 2900.00 (no cap)
        assert result.social_security_tax == Decimal("10918.20")
        assert result.medicare_tax == Decimal("2900.00")
        assert result.total_tax == Decimal("13818.20")

    def test_zero_wages(self):
        """Test with zero wages."""
        inp = Form8919Input(
            wages=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        assert result.social_security_tax == Decimal("0.00")
        assert result.medicare_tax == Decimal("0.00")
        assert result.total_tax == Decimal("0.00")

    def test_small_wages(self):
        """Test with small wages."""
        inp = Form8919Input(
            wages=Decimal("1000"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        # SS: 1000 * 0.062 = 62
        # Medicare: 1000 * 0.0145 = 14.50
        assert result.social_security_tax == Decimal("62.00")
        assert result.medicare_tax == Decimal("14.50")
        assert result.total_tax == Decimal("76.50")

    def test_rounding(self):
        """Test that rounding works correctly."""
        inp = Form8919Input(
            wages=Decimal("12345.67"),
            tax_year=2025,
        )
        result = calculate_form8919(inp)
        # SS: 12345.67 * 0.062 = 765.43154 -> 765.43
        # Medicare: 12345.67 * 0.0145 = 179.012215 -> 179.01
        assert result.social_security_tax == Decimal("765.43")
        assert result.medicare_tax == Decimal("179.01")
        assert result.total_tax == Decimal("944.44")


class TestOverview:
    """Test Form 8919 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8919_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8919_overview()
        assert overview["form"] == "Form 8919"
        assert "Social Security" in overview["title"]


class TestRouter:
    """Integration tests for Form 8919 API endpoints."""

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
        """Test POST /api/v1/form8919/calculate."""
        response = client.post(
            "/api/v1/form8919/calculate",
            json={
                "wages": "50000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "social_security_tax" in data
        assert "medicare_tax" in data
        assert "total_tax" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8919/overview."""
        response = client.get(
            "/api/v1/form8919/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8919"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8919/calculate",
            json={
                "wages": "50000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8919/overview")
        assert response.status_code == 401
