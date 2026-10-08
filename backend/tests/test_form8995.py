"""
Tests for Form 8995 — Qualified Business Income Deduction.
"""
import pytest
from decimal import Decimal
from app.modules.form8995 import (
    Form8995Input,
    Form8995Result,
    calculate_form8995,
    get_form8995_overview,
    QBI_RATE,
    THRESHOLDS,
    THRESHOLD_RANGE,
)


class TestCalculate:
    """Unit tests for Form 8995 calculation."""

    def test_basic_single_filer(self):
        """Test basic single filer with 20% QBI deduction, no phaseout."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("100000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.phaseout_applied is False
        assert result.wage_limit_applied is False

    def test_married_joint(self):
        """Test married filing jointly — higher threshold, no phaseout."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("100000"),
            filing_status="married_joint",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.phaseout_applied is False

    def test_no_phaseout_below_threshold(self):
        """Test AGI just below threshold — no phaseout."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("197299"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.phaseout_applied is False

    def test_phaseout_partial(self):
        """Test AGI in phase-out range — partial phaseout with no wages."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("220000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # phaseout_ratio = (220000 - 197300) / 50000 = 0.454
        # wage_limit = 0, limited_deduction = 0
        # qbi_deduction = 20000 * (1 - 0.454) = 20000 * 0.546 = 10920
        assert result.qbi_deduction == Decimal("10920.00")
        assert result.phaseout_applied is True
        assert result.wage_limit_applied is True

    def test_phaseout_full(self):
        """Test AGI above threshold + range — full phaseout."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("250000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # AGI > 197300 + 50000 = 247300, phaseout_ratio = 1
        # wage_limit = 0, qbi_deduction = 0
        assert result.qbi_deduction == Decimal("0.00")
        assert result.phaseout_applied is True

    def test_specified_service_business_fully_phased_out(self):
        """Test SSTB with AGI above threshold + range — deduction = 0."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("250000"),
            filing_status="single",
            specified_service_business=True,
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("0.00")
        assert result.phaseout_applied is True

    def test_specified_service_business_partial_phaseout(self):
        """Test SSTB in phase-out range — partial deduction."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("220000"),
            filing_status="single",
            specified_service_business=True,
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # Same as partial phaseout: 20000 * 0.546 = 10920
        assert result.qbi_deduction == Decimal("10920.00")
        assert result.phaseout_applied is True

    def test_wage_limit_50_percent_w2(self):
        """Test wage limit using 50% of W-2 wages."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("220000"),
            filing_status="single",
            w2_wages=Decimal("50000"),
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # wage_limit = max(50000*0.5, 50000*0.25 + 0) = max(25000, 12500) = 25000
        # limited_deduction = min(20000, 25000) = 20000
        # qbi_deduction = 20000 * 0.546 + 20000 * 0.454 = 20000
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.wage_limit_applied is True

    def test_wage_limit_25_percent_w2_plus_ubia(self):
        """Test wage limit using 25% W-2 + 2.5% UBIA."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("220000"),
            filing_status="single",
            w2_wages=Decimal("10000"),
            ubia=Decimal("1000000"),
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # wage_limit = max(10000*0.5, 10000*0.25 + 1000000*0.025) = max(5000, 27500) = 27500
        # limited_deduction = min(20000, 27500) = 20000
        # qbi_deduction = 20000
        assert result.qbi_deduction == Decimal("20000.00")

    def test_wage_limit_reduces_deduction(self):
        """Test wage limit actually reduces deduction."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("220000"),
            filing_status="single",
            w2_wages=Decimal("20000"),
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        # wage_limit = max(20000*0.5, 20000*0.25) = max(10000, 5000) = 10000
        # limited_deduction = min(20000, 10000) = 10000
        # qbi_deduction = 20000 * 0.546 + 10000 * 0.454 = 10920 + 4540 = 15460
        assert result.qbi_deduction == Decimal("15460.00")

    def test_zero_qbi(self):
        """Test with zero QBI."""
        inp = Form8995Input(
            qualified_business_income=Decimal("0"),
            agi=Decimal("100000"),
            filing_status="single",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("0.00")

    def test_head_of_household_threshold(self):
        """Test head of household uses single threshold."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("197299"),
            filing_status="head_of_household",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.phaseout_applied is False

    def test_married_separate_threshold(self):
        """Test married filing separately uses single threshold."""
        inp = Form8995Input(
            qualified_business_income=Decimal("100000"),
            agi=Decimal("197299"),
            filing_status="married_separate",
            tax_year=2025,
        )
        result = calculate_form8995(inp)
        assert result.qbi_deduction == Decimal("20000.00")
        assert result.phaseout_applied is False


class TestOverview:
    """Test Form 8995 overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_form8995_overview()
        assert "form" in overview
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_form8995_overview()
        assert overview["form"] == "Form 8995"
        assert "Qualified Business Income" in overview["title"]


class TestRouter:
    """Integration tests for Form 8995 API endpoints."""

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
        """Test POST /api/v1/form8995/calculate."""
        response = client.post(
            "/api/v1/form8995/calculate",
            json={
                "qualified_business_income": "100000",
                "agi": "100000",
                "filing_status": "single",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "qbi_deduction" in data
        assert "phaseout_applied" in data
        assert "wage_limit_applied" in data
        assert "explanation" in data

    def test_overview_endpoint(self, client, auth_headers):
        """Test GET /api/v1/form8995/overview."""
        response = client.get(
            "/api/v1/form8995/overview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["form"] == "Form 8995"

    def test_calculate_requires_auth(self, client):
        """Test that calculate requires authentication."""
        response = client.post(
            "/api/v1/form8995/calculate",
            json={
                "qualified_business_income": "100000",
                "agi": "100000",
                "filing_status": "single",
                "tax_year": 2025,
            },
        )
        assert response.status_code == 401

    def test_overview_requires_auth(self, client):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/form8995/overview")
        assert response.status_code == 401

    def test_calculate_with_wage_limit(self, client, auth_headers):
        """Test calculate endpoint with wage limit scenario."""
        response = client.post(
            "/api/v1/form8995/calculate",
            json={
                "qualified_business_income": "100000",
                "agi": "220000",
                "filing_status": "single",
                "w2_wages": "20000",
                "ubia": "0",
                "tax_year": 2025,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phaseout_applied"] is True
        assert data["wage_limit_applied"] is True
