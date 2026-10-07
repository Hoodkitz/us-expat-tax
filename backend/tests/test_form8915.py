"""
Tests for Form 8915 — Qualified Disaster Retirement Plan Distributions.

Tests cover:
- Filing requirement eligibility (disaster types, timeframes, economic loss)
- Repayment schedule calculations
- Penalty waiver determination
- $100k distribution limit
- Non-qualified disasters
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.modules.form8915 import (
    FilingRequirementInput,
    RepaymentScheduleInput,
    PenaltyWaiverInput,
    check_filing_requirement,
    calculate_repayment_schedule,
    check_penalty_waiver,
    MAX_DISTRIBUTION_LIMIT,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: Get auth token
# ---------------------------------------------------------------------------

def _get_auth_token() -> str:
    """Register a test user and return JWT token."""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_form8915@example.com",
            "tenant_name": "Test Tenant",
            "password": "testpassword123",
        },
    )
    # Login
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test_form8915@example.com",
            "password": "testpassword123",
        },
    )
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------

class TestFilingRequirementModule:
    """Tests for filing requirement eligibility checks."""

    def test_hurricane_with_home_destroyed_eligible(self):
        """Hurricane disaster with home destroyed should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Hurricane Ian, Florida",
            distribution_date="2024-09-28",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Hurricane"
        assert result.distribution_within_window is True
        assert result.economic_loss_threshold_met is True

    def test_wildfire_with_economic_loss_eligible(self):
        """Wildfire disaster with sufficient economic loss should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="California Wildfire",
            distribution_date="2024-08-15",
            home_destroyed=False,
            economic_loss_amt=Decimal("50000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Wildfire"
        assert result.economic_loss_threshold_met is True

    def test_flood_eligible(self):
        """Flood disaster should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Louisiana Flood",
            distribution_date="2024-07-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Flood"

    def test_tornado_eligible(self):
        """Tornado disaster should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Oklahoma Tornado",
            distribution_date="2024-05-20",
            home_destroyed=False,
            economic_loss_amt=Decimal("25000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Tornado"

    def test_earthquake_eligible(self):
        """Earthquake disaster should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="California Earthquake",
            distribution_date="2024-06-10",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Earthquake"

    def test_pandemic_covid19_eligible(self):
        """Pandemic (COVID-19) should be eligible."""
        inp = FilingRequirementInput(
            disaster_area="COVID-19 Pandemic",
            distribution_date="2024-03-15",
            home_destroyed=False,
            economic_loss_amt=Decimal("10000"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is True
        assert result.disaster_type == "Pandemic (COVID-19)"

    def test_non_disaster_not_eligible(self):
        """Non-qualified disaster should NOT be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Random Storm",
            distribution_date="2024-01-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False

    def test_insufficient_economic_loss_not_eligible(self):
        """Insufficient economic loss without home destruction should NOT be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="2024-09-01",
            home_destroyed=False,
            economic_loss_amt=Decimal("500"),  # Below threshold
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False
        assert result.economic_loss_threshold_met is False

    def test_max_distribution_limit_verified(self):
        """Verify max distribution limit is $100,000."""
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="2024-09-01",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.max_distribution_limit == MAX_DISTRIBUTION_LIMIT
        assert result.max_distribution_limit == Decimal("100000")

    def test_invalid_distribution_date_not_eligible(self):
        """Invalid distribution date format should NOT be eligible."""
        inp = FilingRequirementInput(
            disaster_area="Hurricane",
            distribution_date="invalid-date",
            home_destroyed=True,
            economic_loss_amt=Decimal("0"),
        )
        result = check_filing_requirement(inp)
        assert result.eligible is False
        assert "Invalid distribution date" in result.explanation


class TestRepaymentScheduleModule:
    """Tests for repayment schedule calculations."""

    def test_standard_3year_repayment_schedule(self):
        """Standard 3-year repayment schedule should spread correctly."""
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("75000"),
            repayment_years=3,
        )
        result = calculate_repayment_schedule(inp)
        
        assert result.total_distribution == Decimal("75000")
        assert result.annual_repayment == Decimal("25000")
        assert result.tax_spread_per_year == Decimal("25000")
        assert len(result.repayment_schedule) == 3

    def test_2year_repayment_schedule(self):
        """2-year repayment schedule should work."""
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("60000"),
            repayment_years=2,
        )
        result = calculate_repayment_schedule(inp)
        
        assert result.annual_repayment == Decimal("30000")
        assert len(result.repayment_schedule) == 2

    def test_1year_repayment_schedule(self):
        """1-year repayment schedule should work."""
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("50000"),
            repayment_years=1,
        )
        result = calculate_repayment_schedule(inp)
        
        assert result.annual_repayment == Decimal("50000")
        assert len(result.repayment_schedule) == 1

    def test_tax_spread_always_3years(self):
        """Tax spread should always be over 3 years even with different repayment periods."""
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("90000"),
            repayment_years=1,
        )
        result = calculate_repayment_schedule(inp)
        
        # Tax spread is always 1/3 per year over 3 years
        assert result.tax_spread_per_year == Decimal("30000")

    def test_repayment_schedule_contains_years(self):
        """Repayment schedule should contain year information."""
        inp = RepaymentScheduleInput(
            distribution_amt=Decimal("60000"),
            repayment_years=3,
        )
        result = calculate_repayment_schedule(inp)
        
        for item in result.repayment_schedule:
            assert "year" in item
            assert "repayment_due" in item
            assert "tax_if_not_repaid" in item


