"""
Tests for Form 8938 FATCA module.

Tests cover:
- Filing requirement thresholds (Single, MFJ)
- Penalty calculation (base, continued failure, willful)
- Overview endpoint
- Edge cases (zero accounts, exact threshold, large values)
"""
import pytest
from app.modules.form8938 import (
    FilingRequirementInput,
    FilingRequirementResult,
    PenaltyCalculationInput,
    PenaltyResult,
    Form8938Overview,
    ForeignAccountInput,
    check_filing_requirement,
    calculate_penalty,
    get_overview,
    THRESHOLD_SINGLE_YEAR_END,
    THRESHOLD_MFJ_YEAR_END,
    PENALTY_FAILURE_TO_FILE,
    PENALTY_CONTINUED_FAILURE_PER_30_DAYS,
    PENALTY_CONTINUED_FAILURE_MAX,
    PENALTY_WILLFUL_MINIMUM,
    PENALTY_WILLFUL_PERCENTAGE,
)


# ---------------------------------------------------------------------------
# Test: Filing requirement — Single filer below threshold
# ---------------------------------------------------------------------------

class TestFilingRequirementSingleBelowThreshold:
    """Single filer with total value below $10,000 threshold."""

    def test_single_filer_below_threshold(self):
        inp = FilingRequirementInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Deutsche Bank Savings",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=30_000.0,
                ),
                ForeignAccountInput(
                    account_name="Commerzbank Checking",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15_000.0,
                ),
            ],
            tax_year=2025,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.threshold_usd == THRESHOLD_SINGLE_YEAR_END
        assert result.total_value_usd == 45_000.0
        assert result.penalty_if_not_filed == 0.0
        assert "not required" in result.recommendation.lower()

    def test_single_filer_exactly_at_threshold(self):
        """Exactly at threshold — not required (must exceed)."""
        inp = FilingRequirementInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=THRESHOLD_SINGLE_YEAR_END,
                ),
            ],
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.total_value_usd == THRESHOLD_SINGLE_YEAR_END

    def test_single_filer_just_above_threshold(self):
        """Just above threshold — required."""
        inp = FilingRequirementInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=THRESHOLD_SINGLE_YEAR_END + 0.01,
                ),
            ],
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.penalty_if_not_filed == PENALTY_FAILURE_TO_FILE


# ---------------------------------------------------------------------------
# Test: Filing requirement — MFJ filer
# ---------------------------------------------------------------------------

class TestFilingRequirementMFJ:
    """Married Filing Jointly filer with $20,000 threshold."""

    def test_mfj_below_threshold(self):
        inp = FilingRequirementInput(
            filing_status="mfj",
            accounts=[
                ForeignAccountInput(
                    account_name="Joint Savings",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15000.0,
                ),
            ],
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.threshold_usd == THRESHOLD_MFJ_YEAR_END

    def test_mfj_above_threshold(self):
        inp = FilingRequirementInput(
            filing_status="mfj",
            accounts=[
                ForeignAccountInput(
                    account_name="Joint Savings",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=120_000.0,
                ),
            ],
            tax_year=2025,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.total_value_usd == 120_000.0

    def test_mfj_multiple_accounts_aggregate(self):
        """Multiple accounts that individually are below but aggregate above."""
        inp = FilingRequirementInput(
            filing_status="mfj",
            accounts=[
                ForeignAccountInput(
                    account_name="Account 1",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=40_000.0,
                ),
                ForeignAccountInput(
                    account_name="Account 2",
                    account_type="brokerage_account",
                    country="FR",
                    max_value_usd=35_000.0,
                ),
                ForeignAccountInput(
                    account_name="Account 3",
                    account_type="mutual_fund",
                    country="UK",
                    max_value_usd=30_000.0,
                ),
            ],
            tax_year=2025,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.total_value_usd == 105_000.0


# ---------------------------------------------------------------------------
# Test: Penalty calculation
# ---------------------------------------------------------------------------

class TestPenaltyCalculation:
    """Penalty calculation for various scenarios."""

    def test_base_penalty_only(self):
        """Non-willful, no continued failure — base penalty only."""
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15000.0,
                ),
            ],
            tax_year=2024,
            days_unreported=0,
            is_willful=False,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_FAILURE_TO_FILE
        assert result.continued_failure_penalty == 0.0
        assert result.willful_penalty == 0.0
        assert result.total_penalty == PENALTY_FAILURE_TO_FILE

    def test_continued_failure_penalty(self):
        """Continued failure after IRS notice — 60 days = 2 periods."""
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15000.0,
                ),
            ],
            tax_year=2024,
            days_unreported=60,
            is_willful=False,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_FAILURE_TO_FILE
        assert result.continued_failure_penalty == 2 * PENALTY_CONTINUED_FAILURE_PER_30_DAYS
        assert result.total_penalty == PENALTY_FAILURE_TO_FILE + 2 * PENALTY_CONTINUED_FAILURE_PER_30_DAYS

    def test_continued_failure_max_cap(self):
        """Continued failure capped at $50,000."""
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15000.0,
                ),
            ],
            tax_year=2024,
            days_unreported=365,
            is_willful=False,
        )
        result = calculate_penalty(inp)
        assert result.continued_failure_penalty == PENALTY_CONTINUED_FAILURE_MAX
        assert result.total_penalty == PENALTY_FAILURE_TO_FILE + PENALTY_CONTINUED_FAILURE_MAX

    def test_willful_penalty_minimum(self):
        """Willful failure with small account — $100,000 minimum."""
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=15000.0,
                ),
            ],
            tax_year=2024,
            days_unreported=0,
            is_willful=True,
        )
        result = calculate_penalty(inp)
        assert result.willful_penalty == PENALTY_WILLFUL_MINIMUM
        assert result.total_penalty == PENALTY_FAILURE_TO_FILE + PENALTY_WILLFUL_MINIMUM

    def test_willful_penalty_percentage(self):
        """Willful failure with large account — 50% of value exceeds $100,000."""
        large_value = 500_000.0
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Large Account",
                    account_type="brokerage_account",
                    country="CH",
                    max_value_usd=large_value,
                ),
            ],
            tax_year=2024,
            days_unreported=0,
            is_willful=True,
        )
        result = calculate_penalty(inp)
        expected_willful = large_value * PENALTY_WILLFUL_PERCENTAGE
        assert result.willful_penalty == expected_willful
        assert result.willful_penalty > PENALTY_WILLFUL_MINIMUM
        assert result.total_penalty == PENALTY_FAILURE_TO_FILE + expected_willful

    def test_willful_with_continued_failure(self):
        """Willful + continued failure — all penalties combined."""
        inp = PenaltyCalculationInput(
            filing_status="mfj",
            accounts=[
                ForeignAccountInput(
                    account_name="Account 1",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=100_000.0,
                ),
            ],
            tax_year=2024,
            days_unreported=90,
            is_willful=True,
        )
        result = calculate_penalty(inp)
        assert result.base_penalty == PENALTY_FAILURE_TO_FILE
        assert result.continued_failure_penalty == 3 * PENALTY_CONTINUED_FAILURE_PER_30_DAYS
        # Willful penalty = greater of $100,000 or 50% of account value
        expected_willful = max(100_000.0, 100_000.0 * PENALTY_WILLFUL_PERCENTAGE)
        assert result.willful_penalty == expected_willful
        expected_total = (
            PENALTY_FAILURE_TO_FILE
            + 3 * PENALTY_CONTINUED_FAILURE_PER_30_DAYS
            + expected_willful
        )
        assert result.total_penalty == expected_total


