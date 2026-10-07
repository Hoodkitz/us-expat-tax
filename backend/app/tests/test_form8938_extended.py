"""
Tests for Form 8938 Extended Features.

Tests cover:
- Foreign trust reporting (grantor, beneficiary, other)
- Joint filing thresholds (domestic vs abroad)
- Accuracy-related penalty (40% on underpayment)
- Statute of limitations (3 vs 6 years)
- Edge cases (threshold boundaries, zero values, large amounts)
"""
import pytest
from app.modules.form8938_extended import (
    ForeignTrustInput,
    ForeignTrustResult,
    JointFilingThresholdInput,
    JointFilingThresholdResult,
    AccuracyPenaltyInput,
    AccuracyPenaltyResult,
    StatuteOfLimitationsInput,
    StatuteOfLimitationsResult,
    check_foreign_trust_reporting,
    check_joint_filing_threshold,
    calculate_accuracy_penalty,
    check_statute_of_limitations,
    THRESHOLD_MFJ_ABROAD_YEAR_END,
    THRESHOLD_MFJ_ABROAD_ANY_TIME,
    THRESHOLD_SINGLE_ABROAD_YEAR_END,
    THRESHOLD_SINGLE_ABROAD_ANY_TIME,
    THRESHOLD_MFJ_DOMESTIC_YEAR_END,
    THRESHOLD_MFJ_DOMESTIC_ANY_TIME,
    THRESHOLD_SINGLE_DOMESTIC_YEAR_END,
    THRESHOLD_SINGLE_DOMESTIC_ANY_TIME,
    PENALTY_ACCURACY_RELATED,
    STATUTE_NORMAL_YEARS,
    STATUTE_FOREIGN_ASSET_UNREPORTED_YEARS,
)


# ---------------------------------------------------------------------------
# Test: Foreign Trust Reporting
# ---------------------------------------------------------------------------

