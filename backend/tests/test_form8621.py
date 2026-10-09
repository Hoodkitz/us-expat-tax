
"""Tests for Form 8621 (PFIC) module."""
import pytest
from app.modules.form8621 import (
    FilingRequirementInput, MTMCalculationInput, QEFCalculationInput,
    ExcessDistributionInput, check_filing_requirement, calculate_mtm,
    calculate_qef, calculate_excess_distribution, get_overview,
)


class TestFilingRequirement:
    """Test Form 8621 filing requirement."""

    def test_pfic_interest_no_sale(self):
        inp = FilingRequirementInput(
            has_pfic_interest=True,
            had_sale_or_distribution=False,
            received_excess_distribution=False,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert len(result.reasons) > 0

    def test_pfic_with_sale(self):
        inp = FilingRequirementInput(
            has_pfic_interest=True,
            had_sale_or_distribution=True,
            received_excess_distribution=False,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True

    def test_excess_distribution(self):
        inp = FilingRequirementInput(
            has_pfic_interest=True,
            had_sale_or_distribution=True,
            received_excess_distribution=True,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is True
        assert result.penalty_if_not_filed > 0

    def test_no_pfic_no_filing(self):
        inp = FilingRequirementInput(
            has_pfic_interest=False,
            had_sale_or_distribution=False,
            received_excess_distribution=False,
        )
        result = check_filing_requirement(inp)
        assert result.filing_required is False


class TestMTMCalculation:
    """Test Mark-to-Market calculation."""

    def test_mtm_gain(self):
        inp = MTMCalculationInput(
            beginning_fmv=10000.0,
            ending_fmv=15000.0,
            tax_year=2025,
        )
        result = calculate_mtm(inp)
        assert result.unrealized_gain_or_loss == 5000.0
        assert result.ordinary_income_or_loss == 5000.0
        assert result.tax_treatment == "Ordinary Income"

    def test_mtm_loss(self):
        inp = MTMCalculationInput(
            beginning_fmv=15000.0,
            ending_fmv=10000.0,
            tax_year=2025,
        )
        result = calculate_mtm(inp)
        assert result.unrealized_gain_or_loss == -5000.0
        assert result.tax_treatment == "Ordinary Loss"


class TestQEFCalculation:
    """Test QEF election calculation."""

    def test_qef_basic(self):
        inp = QEFCalculationInput(
            ordinary_earnings=5000.0,
            net_capital_gain=2000.0,
            ownership_percentage=10.0,
            tax_year=2025,
        )
        result = calculate_qef(inp)
        assert result.ordinary_earnings_includible == 500.0
        assert result.capital_gain_includible == 200.0
        assert result.total_inclusion == 700.0


class TestExcessDistribution:
    """Test excess distribution calculation."""

    def test_basic_distribution(self):
        inp = ExcessDistributionInput(
            total_distribution=10000.0,
            holding_period_years=5,
            tax_year=2025,
        )
        result = calculate_excess_distribution(inp)
        assert result.total_distribution == 10000.0
        assert result.excess_amount == 10000.0
        assert result.deferred_tax_amount > 0

    def test_no_excess_distribution(self):
        inp = ExcessDistributionInput(
            total_distribution=1000.0,
            holding_period_years=5,
            prior_distributions=[800.0, 900.0, 1000.0],
            tax_year=2025,
        )
        result = calculate_excess_distribution(inp)
        assert result.excess_amount == 0.0


class TestOverview:
    """Test Form 8621 overview."""

    def test_overview(self):
        result = get_overview()
        assert hasattr(result, "form_name") or hasattr(result, "title") or hasattr(result, "description")
