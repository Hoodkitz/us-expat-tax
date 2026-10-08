"""
Tests for Form 8812 — Credits for Qualifying Children.
"""
import pytest
from decimal import Decimal
from app.modules.form8812 import (
    Form8812Input,
    Form8812Result,
    calculate_form8812,
    get_form8812_overview,
)


class TestCalculate:
    """Unit tests for Form 8812 calculation."""

    def test_basic_child_tax_credit(self):
        """Test basic child tax credit calculation."""
        inp = Form8812Input(
            num_qualifying_children=2,
            num_other_dependents=0,
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8812(inp)
        assert result.child_tax_credit == Decimal("4000")
        assert result.total_credit == Decimal("4000")

    def test_credit_for_other_dependents(self):
        """Test credit for other dependents."""
        inp = Form8812Input(
            num_qualifying_children=1,
            num_other_dependents=1,
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8812(inp)
        assert result.child_tax_credit == Decimal("2000")
        assert result.credit_for_other_dependents == Decimal("500")
        assert result.total_credit == Decimal("2500")

    def test_high_agi_reduces_credit(self):
        """Test high AGI reduces credit."""
        inp = Form8812Input(
            num_qualifying_children=2,
            num_other_dependents=0,
            agi=Decimal("400000"),
            tax_year=2025,
        )
        result = calculate_form8812(inp)
        assert result.child_tax_credit < Decimal("4000")

    def test_no_children(self):
        """Test with no qualifying children."""
        inp = Form8812Input(
            num_qualifying_children=0,
            num_other_dependents=0,
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8812(inp)
        assert result.child_tax_credit == Decimal("0")
        assert result.total_credit == Decimal("0")

    def test_refundable_credit(self):
        """Test refundable credit calculation."""
        inp = Form8812Input(
            num_qualifying_children=2,
            num_other_dependents=0,
            agi=Decimal("30000"),
            tax_year=2025,
        )
        result = calculate_form8812(inp)
        assert result.refundable_credit > Decimal("0")


class TestOverview:
    """Test Form 8812 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8812_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8812_overview()
        assert overview["form"] == "Form 8812"
        assert "8812" in overview["title"]


class TestRouter:
    """Integration tests for Form 8812 API endpoints."""

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
        """Test POST /api/v1/form8812/calculate."""
        response = client.post(
            "/api/v1/form8812/calculate",
            json={
                "num_qualifying_children": 2,
                "num_other_dependents": 0,
                "agi": "50000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "child_tax_credit" in data
        assert "credit_for_other_dependents" in data
        assert "refundable_credit" in data
        assert "total_credit" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8812/overview."""
        response = client.get(
            "/api/v1/form8812/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8812"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8812/calculate",
            json={
                "num_qualifying_children": 2,
                "num_other_dependents": 0,
                "agi": "50000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8812/overview")
        assert response.status_code == 401