class TestForeignTrustReporting:
    """Foreign trust reporting under IRC §§671-679."""

    def test_grantor_trust_reporting(self):
        """Grantor trust requires Forms 3520, 3520-A, and 8938."""
        inp = ForeignTrustInput(
            trust_name="Smith Family Trust",
            trust_type="grantor",
            country="CH",
            fair_market_value_usd=500_000.0,
            distributions_received_usd=0.0,
            is_grantor=True,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is True
        assert "Form 3520" in result.required_forms
        assert "Form 3520-A" in result.required_forms
        assert "Form 8938" in result.required_forms
        assert "grantor" in result.explanation.lower()
        assert "35%" in result.penalties_if_not_reported or "10,000" in result.penalties_if_not_reported

    def test_beneficiary_trust_reporting(self):
        """Beneficiary of foreign trust requires Forms 3520 and 8938."""
        inp = ForeignTrustInput(
            trust_name="European Family Trust",
            trust_type="beneficiary",
            country="LU",
            fair_market_value_usd=250_000.0,
            distributions_received_usd=15_000.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is False
        assert "Form 3520" in result.required_forms
        assert "Form 8938" in result.required_forms
        assert "Form 3520-A" not in result.required_forms
        assert result.trust_type == "beneficiary"

    def test_other_trust_interest(self):
        """Other trust interest requires only Form 8938 if value exceeds threshold."""
        inp = ForeignTrustInput(
            trust_name="Offshore Trust",
            trust_type="other",
            country="KY",
            fair_market_value_usd=100_000.0,
            distributions_received_usd=0.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.is_grantor_trust is False
        assert "Form 8938" in result.required_forms
        # Should not require 3520/3520-A for "other" type
        assert len([f for f in result.required_forms if "3520" in f]) == 0

    def test_zero_value_trust(self):
        """Trust with zero value still requires reporting."""
        inp = ForeignTrustInput(
            trust_name="Empty Trust",
            trust_type="beneficiary",
            country="UK",
            fair_market_value_usd=0.0,
            distributions_received_usd=0.0,
            is_grantor=False,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.fair_market_value_usd == 0.0


# ---------------------------------------------------------------------------
# Test: Joint Filing Thresholds
# ---------------------------------------------------------------------------

class TestJointFilingThresholds:
    """Joint filing thresholds for domestic vs abroad residency."""

    def test_mfj_abroad_below_threshold(self):
        """MFJ living abroad — below $400k/$600k thresholds."""
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=350_000.0,
            max_any_time_value_usd=450_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is False
        assert result.applicable_threshold_year_end == THRESHOLD_MFJ_ABROAD_YEAR_END
        assert result.applicable_threshold_any_time == THRESHOLD_MFJ_ABROAD_ANY_TIME
        assert "not required" in result.recommendation.lower()

    def test_mfj_abroad_above_year_end_threshold(self):
        """MFJ living abroad — above $400k year-end threshold."""
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=450_000.0,
            max_any_time_value_usd=550_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert "year-end value" in result.reasons[0].lower()
        assert result.applicable_threshold_year_end == 400_000.0

    def test_mfj_abroad_above_any_time_threshold(self):
        """MFJ living abroad — above $600k any-time threshold."""
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=350_000.0,
            max_any_time_value_usd=650_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert "maximum value" in result.reasons[0].lower()
        assert result.applicable_threshold_any_time == 600_000.0

    def test_single_abroad_thresholds(self):
        """Single living abroad — $200k/$300k thresholds."""
        inp = JointFilingThresholdInput(
            filing_status="single",
            residency_status="abroad",
            year_end_value_usd=250_000.0,
            max_any_time_value_usd=280_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == THRESHOLD_SINGLE_ABROAD_YEAR_END
        assert result.applicable_threshold_any_time == THRESHOLD_SINGLE_ABROAD_ANY_TIME

    def test_mfj_domestic_thresholds(self):
        """MFJ living domestic — $100k/$150k thresholds."""
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="domestic",
            year_end_value_usd=120_000.0,
            max_any_time_value_usd=140_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == THRESHOLD_MFJ_DOMESTIC_YEAR_END
        assert result.applicable_threshold_any_time == THRESHOLD_MFJ_DOMESTIC_ANY_TIME

    def test_single_domestic_thresholds(self):
        """Single living domestic — $50k/$75k thresholds."""
        inp = JointFilingThresholdInput(
            filing_status="single",
            residency_status="domestic",
            year_end_value_usd=60_000.0,
            max_any_time_value_usd=70_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == THRESHOLD_SINGLE_DOMESTIC_YEAR_END
        assert result.applicable_threshold_any_time == THRESHOLD_SINGLE_DOMESTIC_ANY_TIME

    def test_mfs_abroad_uses_single_thresholds(self):
        """MFS living abroad uses single thresholds ($200k/$300k)."""
        inp = JointFilingThresholdInput(
            filing_status="mfs",
            residency_status="abroad",
            year_end_value_usd=250_000.0,
            max_any_time_value_usd=250_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is True
        assert result.applicable_threshold_year_end == THRESHOLD_SINGLE_ABROAD_YEAR_END

    def test_exactly_at_threshold(self):
        """Exactly at threshold — should NOT be required (must exceed)."""
        inp = JointFilingThresholdInput(
            filing_status="mfj",
            residency_status="abroad",
            year_end_value_usd=400_000.0,
            max_any_time_value_usd=600_000.0,
            tax_year=2024,
        )
        result = check_joint_filing_threshold(inp)
        assert result.filing_required is False


# ---------------------------------------------------------------------------
# Test: Accuracy-Related Penalty
# ---------------------------------------------------------------------------

class TestAccuracyPenalty:
    """40% accuracy-related penalty for undisclosed foreign assets."""

    def test_basic_accuracy_penalty(self):
        """40% penalty on underpayment."""
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=50_000.0,
            total_foreign_assets_usd=300_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        assert result.penalty_rate == PENALTY_ACCURACY_RELATED
        assert result.penalty_amount == 50_000.0 * 0.40
        assert result.penalty_amount == 20_000.0
        assert "40%" in result.explanation
        assert "IRC §6662(j)" in result.explanation

    def test_zero_underpayment(self):
        """Zero underpayment — zero penalty."""
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=0.0,
            total_foreign_assets_usd=500_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        assert result.penalty_amount == 0.0
        assert result.underpayment_amount == 0.0

    def test_large_underpayment(self):
        """Large underpayment — substantial penalty."""
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=200_000.0,
            total_foreign_assets_usd=1_000_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        expected_penalty = 200_000.0 * 0.40
        assert result.penalty_amount == expected_penalty
        assert result.penalty_amount == 80_000.0


# ---------------------------------------------------------------------------
# Test: Statute of Limitations
# ---------------------------------------------------------------------------

class TestStatuteOfLimitations:
    """Statute of limitations (3 vs 6 years)."""

    def test_normal_statute_disclosed_assets(self):
        """Normal 3-year statute when assets are disclosed."""
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=True,
            foreign_asset_value_usd=500_000.0,
            gross_income_usd=200_000.0,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == STATUTE_NORMAL_YEARS
        assert result.is_extended is False
        assert result.foreign_assets_disclosed is True
        assert "normal" in result.explanation.lower() or "3" in result.explanation

    def test_extended_statute_undisclosed_large_assets(self):
        """Extended 6-year statute when undisclosed assets exceed 25% of gross income."""
        gross_income = 200_000.0
        foreign_assets = 100_000.0  # > 25% of gross income (50k)
        
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=foreign_assets,
            gross_income_usd=gross_income,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == STATUTE_FOREIGN_ASSET_UNREPORTED_YEARS
        assert result.is_extended is True
        assert "6" in result.explanation or "extended" in result.explanation.lower()

    def test_undisclosed_but_below_threshold(self):
        """Undisclosed assets below 25% of gross income — normal statute."""
        gross_income = 1_000_000.0
        foreign_assets = 100_000.0  # < 25% of gross income (250k)
        
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=foreign_assets,
            gross_income_usd=gross_income,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == STATUTE_NORMAL_YEARS
        assert result.is_extended is False

    def test_exactly_25_percent_threshold(self):
        """Exactly 25% threshold — should NOT extend (must exceed)."""
        gross_income = 400_000.0
        foreign_assets = 100_000.0  # Exactly 25%
        
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=foreign_assets,
            gross_income_usd=gross_income,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        # At exactly 25%, should not extend
        assert result.statute_years == STATUTE_NORMAL_YEARS

    def test_assessment_deadline_calculation(self):
        """Assessment deadline correctly calculated."""
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=300_000.0,
            gross_income_usd=200_000.0,  # 300k > 25% of 200k (50k)
            tax_year=2020,
        )
        result = check_statute_of_limitations(inp)
        # Tax year 2020 + 6 years statute + 1 year filing = 2027
        assert result.assessment_deadline_year == 2020 + 6 + 1
        assert result.is_extended is True

    def test_zero_foreign_assets(self):
        """Zero foreign assets — normal statute applies."""
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=0.0,
            gross_income_usd=100_000.0,
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        assert result.statute_years == STATUTE_NORMAL_YEARS
        assert result.is_extended is False


# ---------------------------------------------------------------------------
# Test: Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_very_large_trust_value(self):
        """Very large trust value is handled correctly."""
        inp = ForeignTrustInput(
            trust_name="Ultra High Net Worth Trust",
            trust_type="grantor",
            country="CH",
            fair_market_value_usd=50_000_000.0,
            distributions_received_usd=1_000_000.0,
            is_grantor=True,
        )
        result = check_foreign_trust_reporting(inp)
        assert result.reporting_required is True
        assert result.fair_market_value_usd == 50_000_000.0

    def test_multiple_statuses_combinations(self):
        """Test all filing status + residency combinations."""
        statuses = ["single", "mfj", "mfs", "hoh"]
        residencies = ["domestic", "abroad"]
        
        for status in statuses:
            for residency in residencies:
                inp = JointFilingThresholdInput(
                    filing_status=status,  # type: ignore
                    residency_status=residency,  # type: ignore
                    year_end_value_usd=1_000_000.0,  # High enough to trigger any threshold
                    max_any_time_value_usd=1_000_000.0,
                    tax_year=2024,
                )
                result = check_joint_filing_threshold(inp)
                assert result.filing_required is True
                assert result.filing_status == status
                assert result.residency_status == residency

    def test_accuracy_penalty_with_cents(self):
        """Accuracy penalty calculation handles cents correctly."""
        inp = AccuracyPenaltyInput(
            underpayment_amount_usd=12_345.67,
            total_foreign_assets_usd=250_000.0,
            tax_year=2024,
        )
        result = calculate_accuracy_penalty(inp)
        expected = 12_345.67 * 0.40
        assert result.penalty_amount == pytest.approx(expected, rel=1e-9)

    def test_statute_with_very_high_income(self):
        """Statute of limitations with very high income."""
        inp = StatuteOfLimitationsInput(
            foreign_assets_disclosed=False,
            foreign_asset_value_usd=10_000_000.0,
            gross_income_usd=100_000_000.0,  # Very high income
            tax_year=2024,
        )
        result = check_statute_of_limitations(inp)
        # 10M < 25% of 100M (25M), so normal statute
        assert result.statute_years == STATUTE_NORMAL_YEARS
        assert result.is_extended is False
