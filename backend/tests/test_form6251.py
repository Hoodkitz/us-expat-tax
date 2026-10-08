"""
Tests for Form 6251 — Alternative Minimum Tax.
"""
import pytest
from decimal import Decimal
from app.modules.form6251 import (
    Form6251Input,
    Form6251Result,
    calculate_form6251,
    get_form6251_overview,
)


class TestCalculate:
    """Unit tests for Form 6251 calculation."""

    def test_basic_amt_calculation(self):
        """Test basic AMT calculation."""
        inp = Form6251Input(
            filing_status="single",
            regular_taxable_income=Decimal("100000"),
            tax_preferences=Decimal("0"),
            adjustments=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form6251(inp)
        assert result.amt_income == Decimal("100000")
        assert result.exemption > Decimal("0")
        assert result.amt_base >= Decimal("0")

    def test_no_amt_due(self):
        """Test when no AMT is due."""
        inp = Form6251Input(
            filing_status="single",
            regular_taxable_income=Decimal("50000"),
            tax_preferences=Decimal("0"),
            adjustments=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form6251(inp)
        assert result.amt_due == Decimal("0")

    def test_amt_with_preferences(self):
        """Test AMT with tax preference items."""
        inp = Form6251Input(
            filing_status="single",
            regular_taxable_income=Decimal("200000"),
            tax_preferences=Decimal("50000"),
            adjustments=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form6251(inp)
        assert result.amt_income == Decimal("250000")
        assert result.amt_due > Decimal("0")

    def test_married_filing_jointly(self):
        """Test AMT for married filing jointly."""
        inp = Form6251Input(
            filing_status="married_joint",
            regular_taxable_income=Decimal("150000"),
            tax_preferences=Decimal("0"),
            adjustments=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form6251(inp)
        assert result.exemption > Decimal("0")

    def test_exemption_phaseout(self):
        """Test exemption phaseout for high income."""
        inp = Form6251Input(
            filing_status="single",
            regular_taxable_income=Decimal("500000"),
            tax_preferences=Decimal("0"),
            adjustments=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form6251(inp)
        assert result.exemption < Decimal("81300")


class TestOverview:
    """Test Form 6251 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form6251_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form6251_overview()
        assert overview["form"] == "Form 6251"
        assert "6251" in overview["title"]


class TestRouter:
    """Integration tests for Form 6251 API endpoints."""

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
        """Test POST /api/v1/form6251/calculate."""
        response = client.post(
            "/api/v1/form6251/calculate",
            json={
                "filing_status": "single",
                "regular_taxable_income": "100000",
                "tax_preferences": "0",
                "adjustments": "0",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "amt_income" in data
        assert "exemption" in data
        assert "amt_base" in data
        assert "amt" in data
        assert "regular_tax" in data
        assert "amt_due" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form6251/overview."""
        response = client.get(
            "/api/v1/form6251/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 6251"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form6251/calculate",
            json={
                "filing_status": "single",
                "regular_taxable_income": "100000",
                "tax_preferences": "0",
                "adjustments": "0",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form6251/overview")
        assert response.status_code == 401
