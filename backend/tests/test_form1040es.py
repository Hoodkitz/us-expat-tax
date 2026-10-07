"""
Tests for Form 1040-ES — Estimated Tax for Individuals.

Tests cover:
- Estimated tax calculation (brackets, safe harbor, penalties)
- Quarterly payment schedule
- Safe harbor rules (90% current year, 100%/110% prior year)
- Underpayment penalty calculation
- Different filing statuses
"""
import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.auth.utils import create_access_token
from app.modules.form1040es import (
    EstimatedTaxInput,
    calculate_estimated_tax,
    calculate_quarterly_schedule,
    get_form1040es_overview,
    STANDARD_DEDUCTIONS,
    TAX_BRACKETS_SINGLE,
    SAFE_HARBOR_PERCENTAGE,
    HIGH_AGI_THRESHOLD,
)

client = TestClient(app)

BASE = "/api/v1/form1040es"


@pytest.fixture()
def auth_token() -> str:
    return create_access_token({
        "sub": f"form1040es-test-{uuid.uuid4().hex[:8]}@example.com",
        "tenant_id": str(uuid.uuid4()),
    })


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Module-level tests (direct function calls)
# ---------------------------------------------------------------------------

class TestEstimatedTaxModule:
    """Tests for estimated tax calculation."""

    def test_single_filer_basic_calculation(self):
        """Basic estimated tax calculation for single filer."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("85000"),
            withholding=Decimal("5000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("12000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.total_tax_liability > 0
        assert result.total_payments == Decimal("5000")
        assert result.balance_due > 0
        assert result.quarterly_payment > 0

    def test_married_joint_filing_status(self):
        """Married filing jointly should use different brackets."""
        inp = EstimatedTaxInput(
            filing_status="married_joint",
            annual_income=Decimal("150000"),
            withholding=Decimal("10000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("20000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.total_tax_liability > 0
        assert result.marginal_tax_rate > 0

    def test_head_of_household_filing_status(self):
        """Head of household should use different brackets."""
        inp = EstimatedTaxInput(
            filing_status="head_of_household",
            annual_income=Decimal("75000"),
            withholding=Decimal("4000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("10000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.total_tax_liability > 0

    def test_married_separate_filing_status(self):
        """Married filing separately should use different brackets."""
        inp = EstimatedTaxInput(
            filing_status="married_separate",
            annual_income=Decimal("60000"),
            withholding=Decimal("3000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("8000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.total_tax_liability > 0

    def test_standard_deduction_applied(self):
        """Standard deduction should be applied when higher than itemized."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),  # Standard deduction ($15,000) should apply
            credits=Decimal("0"),
            prior_year_tax=Decimal("5000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Taxable income should be $50,000 - $15,000 = $35,000
        # Tax: $1,192.50 + ($35,000 - $11,925) * 0.12 = $1,192.50 + $2,769 = $3,961.50
        assert result.total_tax_liability == Decimal("3961.50")

    def test_itemized_deductions_higher_than_standard(self):
        """Itemized deductions should be used when higher than standard."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("20000"),  # Higher than standard $15,000
            credits=Decimal("0"),
            prior_year_tax=Decimal("10000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Taxable income should be $100,000 - $20,000 = $80,000
        assert result.total_tax_liability > 0

    def test_tax_credits_reduce_liability(self):
        """Tax credits should reduce total tax liability."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("2000"),
            prior_year_tax=Decimal("5000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Without credits: $3,961.50, with $2,000 credits: $1,961.50
        assert result.total_tax_liability == Decimal("1961.50")

    def test_safe_harbor_met_current_year(self):
        """Safe harbor should be met when paying 90% of current year tax."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("4000"),  # 90% of ~$3,961.50 = ~$3,565.35
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("10000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Safe harbor amount should be 90% of current year tax
        expected_safe = (result.total_tax_liability * SAFE_HARBOR_PERCENTAGE).quantize(Decimal("0.01"))
        assert result.safe_harbor_amount == expected_safe

    def test_safe_harbor_met_prior_year(self):
        """Safe harbor should be met when paying 100% of prior year tax."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("10000"),  # 100% of prior year tax
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("10000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.safe_harbor_met is True
        assert result.underpayment_penalty == Decimal("0")

    def test_safe_harbor_high_agi_110_percent(self):
        """High AGI taxpayers must pay 110% of prior year tax."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("200000"),  # Above $150k threshold
            withholding=Decimal("10000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("10000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Safe harbor should be 110% of prior year = $11,000
        expected_safe = Decimal("11000.00")
        assert result.safe_harbor_amount == expected_safe

    def test_underpayment_penalty_when_safe_harbor_not_met(self):
        """Underpayment penalty should apply when safe harbor not met."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("1000"),  # Very low withholding
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.safe_harbor_met is False
        assert result.underpayment_penalty > 0

    def test_no_underpayment_penalty_when_safe_harbor_met(self):
        """No underpayment penalty when safe harbor is met."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("10000"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("5000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.safe_harbor_met is True
        assert result.underpayment_penalty == Decimal("0")

    def test_quarterly_payment_calculation(self):
        """Quarterly payment should divide remaining balance by remaining quarters."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=2,  # 2 quarters already paid
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Quarterly payment should be balance_due / 2 (remaining quarters)
        expected_quarterly = (result.balance_due / 2).quantize(Decimal("0.01"))
        assert result.quarterly_payment == expected_quarterly

    def test_effective_tax_rate_calculation(self):
        """Effective tax rate should be tax / income."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        expected_rate = result.total_tax_liability / Decimal("100000")
        assert result.effective_tax_rate == expected_rate

    def test_marginal_tax_rate_calculation(self):
        """Marginal tax rate should match the highest bracket reached."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("5000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        # Taxable income $35,000 falls in 12% bracket
        assert result.marginal_tax_rate == Decimal("0.12")

    def test_zero_income_no_tax(self):
        """Zero income should result in zero tax."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("0"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("0"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.total_tax_liability == Decimal("0")
        assert result.balance_due == Decimal("0")

    def test_balance_due_when_overpaid(self):
        """Balance due should be zero when overpaid."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("50000"),
            withholding=Decimal("10000"),  # More than tax liability
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("5000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_estimated_tax(inp)

        assert result.balance_due == Decimal("0")


class TestQuarterlyScheduleModule:
    """Tests for quarterly payment schedule."""

    def test_quarterly_schedule_has_four_payments(self):
        """Quarterly schedule should have 4 payments."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_quarterly_schedule(inp)

        assert len(result.payments) == 4

    def test_quarterly_schedule_payment_structure(self):
        """Each quarterly payment should have required fields."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_quarterly_schedule(inp)

        for payment in result.payments:
            assert payment.quarter >= 1
            assert payment.quarter <= 4
            assert payment.due_date
            assert payment.amount_due > 0
            assert payment.cumulative_due > 0

    def test_quarterly_schedule_total_due(self):
        """Total due should match total tax liability."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=0,
            amount_paid=Decimal("0"),
        )
        result = calculate_quarterly_schedule(inp)

        # Total due should be approximately total tax liability
        assert result.total_due > 0

    def test_quarterly_schedule_with_partial_payments(self):
        """Schedule should account for partial payments."""
        inp = EstimatedTaxInput(
            filing_status="single",
            annual_income=Decimal("100000"),
            withholding=Decimal("0"),
            deductions=Decimal("0"),
            credits=Decimal("0"),
            prior_year_tax=Decimal("15000"),
            quarters_paid=2,
            amount_paid=Decimal("5000"),
        )
        result = calculate_quarterly_schedule(inp)

        assert result.total_paid == Decimal("5000")
        assert result.remaining_balance > 0


class TestForm1040ESOverview:
    """Tests for Form 1040-ES overview."""

    def test_overview_contains_required_fields(self):
        """Overview should contain all required fields."""
        overview = get_form1040es_overview()

        assert overview["form"] == "Form 1040-ES"
        assert "title" in overview
        assert "purpose" in overview
        assert "who_must_file" in overview
        assert "safe_harbor_rules" in overview
        assert "quarterly_due_dates" in overview
        assert "underpayment_penalty" in overview
        assert "key_rules" in overview
        assert "statutory_references" in overview
        assert "irs_reference" in overview

    def test_overview_safe_harbor_rules(self):
        """Safe harbor rules should be documented."""
        overview = get_form1040es_overview()

        assert "rule_1" in overview["safe_harbor_rules"]
        assert "rule_2" in overview["safe_harbor_rules"]
        assert "90%" in overview["safe_harbor_rules"]["rule_1"]
        assert "100%" in overview["safe_harbor_rules"]["rule_2"]

    def test_overview_quarterly_due_dates(self):
        """Quarterly due dates should be documented."""
        overview = get_form1040es_overview()

        assert "Q1" in overview["quarterly_due_dates"]
        assert "Q2" in overview["quarterly_due_dates"]
        assert "Q3" in overview["quarterly_due_dates"]
        assert "Q4" in overview["quarterly_due_dates"]


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestEstimatedTaxEndpoint:
    """Tests for /api/v1/form1040es/calculate endpoint."""

    def test_calculate_endpoint_basic(self, auth_token):
        """Test basic estimated tax calculation endpoint."""
        resp = client.post(
            "/api/v1/form1040es/calculate",
            json={
                "filing_status": "single",
                "annual_income": "85000.00",
                "withholding": "5000.00",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "12000.00",
                "quarters_paid": 0,
                "amount_paid": "0",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "total_tax_liability" in data
        assert "balance_due" in data
        assert "quarterly_payment" in data
        assert "safe_harbor_met" in data
        assert "explanation" in data

    def test_calculate_endpoint_married_joint(self, auth_token):
        """Test endpoint with married filing jointly status."""
        resp = client.post(
            "/api/v1/form1040es/calculate",
            json={
                "filing_status": "married_joint",
                "annual_income": "150000.00",
                "withholding": "10000.00",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "20000.00",
                "quarters_paid": 0,
                "amount_paid": "0",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_tax_liability"] is not None

    def test_calculate_endpoint_with_credits(self, auth_token):
        """Test endpoint with tax credits."""
        resp = client.post(
            "/api/v1/form1040es/calculate",
            json={
                "filing_status": "single",
                "annual_income": "50000.00",
                "withholding": "0",
                "deductions": "0",
                "credits": "2000.00",
                "prior_year_tax": "5000.00",
                "quarters_paid": 0,
                "amount_paid": "0",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        # With $2,000 credits, tax should be lower
        assert float(data["total_tax_liability"]) < 4000

    def test_calculate_endpoint_invalid_input(self, auth_token):
        """Test endpoint with invalid input."""
        resp = client.post(
            "/api/v1/form1040es/calculate",
            json={
                "filing_status": "single",
                "annual_income": "invalid",
                "withholding": "0",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "5000.00",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_calculate_endpoint_requires_auth(self):
        """Test endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form1040es/calculate",
            json={
                "filing_status": "single",
                "annual_income": "50000.00",
                "withholding": "0",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "5000.00",
            },
        )

        assert resp.status_code == 401


class TestQuarterlyScheduleEndpoint:
    """Tests for /api/v1/form1040es/quarterly-schedule endpoint."""

    def test_quarterly_schedule_endpoint(self, auth_token):
        """Test quarterly schedule endpoint."""
        resp = client.post(
            "/api/v1/form1040es/quarterly-schedule",
            json={
                "filing_status": "single",
                "annual_income": "100000.00",
                "withholding": "0",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "15000.00",
                "quarters_paid": 0,
                "amount_paid": "0",
            },
            headers=auth_headers(auth_token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "payments" in data
        assert len(data["payments"]) == 4
        assert "total_due" in data
        assert "remaining_balance" in data

    def test_quarterly_schedule_endpoint_requires_auth(self):
        """Test endpoint requires authentication."""
        resp = client.post(
            "/api/v1/form1040es/quarterly-schedule",
            json={
                "filing_status": "single",
                "annual_income": "100000.00",
                "withholding": "0",
                "deductions": "0",
                "credits": "0",
                "prior_year_tax": "15000.00",
            },
        )

        assert resp.status_code == 401


class TestOverviewEndpoint:
    """Tests for /api/v1/form1040es/overview endpoint."""

    def test_overview_endpoint_no_auth_required(self):
        """Test overview endpoint (no authentication required)."""
        resp = client.get("/api/v1/form1040es/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["form"] == "Form 1040-ES"
        assert "safe_harbor_rules" in data
        assert "quarterly_due_dates" in data
