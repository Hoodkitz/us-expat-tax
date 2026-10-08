"""
Tests for Form 1040-X — Amended U.S. Individual Income Tax Return.
"""
import pytest
from decimal import Decimal
from app.modules.form1040x import (
    Form1040XInput,
    Form1040XResult,
    calculate_form1040x,
    get_form1040x_overview,
)


class TestCalculate:
    """Unit tests for Form 1040-X calculation."""

    def test_amended_return_with_additional_tax(self):
        """Test amended return showing additional tax due."""
        inp = Form1040XInput(
            original_tax=Decimal("10000"),
            corrected_tax=Decimal("12000"),
            original_payments=Decimal("10000"),
            corrected_payments=Decimal("10000"),
            explanation="Corrected income",
            tax_year=2025,
        )
        result = calculate_form1040x(inp)
        assert result.additional_tax_due == Decimal("2000")
        assert result.refund_due == Decimal("0")
        assert result.total_due == Decimal("2000")

    def test_amended_return_with_refund(self):
        """Test amended return showing refund due."""
        inp = Form1040XInput(
            original_tax=Decimal("10000"),
            corrected_tax=Decimal("8000"),
            original_payments=Decimal("10000"),
            corrected_payments=Decimal("10000"),
            explanation="Corrected deductions",
            tax_year=2025,
        )
        result = calculate_form1040x(inp)
        assert result.additional_tax_due == Decimal("0")
        assert result.refund_due == Decimal("2000")
        assert result.total_due == Decimal("0")

    def test_no_change(self):
        """Test amended return with no change."""
        inp = Form1040XInput(
            original_tax=Decimal("10000"),
            corrected_tax=Decimal("10000"),
            original_payments=Decimal("10000"),
            corrected_payments=Decimal("10000"),
            explanation="No change",
            tax_year=2025,
        )
        result = calculate_form1040x(inp)
        assert result.additional_tax_due == Decimal("0")
        assert result.refund_due == Decimal("0")
        assert result.total_due == Decimal("0")

    def test_penalty_calculation(self):
        """Test penalty calculation on additional tax."""
        inp = Form1040XInput(
            original_tax=Decimal("10000"),
            corrected_tax=Decimal("15000"),
            original_payments=Decimal("10000"),
            corrected_payments=Decimal("10000"),
            explanation="Late filing",
            tax_year=2025,
        )
        result = calculate_form1040x(inp)
        assert result.penalty > Decimal("0")
        assert result.interest > Decimal("0")

    def test_corrected_payments(self):
        """Test with corrected payments."""
        inp = Form1040XInput(
            original_tax=Decimal("10000"),
            corrected_tax=Decimal("10000"),
            original_payments=Decimal("8000"),
            corrected_payments=Decimal("10000"),
            explanation="Additional payments",
            tax_year=2025,
        )
        result = calculate_form1040x(inp)
        assert result.additional_tax_due == Decimal("0")
        assert result.refund_due == Decimal("0")


class TestOverview:
    """Test Form 1040-X overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form1040x_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form1040x_overview()
        assert overview["form"] == "Form 1040-X"
        assert "1040-X" in overview["title"]


class TestRouter:
    """Integration tests for Form 1040-X API endpoints."""

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
        """Test POST /api/v1/form1040x/calculate."""
        response = client.post(
            "/api/v1/form1040x/calculate",
            json={
                "original_tax": "10000",
                "corrected_tax": "12000",
                "original_payments": "10000",
                "corrected_payments": "10000",
                "explanation": "Corrected income",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "additional_tax_due" in data
        assert "refund_due" in data
        assert "penalty" in data
        assert "interest" in data
        assert "total_due" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form1040x/overview."""
        response = client.get(
            "/api/v1/form1040x/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 1040-X"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form1040x/calculate",
            json={
                "original_tax": "10000",
                "corrected_tax": "12000",
                "original_payments": "10000",
                "corrected_payments": "10000",
                "explanation": "Corrected income",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form1040x/overview")
        assert response.status_code == 401
