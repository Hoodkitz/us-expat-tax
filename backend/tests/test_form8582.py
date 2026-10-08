"""
Tests for Form 8582 — Passive Activity Loss Limitations.
"""
import pytest
from decimal import Decimal
from app.modules.form8582 import (
    Form8582Input,
    Form8582Result,
    calculate_form8582,
    get_form8582_overview,
)


class TestCalculate:
    """Unit tests for Form 8582 calculation."""

    def test_basic_passive_loss(self):
        """Test basic passive loss calculation."""
        inp = Form8582Input(
            passive_income=Decimal("0"),
            passive_losses=Decimal("10000"),
            agi=Decimal("100000"),
            active_participation=False,
            tax_year=2025,
        )
        result = calculate_form8582(inp)
        assert result.deductible_loss == Decimal("0")
        assert result.suspended_loss == Decimal("10000")

    def test_active_participation_allowance(self):
        """Test active participation special allowance."""
        inp = Form8582Input(
            passive_income=Decimal("0"),
            passive_losses=Decimal("25000"),
            agi=Decimal("100000"),
            active_participation=True,
            tax_year=2025,
        )
        result = calculate_form8582(inp)
        assert result.special_allowance == Decimal("25000")
        assert result.deductible_loss == Decimal("25000")

    def test_passive_income_offset(self):
        """Test passive income offsetting passive losses."""
        inp = Form8582Input(
            passive_income=Decimal("5000"),
            passive_losses=Decimal("10000"),
            agi=Decimal("100000"),
            active_participation=False,
            tax_year=2025,
        )
        result = calculate_form8582(inp)
        assert result.deductible_loss == Decimal("5000")
        assert result.suspended_loss == Decimal("5000")

    def test_no_passive_losses(self):
        """Test with no passive losses."""
        inp = Form8582Input(
            passive_income=Decimal("5000"),
            passive_losses=Decimal("0"),
            agi=Decimal("100000"),
            active_participation=False,
            tax_year=2025,
        )
        result = calculate_form8582(inp)
        assert result.deductible_loss == Decimal("0")
        assert result.suspended_loss == Decimal("0")

    def test_high_agi_no_allowance(self):
        """Test high AGI disqualifies special allowance."""
        inp = Form8582Input(
            passive_income=Decimal("0"),
            passive_losses=Decimal("25000"),
            agi=Decimal("200000"),
            active_participation=True,
            tax_year=2025,
        )
        result = calculate_form8582(inp)
        assert result.special_allowance == Decimal("0")
        assert result.deductible_loss == Decimal("0")


class TestOverview:
    """Test Form 8582 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8582_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8582_overview()
        assert overview["form"] == "Form 8582"
        assert "8582" in overview["title"]


class TestRouter:
    """Integration tests for Form 8582 API endpoints."""

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
        """Test POST /api/v1/form8582/calculate."""
        response = client.post(
            "/api/v1/form8582/calculate",
            json={
                "passive_income": "0",
                "passive_losses": "10000",
                "agi": "100000",
                "active_participation": False,
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "deductible_loss" in data
        assert "suspended_loss" in data
        assert "special_allowance" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8582/overview."""
        response = client.get(
            "/api/v1/form8582/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8582"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8582/calculate",
            json={
                "passive_income": "0",
                "passive_losses": "10000",
                "agi": "100000",
                "active_participation": False,
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8582/overview")
        assert response.status_code == 401
