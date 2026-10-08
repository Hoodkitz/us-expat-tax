"""
Tests for Form 8959 — Additional Medicare Tax.
"""
import pytest
from decimal import Decimal
from app.modules.form8959 import (
    Form8959Input,
    Form8959Result,
    calculate_form8959,
    get_form8959_overview,
)


class TestCalculate:
    """Unit tests for Form 8959 calculation."""

    def test_basic_additional_medicare_tax(self):
        """Test basic additional Medicare tax."""
        inp = Form8959Input(
            wages=Decimal("200000"),
            self_employment_income=Decimal("0"),
            filing_status="single",
            medicare_withholding=Decimal("2900"),
            tax_year=2025,
        )
        result = calculate_form8959(inp)
        assert result.additional_medicare_tax == Decimal("0")

    def test_high_wages(self):
        """Test additional Medicare tax for high wages."""
        inp = Form8959Input(
            wages=Decimal("300000"),
            self_employment_income=Decimal("0"),
            filing_status="single",
            medicare_withholding=Decimal("4350"),
            tax_year=2025,
        )
        result = calculate_form8959(inp)
        assert result.additional_medicare_tax > Decimal("0")

    def test_self_employment_income(self):
        """Test additional Medicare tax with self-employment income."""
        inp = Form8959Input(
            wages=Decimal("0"),
            self_employment_income=Decimal("300000"),
            filing_status="single",
            medicare_withholding=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8959(inp)
        assert result.additional_medicare_tax > Decimal("0")

    def test_married_filing_jointly(self):
        """Test additional Medicare tax for married filing jointly."""
        inp = Form8959Input(
            wages=Decimal("300000"),
            self_employment_income=Decimal("0"),
            filing_status="married_joint",
            medicare_withholding=Decimal("4350"),
            tax_year=2025,
        )
        result = calculate_form8959(inp)
        assert result.additional_medicare_tax == Decimal("0")

    def test_no_income(self):
        """Test with no income."""
        inp = Form8959Input(
            wages=Decimal("0"),
            self_employment_income=Decimal("0"),
            filing_status="single",
            medicare_withholding=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8959(inp)
        assert result.additional_medicare_tax == Decimal("0")


class TestOverview:
    """Test Form 8959 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8959_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8959_overview()
        assert overview["form"] == "Form 8959"
        assert "8959" in overview["title"]


class TestRouter:
    """Integration tests for Form 8959 API endpoints."""

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
        """Test POST /api/v1/form8959/calculate."""
        response = client.post(
            "/api/v1/form8959/calculate",
            json={
                "wages": "200000",
                "self_employment_income": "0",
                "filing_status": "single",
                "medicare_withholding": "2900",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "additional_medicare_tax" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8959/overview."""
        response = client.get(
            "/api/v1/form8959/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8959"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8959/calculate",
            json={
                "wages": "200000",
                "self_employment_income": "0",
                "filing_status": "single",
                "medicare_withholding": "2900",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8959/overview")
        assert response.status_code == 401
