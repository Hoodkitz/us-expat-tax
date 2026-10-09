"""Tests for FEIE (Form 2555) module — IRS Rev. Proc. 2024-40 limits."""
from __future__ import annotations

import pytest

from app.modules.feie import (
    FEIE_LIMITS,
    DEFAULT_FEIE_LIMIT,
    FEIEInput,
    calculate_feie,
    check_feie_eligibility,
)


class TestFEIELimits:
    """Verify IRS FEIE limits per tax year."""

    def test_2025_limit_is_138300(self):
        """IRS Rev. Proc. 2024-40: 2025 FEIE limit = $138,300."""
        assert FEIE_LIMITS[2025] == 138_300.0

    def test_default_limit_matches_2025(self):
        """Default limit should match the most recent tax year."""
        assert DEFAULT_FEIE_LIMIT == 138_300.0

    def test_all_limits_are_monotonically_increasing(self):
        """FEIE limits should never decrease year-over-year."""
        years = sorted(FEIE_LIMITS.keys())
        for i in range(1, len(years)):
            assert FEIE_LIMITS[years[i]] >= FEIE_LIMITS[years[i - 1]]

    def test_known_historical_limits(self):
        """Spot-check known IRS limits."""
        assert FEIE_LIMITS[2020] == 107_600.0
        assert FEIE_LIMITS[2021] == 108_700.0
        assert FEIE_LIMITS[2022] == 112_000.0
        assert FEIE_LIMITS[2023] == 120_000.0
        assert FEIE_LIMITS[2024] == 126_500.0


class TestFEIECalculation:
    """Test FEIE calculation with 2025 limits."""

    def test_2025_full_exclusion(self):
        """Taxpayer with income below 2025 limit gets full exclusion."""
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=100_000.0,
            housing_costs=0.0,
            days_in_foreign_country=365,
            bona_fide_resident=False,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        assert result.feie_limit == 138_300.0
        assert result.feie_exclusion == 100_000.0
        assert result.taxable_income_estimate == 0.0

    def test_2025_excess_income_capped(self):
        """Income above 2025 limit is capped at $138,300."""
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=200_000.0,
            housing_costs=0.0,
            days_in_foreign_country=365,
            bona_fide_resident=False,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        assert result.feie_exclusion == 138_300.0
        assert result.taxable_income_estimate == 61_700.0

    def test_2025_housing_exclusion(self):
        """Housing exclusion uses 2025 limit for base amount."""
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=138_300.0,
            housing_costs=50_000.0,
            days_in_foreign_country=365,
            bona_fide_resident=False,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is True
        # Base = 16% of 138,300 = 22,128
        assert result.housing_base_amount == pytest.approx(22_128.0)
        # Net housing = 50,000 - 0 = 50,000
        # Exclusion = min(50,000 - 22,128, 30% * 138,300) = min(27,872, 41,490) = 27,872
        assert result.housing_exclusion == pytest.approx(27_872.0)

    def test_not_qualified_no_exclusion(self):
        """Taxpayer not meeting either test gets no exclusion."""
        inp = FEIEInput(
            tax_year=2025,
            foreign_earned_income=100_000.0,
            housing_costs=0.0,
            days_in_foreign_country=100,
            bona_fide_resident=False,
            filing_status="single",
        )
        result = calculate_feie(inp)
        assert result.qualifies is False
        assert result.feie_exclusion == 0.0
        assert result.taxable_income_estimate == 100_000.0


class TestFEIEEligibility:
    """Test quick eligibility pre-check."""

    def test_non_resident_not_eligible(self):
        result = check_feie_eligibility(
            days_outside_us=365,
            bona_fide_resident=True,
            us_citizen_or_green_card=False,
        )
        assert result["eligible"] is False

    def test_physical_presence_passes(self):
        result = check_feie_eligibility(
            days_outside_us=340,
            bona_fide_resident=False,
            us_citizen_or_green_card=True,
        )
        assert result["eligible"] is True
        assert result["test_passed"] == "physical_presence"

    def test_bona_fide_residence_passes(self):
        result = check_feie_eligibility(
            days_outside_us=100,
            bona_fide_resident=True,
            us_citizen_or_green_card=True,
        )
        assert result["eligible"] is True
        assert result["test_passed"] == "bona_fide_residence"

    def test_neither_test_fails(self):
        result = check_feie_eligibility(
            days_outside_us=100,
            bona_fide_resident=False,
            us_citizen_or_green_card=True,
        )
        assert result["eligible"] is False
