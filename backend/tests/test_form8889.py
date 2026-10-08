"""
Tests for Form 8889 — Health Savings Accounts.
"""
import pytest
from decimal import Decimal
from app.modules.form8889 import (
    Form8889Input,
    Form8889Result,
    calculate_form8889,
    get_form8889_overview,
)


class TestCalculate:
    """Unit tests for Form 8889 calculation."""

    def test_basic_hsa_contribution(self):
        """Test basic HSA contribution."""
        inp = Form8889Input(
            coverage_type="self_only",
            employee_contributions=Decimal("3000"),
            employer_contributions=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8889(inp)
        assert result.contribution_limit == Decimal("4300")
        assert result.total_contributions == Decimal("3000")
        assert result.deduction == Decimal("3000")

    def test_hsa_distribution(self):
        """Test HSA distribution."""
        inp = Form8889Input(
            coverage_type="self_only",
            employee_contributions=Decimal("3000"),
            employer_contributions=Decimal("0"),
            distributions=Decimal("1000"),
            qualified_medical_expenses=Decimal("500"),
            tax_year=2025,
        )
        result = calculate_form8889(inp)
        assert result.taxable_distribution == Decimal("500")
        assert result.penalty == Decimal("100")

    def test_excess_contribution(self):
        """Test excess HSA contribution."""
        inp = Form8889Input(
            coverage_type="self_only",
            employee_contributions=Decimal("5000"),
            employer_contributions=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8889(inp)
        assert result.excess_contributions == Decimal("700")

    def test_no_contribution(self):
        """Test with no HSA contribution."""
        inp = Form8889Input(
            coverage_type="self_only",
            employee_contributions=Decimal("0"),
            employer_contributions=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8889(inp)
        assert result.total_contributions == Decimal("0")
        assert result.deduction == Decimal("0")

    def test_family_coverage(self):
        """Test family coverage HSA."""
        inp = Form8889Input(
            coverage_type="family",
            employee_contributions=Decimal("7000"),
            employer_contributions=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form8889(inp)
        assert result.contribution_limit == Decimal("8550")
        assert result.deduction == Decimal("7000")


class TestOverview:
    """Test Form 8889 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8889_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8889_overview()
        assert overview["form"] == "Form 8889"
        assert "8889" in overview["title"]


class TestRouter:
    """Integration tests for Form 8889 API endpoints."""

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
        """Test POST /api/v1/form8889/calculate."""
        response = client.post(
            "/api/v1/form8889/calculate",
            json={
                "coverage_type": "self_only",
                "employee_contributions": "3000",
                "employer_contributions": "0",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "contribution_limit" in data
        assert "total_contributions" in data
        assert "excess_contributions" in data
        assert "deduction" in data
        assert "taxable_distribution" in data
        assert "penalty" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8889/overview."""
        response = client.get(
            "/api/v1/form8889/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8889"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8889/calculate",
            json={
                "coverage_type": "self_only",
                "employee_contributions": "3000",
                "employer_contributions": "0",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8889/overview")
        assert response.status_code == 401
