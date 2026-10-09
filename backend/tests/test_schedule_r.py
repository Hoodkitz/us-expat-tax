"""
Tests for Schedule R — Credit for the Elderly or the Disabled.

Tests cover:
- Eligibility (age 65+ or disabled)
- Base amount determination by filing status
- Nontaxable income reduction
- AGI threshold reduction (50% of excess)
- Final credit calculation (15% rate)
- Edge cases (zero credit, high AGI, married filing separately)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.schedule_r import (
    ScheduleRInput,
    calculate_schedule_r,
    get_schedule_r_overview,
    BASE_AMOUNT_SINGLE,
    BASE_AMOUNT_MARRIED_BOTH_65,
    BASE_AMOUNT_MARRIED_ONE_65,
    BASE_AMOUNT_MARRIED_SEPARATE,
    AGI_THRESHOLD_SINGLE,
    AGI_THRESHOLD_MARRIED_JOINTLY,
    AGI_THRESHOLD_MARRIED_SEPARATELY,
    CREDIT_RATE,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: Get auth token
# ---------------------------------------------------------------------------

def _get_auth_token() -> str:
    """Register a test user and return JWT token."""
    client.post(
        "/auth/register",
        json={
            "email": "test_schedule_r@example.com",
            "tenant_name": "Test Tenant",
            "password": "testpassword123",
        },
    )
    resp = client.post(
        "/auth/login",
        json={
            "email": "test_schedule_r@example.com",
            "password": "testpassword123",
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------

class TestEligibility:
    """Tests for Schedule R eligibility."""

    def test_age_65_eligible(self):
        """Taxpayer age 65 should be eligible."""
        inp = ScheduleRInput(
            filing_status="single",
            age=65,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is True

    def test_age_64_not_eligible(self):
        """Taxpayer age 64 should NOT be eligible."""
        inp = ScheduleRInput(
            filing_status="single",
            age=64,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is False

    def test_disabled_eligible(self):
        """Permanently disabled taxpayer should be eligible."""
        inp = ScheduleRInput(
            filing_status="single",
            age=50,
            is_disabled=True,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is True

    def test_married_jointly_one_65_eligible(self):
        """Married filing jointly with one spouse 65+ should be eligible."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=60,
            spouse_age=67,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is True

    def test_married_jointly_both_under_65_not_eligible(self):
        """Married filing jointly with both under 65 and not disabled should NOT be eligible."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=60,
            spouse_age=62,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is False

    def test_married_jointly_spouse_disabled_eligible(self):
        """Married filing jointly with disabled spouse should be eligible."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=60,
            spouse_age=62,
            spouse_is_disabled=True,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.eligible is True


class TestBaseAmount:
    """Tests for base amount determination."""

    def test_single_base_amount(self):
        """Single filer base amount should be $5,000."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.base_amount == BASE_AMOUNT_SINGLE

    def test_married_jointly_both_65_base_amount(self):
        """MFJ with both 65+ base amount should be $7,500."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=67,
            spouse_age=68,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.base_amount == BASE_AMOUNT_MARRIED_BOTH_65

    def test_married_jointly_one_65_base_amount(self):
        """MFJ with only one 65+ base amount should be $5,000."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=67,
            spouse_age=62,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.base_amount == BASE_AMOUNT_MARRIED_ONE_65

    def test_married_filing_separately_base_amount(self):
        """MFS base amount should be $3,750."""
        inp = ScheduleRInput(
            filing_status="married_filing_separately",
            age=67,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.base_amount == BASE_AMOUNT_MARRIED_SEPARATE

    def test_head_of_household_base_amount(self):
        """Head of household base amount should be $5,000."""
        inp = ScheduleRInput(
            filing_status="head_of_household",
            age=67,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.base_amount == BASE_AMOUNT_SINGLE


class TestNontaxableIncomeReduction:
    """Tests for nontaxable income reduction."""

    def test_nontaxable_ss_reduces_base(self):
        """Nontaxable Social Security should reduce the base amount."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
            nontaxable_social_security=2000,
        )
        result = calculate_schedule_r(inp)
        assert result.total_nontaxable_income == 2000.0
        assert result.credit_before_rate == 3000.0  # 5000 - 2000

    def test_nontaxable_pension_reduces_base(self):
        """Nontaxable pension should reduce the base amount."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
            nontaxable_pension=1500,
        )
        result = calculate_schedule_r(inp)
        assert result.total_nontaxable_income == 1500.0
        assert result.credit_before_rate == 3500.0  # 5000 - 1500

    def test_combined_nontaxable_income(self):
        """Combined nontaxable income should reduce base amount."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
            nontaxable_social_security=1000,
            nontaxable_pension=500,
            nontaxable_other=200,
        )
        result = calculate_schedule_r(inp)
        assert result.total_nontaxable_income == 1700.0
        assert result.credit_before_rate == 3300.0  # 5000 - 1700

    def test_nontaxable_income_exceeds_base(self):
        """Nontaxable income exceeding base should result in zero credit."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
            nontaxable_social_security=6000,
        )
        result = calculate_schedule_r(inp)
        assert result.credit_before_rate == 0.0
        assert result.credit_amount == 0.0


class TestAGIReduction:
    """Tests for AGI threshold reduction."""

    def test_agi_below_threshold_no_reduction(self):
        """AGI below threshold should not trigger reduction."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=5000,
        )
        result = calculate_schedule_r(inp)
        assert result.excess_agi == 0.0
        assert result.agi_reduction == 0.0

    def test_agi_above_threshold_reduction(self):
        """AGI above threshold should trigger 50% reduction."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=10000,
        )
        result = calculate_schedule_r(inp)
        assert result.excess_agi == 2500.0  # 10000 - 7500
        assert result.agi_reduction == 1250.0  # 2500 * 0.5

    def test_married_jointly_agi_threshold(self):
        """MFJ AGI threshold should be $10,000."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=67,
            spouse_age=68,
            agi=12000,
        )
        result = calculate_schedule_r(inp)
        assert result.agi_threshold == AGI_THRESHOLD_MARRIED_JOINTLY
        assert result.excess_agi == 2000.0  # 12000 - 10000
        assert result.agi_reduction == 1000.0  # 2000 * 0.5

    def test_married_filing_separately_agi_threshold(self):
        """MFS AGI threshold should be $5,000."""
        inp = ScheduleRInput(
            filing_status="married_filing_separately",
            age=67,
            agi=6000,
        )
        result = calculate_schedule_r(inp)
        assert result.agi_threshold == AGI_THRESHOLD_MARRIED_SEPARATELY
        assert result.excess_agi == 1000.0  # 6000 - 5000
        assert result.agi_reduction == 500.0  # 1000 * 0.5


