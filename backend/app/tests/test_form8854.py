"""
Tests for Form 8854 Expatriation Tax Module
Pure unit tests without FastAPI TestClient.
"""
import pytest
from app.modules.form8854 import (
    FilingRequirementTest,
    ExitTaxCalculator,
    PenaltyCalculator,
    get_form8854_overview,
    NET_WORTH_THRESHOLD,
    TAX_LIABILITY_THRESHOLD_2025,
    MARK_TO_MARKET_EXEMPTION_2025,
    FAILURE_TO_FILE_PENALTY,
    LONG_TERM_RESIDENT_YEARS,
)


# ============================================================================
# Module Tests (Pure Logic)
# ============================================================================


class TestFilingRequirementTest:
    """Test covered expatriate determination logic."""
    
    def test_net_worth_test_exceeds_threshold(self):
        """Net worth > $2M should trigger covered expatriate status."""
        assert FilingRequirementTest.net_worth_test(2_500_000) is True
    
    def test_net_worth_test_below_threshold(self):
        """Net worth <= $2M should not trigger by net worth alone."""
        assert FilingRequirementTest.net_worth_test(1_500_000) is False
        assert FilingRequirementTest.net_worth_test(2_000_000) is False
    
    def test_net_worth_test_exactly_at_threshold(self):
        """Net worth exactly at $2M should not trigger."""
        assert FilingRequirementTest.net_worth_test(NET_WORTH_THRESHOLD) is False
    
    def test_tax_liability_test_exceeds_threshold(self):
        """5-year avg tax > $206k (2025) should trigger covered expatriate."""
        assert FilingRequirementTest.tax_liability_test(220_000, 2025) is True
    
    def test_tax_liability_test_below_threshold(self):
        """5-year avg tax <= $206k should not trigger."""
        assert FilingRequirementTest.tax_liability_test(150_000, 2025) is False
        assert FilingRequirementTest.tax_liability_test(206_000, 2025) is False
    
    def test_long_term_resident_test_qualifies(self):
        """>=8 of last 15 years should qualify as long-term resident."""
        assert FilingRequirementTest.long_term_resident_test(8) is True
        assert FilingRequirementTest.long_term_resident_test(10) is True
        assert FilingRequirementTest.long_term_resident_test(15) is True
    
    def test_long_term_resident_test_does_not_qualify(self):
        """<8 years should not qualify as long-term resident."""
        assert FilingRequirementTest.long_term_resident_test(7) is False
        assert FilingRequirementTest.long_term_resident_test(3) is False
    
    def test_is_covered_expatriate_by_net_worth(self):
        """High net worth should result in covered expatriate."""
        result = FilingRequirementTest.is_covered_expatriate(
            net_worth=3_000_000,
            five_year_avg_tax=100_000,
            years_of_residence=10,
        )
        assert result["covered_expatriate"] is True
        assert result["net_worth_test"]["exceeds_threshold"] is True
    
    def test_is_covered_expatriate_by_tax_liability(self):
        """High tax liability should result in covered expatriate."""
        result = FilingRequirementTest.is_covered_expatriate(
            net_worth=1_000_000,
            five_year_avg_tax=250_000,
            years_of_residence=10,
        )
        assert result["covered_expatriate"] is True
        assert result["tax_liability_test"]["exceeds_threshold"] is True
    
    def test_is_covered_expatriate_both_tests_pass(self):
        """Both net worth and tax liability high should result in covered expatriate."""
        result = FilingRequirementTest.is_covered_expatriate(
            net_worth=5_000_000,
            five_year_avg_tax=300_000,
            years_of_residence=12,
        )
        assert result["covered_expatriate"] is True
        assert result["net_worth_test"]["exceeds_threshold"] is True
        assert result["tax_liability_test"]["exceeds_threshold"] is True
    
    def test_is_not_covered_expatriate(self):
        """Low net worth and low tax liability should not result in covered expatriate."""
        result = FilingRequirementTest.is_covered_expatriate(
            net_worth=1_000_000,
            five_year_avg_tax=100_000,
            years_of_residence=5,
        )
        assert result["covered_expatriate"] is False
        assert result["net_worth_test"]["exceeds_threshold"] is False
        assert result["tax_liability_test"]["exceeds_threshold"] is False


