"""
Tests for Form 2106 — Employee Business Expenses.
"""
import pytest
from decimal import Decimal
from app.modules.form2106 import (
    Form2106Input,
    Form2106Result,
    calculate_form2106,
    get_form2106_overview,
)


class TestCalculate:
    """Unit tests for Form 2106 calculation."""

    def test_basic_employee_expenses(self):
        """Test basic employee business expenses."""
        inp = Form2106Input(
            employee_expenses=Decimal("5000"),
            travel_expenses=Decimal("2000"),
            meal_expenses=Decimal("1000"),
            vehicle_expenses=Decimal("1500"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2106(inp)
        assert result.total_expenses == Decimal("9500")
        assert result.deductible_meals == Decimal("500")
        assert result.deductible_expenses > Decimal("0")
        assert result.net_deduction > Decimal("0")

    def test_no_expenses(self):
        """Test with no expenses."""
        inp = Form2106Input(
            employee_expenses=Decimal("0"),
            travel_expenses=Decimal("0"),
            meal_expenses=Decimal("0"),
            vehicle_expenses=Decimal("0"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2106(inp)
        assert result.total_expenses == Decimal("0")
        assert result.net_deduction == Decimal("0")

    def test_agi_floor(self):
        """Test AGI floor (2% of AGI)."""
        inp = Form2106Input(
            employee_expenses=Decimal("5000"),
            travel_expenses=Decimal("2000"),
            meal_expenses=Decimal("1000"),
            vehicle_expenses=Decimal("1500"),
            agi=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form2106(inp)
        assert result.agi_floor == Decimal("2000")
        assert result.net_deduction == result.deductible_expenses - result.agi_floor

    def test_high_agi_reduces_deduction(self):
        """Test that high AGI reduces deduction."""
        inp = Form2106Input(
            employee_expenses=Decimal("5000"),
            travel_expenses=Decimal("2000"),
            meal_expenses=Decimal("1000"),
            vehicle_expenses=Decimal("1500"),
            agi=Decimal("200000"),
            tax_year=2025,
        )
        result = calculate_form2106(inp)
        assert result.agi_floor == Decimal("4000")
        assert result.net_deduction < result.deductible_expenses

    def test_meal_deduction_50_percent(self):
        """Test that meals are 50% deductible."""
        inp = Form2106Input(
            employee_expenses=Decimal("0"),
            travel_expenses=Decimal("0"),
            meal_expenses=Decimal("1000"),
            vehicle_expenses=Decimal("0"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2106(inp)
        assert result.deductible_meals == Decimal("500")


class TestOverview:
    """Test Form 2106 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form2106_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form2106_overview()
        assert overview["form"] == "Form 2106"
        assert "2106" in overview["title"]


class TestRouter:
    """Integration tests for Form 2106 API endpoints."""

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
        """Test POST /api/v1/form2106/calculate."""
        response = client.post(
            "/api/v1/form2106/calculate",
            json={
                "employee_expenses": "5000",
                "travel_expenses": "2000",
                "meal_expenses": "1000",
                "vehicle_expenses": "1500",
                "agi": "50000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_expenses" in data
        assert "deductible_meals" in data
        assert "deductible_expenses" in data
        assert "agi_floor" in data
        assert "net_deduction" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form2106/overview."""
        response = client.get(
            "/api/v1/form2106/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 2106"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form2106/calculate",
            json={
                "employee_expenses": "5000",
                "travel_expenses": "2000",
                "meal_expenses": "1000",
                "vehicle_expenses": "1500",
                "agi": "50000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form2106/overview")
        assert response.status_code == 401