class TestCreditCalculation:
    """Tests for final credit calculation."""

    def test_maximum_credit_single(self):
        """Maximum credit for single filer should be $750 (15% of $5,000)."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.credit_amount == 750.0  # 5000 * 0.15

    def test_maximum_credit_married_jointly_both_65(self):
        """Maximum credit for MFJ both 65+ should be $1,125 (15% of $7,500)."""
        inp = ScheduleRInput(
            filing_status="married_filing_jointly",
            age=67,
            spouse_age=68,
            agi=0,
        )
        result = calculate_schedule_r(inp)
        assert result.credit_amount == 1125.0  # 7500 * 0.15

    def test_credit_with_reductions(self):
        """Credit should be reduced by nontaxable income and AGI."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=10000,
            nontaxable_social_security=1000,
        )
        result = calculate_schedule_r(inp)
        # Base: 5000, nontaxable: 1000, AGI reduction: 1250
        # Credit before rate: 5000 - 1000 - 1250 = 2750
        # Credit: 2750 * 0.15 = 412.50
        assert result.credit_before_rate == 2750.0
        assert result.credit_amount == 412.50

    def test_zero_credit_high_agi(self):
        """High AGI should result in zero credit."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=50000,
        )
        result = calculate_schedule_r(inp)
        assert result.credit_amount == 0.0

    def test_zero_credit_high_nontaxable(self):
        """High nontaxable income should result in zero credit."""
        inp = ScheduleRInput(
            filing_status="single",
            age=67,
            agi=0,
            nontaxable_social_security=10000,
        )
        result = calculate_schedule_r(inp)
        assert result.credit_amount == 0.0


class TestOverview:
    """Test Schedule R overview."""

    def test_overview_structure(self):
        """Test that overview has required fields."""
        overview = get_schedule_r_overview()
        assert "title" in overview
        assert "statutory_authority" in overview
        assert "eligibility" in overview
        assert "base_amounts" in overview
        assert "agi_thresholds" in overview
        assert "calculation_steps" in overview
        assert "notes" in overview

    def test_overview_content(self):
        """Test overview content."""
        overview = get_schedule_r_overview()
        assert "Schedule R" in overview["title"]
        assert "Credit for the Elderly" in overview["title"]


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestCalculateEndpoint:
    """Tests for /api/v1/schedule-r/calculate endpoint."""

    def test_calculate_endpoint_eligible(self):
        """Test calculate endpoint with eligible taxpayer."""
        token = _get_auth_token()
        resp = client.post(
            "/api/v1/schedule-r/calculate",
            json={
                "filing_status": "single",
                "age": 67,
                "agi": 0,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert data["credit_amount"] == 750.0

    def test_calculate_endpoint_not_eligible(self):
        """Test calculate endpoint with ineligible taxpayer."""
        token = _get_auth_token()
        resp = client.post(
            "/api/v1/schedule-r/calculate",
            json={
                "filing_status": "single",
                "age": 50,
                "agi": 0,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False
        assert data["credit_amount"] == 0.0

    def test_calculate_endpoint_married_jointly(self):
        """Test calculate endpoint with married filing jointly."""
        token = _get_auth_token()
        resp = client.post(
            "/api/v1/schedule-r/calculate",
            json={
                "filing_status": "married_filing_jointly",
                "age": 67,
                "spouse_age": 68,
                "agi": 0,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert data["base_amount"] == 7500.0
        assert data["credit_amount"] == 1125.0

    def test_calculate_endpoint_with_nontaxable_income(self):
        """Test calculate endpoint with nontaxable income."""
        token = _get_auth_token()
        resp = client.post(
            "/api/v1/schedule-r/calculate",
            json={
                "filing_status": "single",
                "age": 67,
                "agi": 10000,
                "nontaxable_social_security": 1000,
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert data["total_nontaxable_income"] == 1000.0
        assert data["credit_amount"] == 412.50

    def test_calculate_endpoint_requires_auth(self):
        """Test that calculate endpoint requires authentication."""
        resp = client.post(
            "/api/v1/schedule-r/calculate",
            json={
                "filing_status": "single",
                "age": 67,
                "agi": 0,
            },
        )
        assert resp.status_code == 401


class TestOverviewEndpoint:
    """Tests for /api/v1/schedule-r/overview endpoint."""

    def test_overview_endpoint(self):
        """Test overview endpoint."""
        token = _get_auth_token()
        resp = client.get(
            "/api/v1/schedule-r/overview",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "Schedule R" in data["title"]
        assert "statutory_authority" in data

    def test_overview_endpoint_requires_auth(self):
        """Test that overview endpoint requires authentication."""
        resp = client.get("/api/v1/schedule-r/overview")
        assert resp.status_code == 401
