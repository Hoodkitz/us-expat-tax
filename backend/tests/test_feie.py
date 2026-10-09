
"""Tests for FEIE (Foreign Earned Income Exclusion) module."""
import pytest
from app.modules.feie import FEIEInput, FEIEResult, calculate_feie, check_feie_eligibility


class TestFEIECalculation:
    """Test FEIE calculation."""

    def test_basic_feie_qualifies(self):
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=120000.0,
            housing_costs=0.0,
            days_in_foreign_country=350,
            bona_fide_resident=True,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        assert result.qualifies_bfr is True
        assert result.feie_exclusion > 0
        assert result.total_exclusion > 0

    def test_feie_not_enough_days(self):
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=120000.0,
            housing_costs=0.0,
            days_in_foreign_country=100,
            bona_fide_resident=False,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is False

    def test_feie_with_housing(self):
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=130000.0,
            housing_costs=20000.0,
            days_in_foreign_country=340,
            bona_fide_resident=True,
            filing_status="single",
            employer_provided_housing=5000.0,
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        assert result.housing_exclusion >= 0

    def test_feie_married_joint(self):
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=200000.0,
            housing_costs=0.0,
            days_in_foreign_country=365,
            bona_fide_resident=True,
            filing_status="married_filing_jointly",
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        assert result.taxable_income_estimate >= 0


class TestFEIEEligibility:
    """Test FEIE eligibility check."""

    def test_bona_fide_resident_eligible(self):
        result = check_feie_eligibility(days_outside_us=330, bona_fide_resident=True, us_citizen_or_green_card=True)
        assert result["eligible"] is True

    def test_physical_presence_eligible(self):
        result = check_feie_eligibility(days_outside_us=340, bona_fide_resident=False, us_citizen_or_green_card=True)
        assert result["eligible"] is True

    def test_too_few_days_not_eligible(self):
        result = check_feie_eligibility(days_outside_us=50, bona_fide_resident=False, us_citizen_or_green_card=True)
        assert result["eligible"] is False

    def test_non_us_citizen_not_eligible(self):
        result = check_feie_eligibility(days_outside_us=340, bona_fide_resident=True, us_citizen_or_green_card=False)
        assert result["eligible"] is False
