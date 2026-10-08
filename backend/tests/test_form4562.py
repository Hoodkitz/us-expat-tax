"""
Tests for Form 4562 — Depreciation and Amortization.
"""
import pytest
from decimal import Decimal
from app.modules.form4562 import (
    Form4562Input,
    Form4562Result,
    calculate_form4562,
    get_form4562_overview,
)


class TestCalculate:
    """Unit tests for Form 4562 calculation."""

    def test_basic_depreciation(self):
        """Test basic depreciation calculation."""
        inp = Form4562Input(
            asset_cost=Decimal("10000"),
            asset_type="5-year",
            business_use_percentage=Decimal("100"),
            section_179_election=False,
            bonus_depreciation=False,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.total_depreciation > Decimal("0")
        assert result.regular_depreciation > Decimal("0")

    def test_section_179_election(self):
        """Test Section 179 election."""
        inp = Form4562Input(
            asset_cost=Decimal("50000"),
            asset_type="5-year",
            business_use_percentage=Decimal("100"),
            section_179_election=True,
            bonus_depreciation=False,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.section_179_deduction == Decimal("50000")
        assert result.total_depreciation >= result.section_179_deduction

    def test_bonus_depreciation(self):
        """Test bonus depreciation."""
        inp = Form4562Input(
            asset_cost=Decimal("50000"),
            asset_type="5-year",
            business_use_percentage=Decimal("100"),
            section_179_election=False,
            bonus_depreciation=True,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.bonus_depreciation == Decimal("20000")
        assert result.total_depreciation > result.bonus_depreciation

    def test_partial_business_use(self):
        """Test partial business use percentage."""
        inp = Form4562Input(
            asset_cost=Decimal("10000"),
            asset_type="5-year",
            business_use_percentage=Decimal("50"),
            section_179_election=False,
            bonus_depreciation=False,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.total_depreciation < Decimal("2000")

    def test_7_year_asset(self):
        """Test 7-year asset depreciation."""
        inp = Form4562Input(
            asset_cost=Decimal("10000"),
            asset_type="7-year",
            business_use_percentage=Decimal("100"),
            section_179_election=False,
            bonus_depreciation=False,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.regular_depreciation > Decimal("0")

    def test_39_year_asset(self):
        """Test 39-year asset depreciation."""
        inp = Form4562Input(
            asset_cost=Decimal("100000"),
            asset_type="39-year",
            business_use_percentage=Decimal("100"),
            section_179_election=False,
            bonus_depreciation=False,
            tax_year=2025,
        )
        result = calculate_form4562(inp)
        assert result.regular_depreciation > Decimal("0")
        assert result.regular_depreciation < Decimal("3000")


class TestOverview:
    """Test Form 4562 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form4562_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form4562_overview()
        assert overview["form"] == "Form 4562"
        assert "4562" in overview["title"]


class TestRouter:
    """Integration tests for Form 4562 API endpoints."""

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
        """Test POST /api/v1/form4562/calculate."""
        response = client.post(
            "/api/v1/form4562/calculate",
            json={
                "asset_cost": "10000",
                "asset_type": "5-year",
                "business_use_percentage": "100",
                "section_179_election": False,
                "bonus_depreciation": False,
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "section_179_deduction" in data
        assert "bonus_depreciation" in data
        assert "regular_depreciation" in data
        assert "total_depreciation" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form4562/overview."""
        response = client.get(
            "/api/v1/form4562/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 4562"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form4562/calculate",
            json={
                "asset_cost": "10000",
                "asset_type": "5-year",
                "business_use_percentage": "100",
                "section_179_election": False,
                "bonus_depreciation": False,
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form4562/overview")
        assert response.status_code == 401
