"""
Tests for Form 2441 — Child and Dependent Care Expenses.
"""
import pytest
from decimal import Decimal
from app.modules.form2441 import (
    Form2441Input,
    Form2441Result,
    calculate_form2441,
    get_form2441_overview,
)


class TestCalculate:
    """Unit tests for Form 2441 calculation."""

    def test_basic_child_care_credit(self):
        """Test basic child and dependent care credit."""
        inp = Form2441Input(
            num_dependents=2,
            care_expenses=Decimal("6000"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal("6000")
        assert result.applicable_percentage > Decimal("0")
        assert result.credit_amount > Decimal("0")

    def test_high_agi_reduces_credit(self):
        """Test that high AGI reduces credit percentage."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal("3000"),
            agi=Decimal("100000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.applicable_percentage < Decimal("0.35")

    def test_low_income_max_credit(self):
        """Test that low income gets maximum credit percentage."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal("3000"),
            agi=Decimal("15000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.applicable_percentage == Decimal("0.35")

    def test_max_expenses_one_dependent(self):
        """Test max expenses for one dependent."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal("10000"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal("3000")

    def test_max_expenses_two_dependents(self):
        """Test max expenses for two dependents."""
        inp = Form2441Input(
            num_dependents=2,
            care_expenses=Decimal("10000"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal("6000")

    def test_no_expenses(self):
        """Test with no care expenses."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal("0"),
            agi=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.credit_amount == Decimal("0")


class TestOverview:
    """Test Form 2441 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form2441_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form2441_overview()
        assert overview["form"] == "Form 2441"
        assert "2441" in overview["title"]


class TestRouter:
    """Integration tests for Form 2441 API endpoints."""

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
        """Test POST /api/v1/form2441/calculate."""
        response = client.post(
            "/api/v1/form2441/calculate",
            json={
                "num_dependents": 2,
                "care_expenses": "6000",
                "agi": "50000",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "max_expenses" in data
        assert "applicable_percentage" in data
        assert "credit_amount" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form2441/overview."""
        response = client.get(
            "/api/v1/form2441/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 2441"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form2441/calculate",
            json={
                "num_dependents": 2,
                "care_expenses": "6000",
                "agi": "50000",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form2441/overview")
        assert response.status_code == 401