class TestPenaltyWaiverModule:
    """Tests for penalty waiver determination."""

    def test_penalty_waiver_under_age_59(self):
        """Penalty waiver should apply for taxpayer under age 59½."""
        inp = PenaltyWaiverInput(
            age=45,
            distribution_amt=Decimal("50000"),
        )
        result = check_penalty_waiver(inp)
        
        assert result.waiver_eligible is True
        assert result.standard_penalty_rate == Decimal("0.10")
        assert result.waived_penalty_amount == Decimal("5000")

    def test_penalty_waiver_over_age_59(self):
        """Penalty waiver should apply regardless of age (even over 59½)."""
        inp = PenaltyWaiverInput(
            age=65,
            distribution_amt=Decimal("80000"),
        )
        result = check_penalty_waiver(inp)
        
        assert result.waiver_eligible is True
        assert result.waived_penalty_amount == Decimal("8000")

    def test_penalty_calculation_correct(self):
        """Penalty calculation should be 10% of distribution amount."""
        inp = PenaltyWaiverInput(
            age=40,
            distribution_amt=Decimal("100000"),
        )
        result = check_penalty_waiver(inp)
        
        assert result.waived_penalty_amount == Decimal("10000")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestFilingRequirementEndpoint:
    """Tests for /api/v1/form8915/filing-requirement endpoint."""

    def test_filing_requirement_endpoint_eligible(self):
        """Test filing requirement endpoint with eligible disaster."""
        token = _get_auth_token()
        
        resp = client.post(
            "/api/v1/form8915/filing-requirement",
            json={
                "disaster_area": "Hurricane Ian, Florida",
                "distribution_date": "2024-09-28",
                "home_destroyed": True,
                "economic_loss_amt": "0",
            },
            headers=_auth_headers(token),
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert data["disaster_type"] == "Hurricane"

    def test_filing_requirement_endpoint_not_eligible(self):
        """Test filing requirement endpoint with non-eligible disaster."""
        token = _get_auth_token()
        
        resp = client.post(
            "/api/v1/form8915/filing-requirement",
            json={
                "disaster_area": "Random Event",
                "distribution_date": "2024-01-01",
                "home_destroyed": False,
                "economic_loss_amt": "100",
            },
            headers=_auth_headers(token),
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False


class TestRepaymentScheduleEndpoint:
    """Tests for /api/v1/form8915/repayment-schedule endpoint."""

    def test_repayment_schedule_endpoint(self):
        """Test repayment schedule endpoint."""
        token = _get_auth_token()
        
        resp = client.post(
            "/api/v1/form8915/repayment-schedule",
            json={
                "distribution_amt": "75000.00",
                "repayment_years": 3,
            },
            headers=_auth_headers(token),
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_distribution"] == "75000.00"
        assert data["annual_repayment"] == "25000.00"
        assert len(data["repayment_schedule"]) == 3


class TestPenaltyWaiverEndpoint:
    """Tests for /api/v1/form8915/penalty-waiver endpoint."""

    def test_penalty_waiver_endpoint(self):
        """Test penalty waiver endpoint."""
        token = _get_auth_token()
        
        resp = client.post(
            "/api/v1/form8915/penalty-waiver",
            json={
                "age": 45,
                "distribution_amt": "60000.00",
            },
            headers=_auth_headers(token),
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["waiver_eligible"] is True
        assert data["waived_penalty_amount"] == "6000.00"


class TestOverviewEndpoint:
    """Tests for /api/v1/form8915/overview endpoint."""

    def test_overview_endpoint_no_auth_required(self):
        """Test overview endpoint (no authentication required)."""
        resp = client.get("/api/v1/form8915/overview")
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["form"] == "Form 8915"
        assert "qualified_disaster_types" in data
        assert data["max_distribution_limit"] == "100000"
        assert data["repayment_period_years"] == 3
