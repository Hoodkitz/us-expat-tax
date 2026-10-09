"""
Tests for Form 2441 — Child and Dependent Care Expenses.
"""
from decimal import Decimal

import pytest

from app.modules.form2441 import (
    Form2441Input,
    QualifyingPerson,
    calculate_form2441,
    get_form2441_overview,
)


class TestCalculate:
    """Unit tests for Form 2441 calculation."""

    def test_basic_child_care_credit(self):
        """Test basic child and dependent care credit."""
        inp = Form2441Input(
            num_dependents=2,
            care_expenses=Decimal(6000),
            agi=Decimal(50000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal(6000)
        assert result.applicable_percentage > Decimal(0)
        assert result.credit_amount > Decimal(0)

    def test_high_agi_reduces_credit(self):
        """Test that high AGI reduces credit percentage."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(3000),
            agi=Decimal(100000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.applicable_percentage < Decimal("0.35")

    def test_low_income_max_credit(self):
        """Test that low income gets maximum credit percentage."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(3000),
            agi=Decimal(15000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.applicable_percentage == Decimal("0.35")

    def test_max_expenses_one_dependent(self):
        """Test max expenses for one dependent."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(10000),
            agi=Decimal(50000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal(3000)

    def test_max_expenses_two_dependents(self):
        """Test max expenses for two dependents."""
        inp = Form2441Input(
            num_dependents=2,
            care_expenses=Decimal(10000),
            agi=Decimal(50000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.max_expenses == Decimal(6000)

    def test_no_expenses(self):
        """Test with no care expenses."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(0),
            agi=Decimal(50000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.credit_amount == Decimal(0)

    def test_earned_income_limit(self):
        """Test that credit is limited by earned income."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(3000),
            agi=Decimal(50000),
            tax_year=2025,
            earned_income=Decimal(1000),
        )
        result = calculate_form2441(inp)
        assert result.earned_income_limit == Decimal(1000)
        assert result.credit_amount <= Decimal(1000)

    def test_qualifying_person_child_under_13(self):
        """Test qualifying person check for child under 13."""
        person = QualifyingPerson(
            name="Child",
            relationship="child",
            age=5,
            is_disabled=False,
            care_expenses=Decimal(3000),
        )
        assert person.is_qualifying() is True

    def test_qualifying_person_child_over_13_not_disabled(self):
        """Test that child over 13 is not qualifying unless disabled."""
        person = QualifyingPerson(
            name="Teen",
            relationship="child",
            age=15,
            is_disabled=False,
            care_expenses=Decimal(3000),
        )
        assert person.is_qualifying() is False

    def test_qualifying_person_disabled_spouse(self):
        """Test qualifying person check for disabled spouse."""
        person = QualifyingPerson(
            name="Spouse",
            relationship="spouse",
            age=45,
            is_disabled=True,
            care_expenses=Decimal(3000),
        )
        assert person.is_qualifying() is True

    def test_qualifying_person_disabled_dependent(self):
        """Test qualifying person check for disabled dependent."""
        person = QualifyingPerson(
            name="Parent",
            relationship="dependent",
            age=70,
            is_disabled=True,
            care_expenses=Decimal(3000),
        )
        assert person.is_qualifying() is True

    def test_qualifying_persons_list(self):
        """Test calculation with qualifying persons list."""
        persons = [
            QualifyingPerson("Child1", "child", 5, False, Decimal(3000)),
            QualifyingPerson("Child2", "child", 8, False, Decimal(3000)),
        ]
        inp = Form2441Input(
            num_dependents=2,
            care_expenses=Decimal(6000),
            agi=Decimal(50000),
            tax_year=2025,
            qualifying_persons=persons,
        )
        result = calculate_form2441(inp)
        assert result.num_qualifying_persons == 2
        assert result.max_expenses == Decimal(6000)

    def test_no_qualifying_persons(self):
        """Test with no qualifying persons."""
        inp = Form2441Input(
            num_dependents=0,
            care_expenses=Decimal(3000),
            agi=Decimal(50000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        assert result.is_eligible is False
        assert result.credit_amount == Decimal(0)

    def test_agi_phase_out_midpoint(self):
        """Test AGI phase-out at midpoint ($29,000)."""
        inp = Form2441Input(
            num_dependents=1,
            care_expenses=Decimal(3000),
            agi=Decimal(29000),
            tax_year=2025,
        )
        result = calculate_form2441(inp)
        # At $29k, percentage should be between 20% and 35%
        assert Decimal("0.20") < result.applicable_percentage < Decimal("0.35")


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

    def test_calculate_with_qualifying_persons(self, client, auth_headers):
        """Test calculate with qualifying persons list."""
        response = client.post(
            "/api/v1/form2441/calculate",
            json={
                "num_dependents": 1,
                "care_expenses": "3000",
                "agi": "50000",
                "tax_year": 2025,
                "qualifying_persons": [
                    {
                        "name": "Child",
                        "relationship": "child",
                        "age": 5,
                        "is_disabled": False,
                        "care_expenses": "3000",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["num_qualifying_persons"] == 1
        assert data["is_eligible"] is True

    def test_calculate_with_earned_income(self, client, auth_headers):
        """Test calculate with earned income limit."""
        response = client.post(
            "/api/v1/form2441/calculate",
            json={
                "num_dependents": 1,
                "care_expenses": "3000",
                "agi": "50000",
                "tax_year": 2025,
                "earned_income": "500",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["earned_income_limit"] == "500"
        assert float(data["credit_amount"]) <= 500.0