# ---------------------------------------------------------------------------
# Test: Overview
# ---------------------------------------------------------------------------

class TestOverview:
    """Overview endpoint returns correct information."""

    def test_overview_contains_thresholds(self):
        result = get_overview()
        assert result.title is not None
        assert "single_year_end" in result.thresholds
        assert "mfj_year_end" in result.thresholds
        assert result.thresholds["single_year_end"] == THRESHOLD_SINGLE_YEAR_END
        assert result.thresholds["mfj_year_end"] == THRESHOLD_MFJ_YEAR_END

    def test_overview_contains_penalties(self):
        result = get_overview()
        assert "failure_to_file" in result.penalties
        assert "willful_minimum" in result.penalties
        assert result.penalties["failure_to_file"] == PENALTY_FAILURE_TO_FILE
        assert result.penalties["willful_minimum"] == PENALTY_WILLFUL_MINIMUM

    def test_overview_contains_account_types(self):
        result = get_overview()
        assert len(result.account_types) > 0
        assert any("bank" in at.lower() for at in result.account_types)
        assert any("brokerage" in at.lower() for at in result.account_types)

    def test_overview_contains_recommendation(self):
        result = get_overview()
        assert result.recommendation is not None
        assert len(result.recommendation) > 50


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_zero_accounts(self):
        """No accounts — filing not required."""
        inp = FilingRequirementInput(
            filing_status="single",
            accounts=[],
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.total_value_usd == 0.0

    def test_zero_value_account(self):
        """Account with zero value — doesn't contribute to total."""
        inp = FilingRequirementInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Empty Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=0.0,
                ),
            ],
            tax_year=2024,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False
        assert result.total_value_usd == 0.0

    def test_very_large_account(self):
        """Very large account value — willful penalty is 50% of value."""
        large_value = 10_000_000.0
        inp = PenaltyCalculationInput(
            filing_status="single",
            accounts=[
                ForeignAccountInput(
                    account_name="Swiss Bank Account",
                    account_type="bank_account",
                    country="CH",
                    max_value_usd=large_value,
                ),
            ],
            tax_year=2024,
            days_unreported=0,
            is_willful=True,
        )
        result = calculate_penalty(inp)
        assert result.willful_penalty == large_value * PENALTY_WILLFUL_PERCENTAGE
        assert result.willful_penalty == 5_000_000.0

    def test_mfs_uses_single_threshold(self):
        """Married Filing Separately uses single threshold."""
        inp = FilingRequirementInput(
            filing_status="mfs",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=55_000.0,
                ),
            ],
            tax_year=2025,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.threshold_usd == THRESHOLD_SINGLE_YEAR_END

    def test_hoh_uses_single_threshold(self):
        """Head of Household uses single threshold."""
        inp = FilingRequirementInput(
            filing_status="hoh",
            accounts=[
                ForeignAccountInput(
                    account_name="Test Account",
                    account_type="bank_account",
                    country="DE",
                    max_value_usd=55_000.0,
                ),
            ],
            tax_year=2025,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.threshold_usd == THRESHOLD_SINGLE_YEAR_END