class TestExitTaxCalculator:
    """Test exit tax calculations."""
    
    def test_mark_to_market_gain_positive(self):
        """FMV > basis should yield positive gain."""
        gain = ExitTaxCalculator.calculate_mark_to_market_gain(
            fair_market_value=1_500_000,
            adjusted_basis=1_000_000
        )
        assert gain == 500_000
    
    def test_mark_to_market_gain_zero(self):
        """FMV = basis should yield zero gain."""
        gain = ExitTaxCalculator.calculate_mark_to_market_gain(
            fair_market_value=1_000_000,
            adjusted_basis=1_000_000
        )
        assert gain == 0
    
    def test_mark_to_market_gain_negative(self):
        """FMV < basis should yield zero (no loss recognized)."""
        gain = ExitTaxCalculator.calculate_mark_to_market_gain(
            fair_market_value=800_000,
            adjusted_basis=1_000_000
        )
        assert gain == 0
    
    def test_apply_exemption_below_threshold(self):
        """Gain below exemption should be fully exempt."""
        result = ExitTaxCalculator.apply_exemption(500_000, 2025)
        assert result["exemption_used"] == 500_000
        assert result["taxable_gain"] == 0
    
    def test_apply_exemption_above_threshold(self):
        """Gain above exemption should use full exemption."""
        result = ExitTaxCalculator.apply_exemption(1_500_000, 2025)
        assert result["exemption_used"] == MARK_TO_MARKET_EXEMPTION_2025
        assert result["taxable_gain"] == 1_500_000 - MARK_TO_MARKET_EXEMPTION_2025
    
    def test_apply_exemption_exactly_at_threshold(self):
        """Gain exactly at exemption should be fully exempt."""
        result = ExitTaxCalculator.apply_exemption(MARK_TO_MARKET_EXEMPTION_2025, 2025)
        assert result["exemption_used"] == MARK_TO_MARKET_EXEMPTION_2025
        assert result["taxable_gain"] == 0
    
    def test_calculate_exit_tax_with_exemption(self):
        """Exit tax calculation with partial exemption."""
        result = ExitTaxCalculator.calculate_exit_tax(
            fair_market_value=2_000_000,
            adjusted_basis=1_000_000,
            capital_gains_rate=0.20,
            year=2025
        )
        # Gain = 1M, Exemption = 866k, Taxable = 134k, Tax = 26.8k
        assert result["unrealized_gain"] == 1_000_000
        assert result["exemption_used"] == MARK_TO_MARKET_EXEMPTION_2025
        assert result["taxable_gain"] == 1_000_000 - MARK_TO_MARKET_EXEMPTION_2025
        assert result["exit_tax"] == pytest.approx(
            (1_000_000 - MARK_TO_MARKET_EXEMPTION_2025) * 0.20
        )
    
    def test_calculate_exit_tax_fully_exempt(self):
        """Exit tax should be zero when gain is below exemption."""
        result = ExitTaxCalculator.calculate_exit_tax(
            fair_market_value=1_500_000,
            adjusted_basis=1_000_000,
            capital_gains_rate=0.20,
            year=2025
        )
        # Gain = 500k, Exemption = 866k, Taxable = 0, Tax = 0
        assert result["unrealized_gain"] == 500_000
        assert result["exemption_used"] == 500_000
        assert result["taxable_gain"] == 0
        assert result["exit_tax"] == 0
    
    def test_calculate_exit_tax_no_gain(self):
        """Exit tax should be zero when FMV = basis."""
        result = ExitTaxCalculator.calculate_exit_tax(
            fair_market_value=1_000_000,
            adjusted_basis=1_000_000,
            capital_gains_rate=0.20,
            year=2025
        )
        assert result["unrealized_gain"] == 0
        assert result["exit_tax"] == 0


class TestPenaltyCalculator:
    """Test penalty calculations."""
    
    def test_failure_to_file_penalty(self):
        """Failure-to-file penalty should be $10,000."""
        result = PenaltyCalculator.failure_to_file_penalty(months_late=6)
        assert result["total_penalty"] == FAILURE_TO_FILE_PENALTY
        assert result["months_late"] == 6
    
    def test_estimate_total_penalties_with_failure_to_file(self):
        """Total penalties should include failure-to-file."""
        result = PenaltyCalculator.estimate_total_penalties(
            failed_to_file=True,
            months_late=12
        )
        assert result["total_penalties"] == FAILURE_TO_FILE_PENALTY
        assert len(result["penalties"]) == 1
    
    def test_estimate_total_penalties_no_failure(self):
        """No penalties if form was filed on time."""
        result = PenaltyCalculator.estimate_total_penalties(
            failed_to_file=False,
            months_late=0
        )
        assert result["total_penalties"] == 0
        assert len(result["penalties"]) == 0


class TestOverview:
    """Test overview function."""
    
    def test_get_form8854_overview(self):
        """Overview should return all key thresholds and info."""
        overview = get_form8854_overview()
        assert overview["form_name"] == "Form 8854"
        assert overview["covered_expatriate_tests"]["net_worth_threshold"] == NET_WORTH_THRESHOLD
        assert overview["covered_expatriate_tests"]["tax_liability_threshold_2025"] == TAX_LIABILITY_THRESHOLD_2025
        assert overview["exit_tax"]["mark_to_market_exemption_2025"] == MARK_TO_MARKET_EXEMPTION_2025
        assert overview["penalties"]["failure_to_file"] == FAILURE_TO_FILE_PENALTY

