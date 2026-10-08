"""
Tests for Form 5329 — Additional Taxes on Qualified Plans.
"""
import pytest
from decimal import Decimal
from app.modules.form5329 import (
    Form5329Input,
    Form5329Result,
    calculate_form5329,
    get_form5329_overview,
)


class TestCalculate:
    """Unit tests for Form 5329 calculation."""

    def test_early_distribution_penalty(self):
        """Test early distribution penalty calculation."""
        inp = Form5329Input(
            early_distribution=Decimal("10000"),
            excess_ira_contribution=Decimal("0"),
            excess_hsa_contribution=Decimal("0"),
            excess_rmd=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.early_distribution_penalty == Decimal("1000")
        assert result.total_penalty == Decimal("1000")

    def test_excess_ira_penalty(self):
        """Test excess IRA contribution penalty."""
        inp = Form5329Input(
            early_distribution=Decimal("0"),
            excess_ira_contribution=Decimal("1000"),
            excess_hsa_contribution=Decimal("0"),
            excess_rmd=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.excess_ira_penalty == Decimal("60")
        assert result.total_penalty == Decimal("60")

    def test_excess_hsa_penalty(self):
        """Test excess HSA contribution penalty."""
        inp = Form5329Input(
            early_distribution=Decimal("0"),
            excess_ira_contribution=Decimal("0"),
            excess_hsa_contribution=Decimal("1000"),
            excess_rmd=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.excess_hsa_penalty == Decimal("60")
        assert result.total_penalty == Decimal("60")

    def test_excess_rmd_penalty(self):
        """Test excess RMD penalty."""
        inp = Form5329Input(
            early_distribution=Decimal("0"),
            excess_ira_contribution=Decimal("0"),
            excess_hsa_contribution=Decimal("0"),
            excess_rmd=Decimal("10000"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.excess_rmd_penalty == Decimal("5000")
        assert result.total_penalty == Decimal("5000")

    def test_multiple_penalties(self):
        """Test multiple penalties combined."""
        inp = Form5329Input(
            early_distribution=Decimal("10000"),
            excess_ira_contribution=Decimal("1000"),
            excess_hsa_contribution=Decimal("0"),
            excess_rmd=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.early_distribution_penalty == Decimal("1000")
        assert result.excess_ira_penalty == Decimal("60")
        assert result.total_penalty == Decimal("1060")

    def test_no_penalties(self):
        """Test with no penalties."""
        inp = Form5329Input(
            early_distribution=Decimal("0"),
            excess_ira_contribution=Decimal("0"),
            excess_hsa_contribution=Decimal("0"),
            excess_rmd=Decimal("0"),
            tax_year=2025,
        )
        result = calculate_form5329(inp)
        assert result.total_penalty == Decimal("0")


class TestOverview:
    """Test Form 5329 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form5329_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form5329_overview()
        assert overview["form"] == "Form 5329"
        assert "5329" in overview["title"]


class TestRouter:
    """Integration tests for Form 5329 API endpoints."""

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
        """Test POST /api/v1/form5329/calculate."""
        response = client.post(
            "/api/v1/form5329/calculate",
            json={
                "early_distribution": "10000",
                "excess_ira_contribution": "0",
                "excess_hsa_contribution": "0",
                "excess_rmd": "0",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "early_distribution_penalty" in data
        assert "excess_ira_penalty" in data
        assert "excess_hsa_penalty" in data
        assert "excess_rmd_penalty" in data
        assert "total_penalty" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form5329/overview."""
        response = client.get(
            "/api/v1/form5329/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 5329"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form5329/calculate",
            json={
                "early_distribution": "10000",
                "excess_ira_contribution": "0",
                "excess_hsa_contribution": "0",
                "excess_rmd": "0",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form5329/overview")
        assert response.status_code == 401
