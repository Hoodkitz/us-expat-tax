"""
Tests for Form 8917 — Tuition and Fees Deduction.
"""
import pytest
from decimal import Decimal
from app.modules.form8917 import (
    Form8917Input,
    Form8917Result,
    calculate_form8917,
    get_form8917_overview,
)


class TestCalculate:
    """Unit tests for Form 8917 calculation."""

    def test_basic_tuition_deduction(self):
        """Test basic tuition and fees deduction."""
        inp = Form8917Input(
            qualified_expenses=Decimal("4000"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8917(inp)
        assert result.deduction == Decimal("4000")

    def test_maximum_deduction(self):
        """Test maximum tuition deduction."""
        inp = Form8917Input(
            qualified_expenses=Decimal("10000"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8917(inp)
        assert result.deduction == Decimal("4000")

    def test_high_agi_no_deduction(self):
        """Test high AGI results in no deduction."""
        inp = Form8917Input(
            qualified_expenses=Decimal("4000"),
            agi=Decimal("90000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8917(inp)
        assert result.deduction == Decimal("0")

    def test_no_qualified_expenses(self):
        """Test with no qualified expenses."""
        inp = Form8917Input(
            qualified_expenses=Decimal("0"),
            agi=Decimal("50000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8917(inp)
        assert result.deduction == Decimal("0")

    def test_married_filing_jointly(self):
        """Test tuition deduction for married filing jointly."""
        inp = Form8917Input(
            qualified_expenses=Decimal("4000"),
            agi=Decimal("100000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8917(inp)
        assert result.deduction == Decimal("4000")


class TestOverview:
    """Test Form 8917 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8917_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8917_overview()
        assert overview["form"] == "Form 8917"
        assert "8917" in overview["title"]


class TestRouter:
    """Integration tests for Form 8917 API endpoints."""

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
        """Test POST /api/v1/form8917/calculate."""
        response = client.post(
            "/api/v1/form8917/calculate",
            json={
                "qualified_expenses": "4000",
                "agi": "50000",
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "deduction" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8917/overview."""
        response = client.get(
            "/api/v1/form8917/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8917"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8917/calculate",
            json={
                "qualified_expenses": "4000",
                "agi": "50000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8917/overview")
        assert response.status_code == 401
