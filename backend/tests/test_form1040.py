"""
Tests for Form 1040 — U.S. Individual Income Tax Return.
"""
import pytest
from decimal import Decimal
from app.modules.form1040 import (
    Form1040Input,
    Form1040Result,
    calculate_form1040,
    get_form1040_overview,
)


class TestCalculate:
    """Unit tests for Form 1040 calculation (2025 rules)."""

    def test_basic_single_filer(self):
        inp = Form1040Input(filing_status="single", gross_income=Decimal("51000"))
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("35250.00")
        # 10% of 11,925 + 12% of (35,250 - 11,925)
        assert result.tax_before_credits == Decimal("3991.50")
        assert result.marginal_tax_rate == Decimal("0.12")

    def test_married_joint(self):
        inp = Form1040Input(filing_status="married_joint", gross_income=Decimal("102000"))
        result = calculate_form1040(inp)
        assert result.taxable_income == Decimal("70500.00")

    def test_head_of_household(self):
        inp = Form1040Input(filing_status="head_of_household", gross_income=Decimal("60500"))
        assert calculate_form1040(inp).taxable_income == Decimal("36875.00")

    def test_no_income(self):
        result = calculate_form1040(Form1040Input(filing_status="single", gross_income=Decimal("0")))
        assert result.total_tax == Decimal("0.00")
        assert result.effective_tax_rate == Decimal("0")

    def test_high_income_top_bracket(self):
        result = calculate_form1040(Form1040Input(filing_status="single", gross_income=Decimal("1000000")))
        assert result.marginal_tax_rate == Decimal("0.37")

    def test_itemized_deductions_used_when_larger(self):
        inp = Form1040Input(filing_status="single", gross_income=Decimal("100000"), deductions=Decimal("30000"))
        assert calculate_form1040(inp).taxable_income == Decimal("70000.00")

    def test_adjustments_reduce_agi(self):
        inp = Form1040Input(filing_status="single", gross_income=Decimal("100000"), adjustments=Decimal("5000"))
        assert calculate_form1040(inp).agi == Decimal("95000.00")

    def test_credits_cannot_make_tax_negative(self):
        inp = Form1040Input(filing_status="single", gross_income=Decimal("20000"), credits=Decimal("99999"))
        assert calculate_form1040(inp).total_tax == Decimal("0.00")

    def test_refund_and_balance_due(self):
        low = calculate_form1040(Form1040Input(filing_status="single", gross_income=Decimal("51000"), withholding=Decimal("10000")))
        assert low.refund == Decimal("6008.50") and low.balance_due == Decimal("0.00")
        high = calculate_form1040(Form1040Input(filing_status="single", gross_income=Decimal("51000")))
        assert high.balance_due == Decimal("3991.50") and high.refund == Decimal("0.00")

    def test_married_separate(self):
        inp = Form1040Input(filing_status="married_separate", gross_income=Decimal("15750"))
        assert calculate_form1040(inp).taxable_income == Decimal("0.00")


class TestOverview:
    """Test Form 1040 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form1040_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form1040_overview()
        assert overview["form"] == "Form 1040"
        assert "1040" in overview["form"]


class TestRouter:
    """Integration tests for Form 1040 API endpoints."""

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
        """Test POST /api/v1/form1040/calculate."""
        response = client.post(
            "/api/v1/form1040/calculate",
            json={
                "gross_income": "51000",
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "taxable_income" in data
        assert "total_tax" in data
        assert "effective_tax_rate" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form1040/overview."""
        response = client.get(
            "/api/v1/form1040/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 1040"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form1040/calculate",
            json={
                "gross_income": "51000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form1040/overview")
        assert response.status_code == 401
