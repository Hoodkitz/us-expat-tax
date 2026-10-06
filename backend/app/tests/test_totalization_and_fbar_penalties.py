"""
Tests for Totalization Agreement helper and FBAR Penalties calculator.
Pure unit tests; no HTTP client or JWT required.
"""
from __future__ import annotations

import pytest

from app.modules.totalization import (
    TotalizationRequest,
    check_totalization,
    _CANONICAL_NAMES,
    TOTALIZATION_COUNTRIES,
)
from app.modules.fbar_penalties import (
    FBARPenaltyRequest,
    calculate_fbar_penalties,
    NON_WILLFUL_ADJUSTED_2024,
    WILLFUL_BASE_MIN,
    FRAUD_MAX_FINE,
    STREAMLINED_PENALTY_PCT,
)


# ===========================================================================
# Totalization Agreement tests
# ===========================================================================


class TestTotalizationCountriesExist:
    """Agreement-exists scenarios."""

    def test_germany_agreement_exists(self):
        req = TotalizationRequest(
            country="Germany",
            employment_type="employee",
            years_in_us=3.0,
            years_in_country=2.0,
            us_citizen=True,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True
        assert result.avoid_double_taxation is True

    def test_uk_agreement_exists(self):
        req = TotalizationRequest(
            country="UK",
            employment_type="employee",
            years_in_us=5.0,
            years_in_country=4.0,
            us_citizen=False,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True
        assert result.avoid_double_taxation is True

    def test_united_kingdom_alias_works(self):
        req = TotalizationRequest(
            country="United Kingdom",
            employment_type="employee",
            years_in_us=5.0,
            years_in_country=4.0,
            us_citizen=False,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True

    def test_france_agreement_exists(self):
        req = TotalizationRequest(
            country="France",
            employment_type="self_employed",
            years_in_us=8.0,
            years_in_country=3.0,
            us_citizen=True,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True

    def test_no_agreement_country(self):
        req = TotalizationRequest(
            country="China",
            employment_type="employee",
            years_in_us=5.0,
            years_in_country=3.0,
            us_citizen=True,
        )
        result = check_totalization(req)
        assert result.agreement_exists is False
        assert result.avoid_double_taxation is False
        assert result.fica_exempt is False
        assert "does not have a Totalization Agreement" in result.explanation

    def test_no_agreement_russia(self):
        req = TotalizationRequest(
            country="Russia",
            employment_type="employee",
            years_in_us=2.0,
            years_in_country=5.0,
            us_citizen=False,
        )
        result = check_totalization(req)
        assert result.agreement_exists is False
        assert result.fica_exempt is False


class TestTotalizationFICAExemption:
    """FICA exemption / applicable system logic."""

    def test_temporary_employee_not_fica_exempt(self):
        """Employee on short assignment: stays under US system → NOT exempt from FICA."""
        req = TotalizationRequest(
            country="Germany",
            employment_type="employee",
            years_in_us=3.0,
            years_in_country=2.0,  # ≤5 years → temporary
            us_citizen=True,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True
        assert result.fica_exempt is False  # paying US FICA, exempt from German SS

    def test_long_term_employee_fica_exempt(self):
        """Employee resident long-term in foreign country → covered by foreign system → FICA exempt."""
        req = TotalizationRequest(
            country="Germany",
            employment_type="employee",
            years_in_us=12.0,
            years_in_country=8.0,  # >5 years → permanent assignment
            us_citizen=True,
        )
        result = check_totalization(req)
        assert result.agreement_exists is True
        assert result.fica_exempt is True
        assert "Germany" in result.applicable_system or "country of employment" in result.applicable_system

    def test_agreement_countries_list_returned(self):
        """Result always includes full list of agreement countries."""
        req = TotalizationRequest(
            country="Japan",
            employment_type="employee",
            years_in_us=1.0,
            years_in_country=1.0,
            us_citizen=True,
        )
        result = check_totalization(req)
        assert isinstance(result.agreement_countries, list)
        assert len(result.agreement_countries) > 20  # we have ~30 countries
        assert "Germany" in result.agreement_countries
        assert "France" in result.agreement_countries

    def test_canonical_names_deduped(self):
        """No duplicate display names in the canonical list."""
        assert len(_CANONICAL_NAMES) == len(set(_CANONICAL_NAMES))


# ===========================================================================
# FBAR Penalties tests
# ===========================================================================


class TestFBARNonWillful:
    """Non-willful violation scenarios."""

    def test_non_willful_single_year(self):
        req = FBARPenaltyRequest(
            violation_type="non_willful",
            years_of_violation=1,
            max_account_balance=50_000.0,
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        assert result.max_penalty == pytest.approx(NON_WILLFUL_ADJUSTED_2024, rel=0.01)
        assert result.criminal_risk is False
        assert result.streamlined_eligible is False

    def test_non_willful_three_years(self):
        req = FBARPenaltyRequest(
            violation_type="non_willful",
            years_of_violation=3,
            max_account_balance=80_000.0,
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        assert result.max_penalty == pytest.approx(NON_WILLFUL_ADJUSTED_2024 * 3, rel=0.01)
        assert result.criminal_risk is False

    def test_non_willful_streamlined_voluntary(self):
        """Voluntary disclosure makes streamlined eligible."""
        req = FBARPenaltyRequest(
            violation_type="non_willful",
            years_of_violation=2,
            max_account_balance=200_000.0,
            filed_late=True,
            voluntary_disclosure=True,
        )
        result = calculate_fbar_penalties(req)
        assert result.streamlined_eligible is True
        expected_streamlined = 200_000.0 * STREAMLINED_PENALTY_PCT
        # min_penalty should reflect the streamlined amount
        assert result.min_penalty == pytest.approx(expected_streamlined, rel=0.01)


class TestFBARWillful:
    """Willful violation scenarios."""

    def test_willful_low_balance(self):
        """When balance × 50% < $100k, penalty is $100k/year floor."""
        req = FBARPenaltyRequest(
            violation_type="willful",
            years_of_violation=1,
            max_account_balance=100_000.0,  # 50% = $50k < $100k
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        assert result.max_penalty == pytest.approx(WILLFUL_BASE_MIN, rel=0.01)
        assert result.criminal_risk is False
        assert result.streamlined_eligible is False

    def test_willful_high_balance(self):
        """When balance × 50% > $100k, penalty scales with balance."""
        balance = 1_000_000.0
        req = FBARPenaltyRequest(
            violation_type="willful",
            years_of_violation=2,
            max_account_balance=balance,
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        expected = balance * 0.50 * 2
        assert result.max_penalty == pytest.approx(expected, rel=0.01)
        # high balance ≥ 1M triggers criminal risk flag
        assert result.criminal_risk is True

    def test_willful_voluntary_disclosure_reduces_penalty(self):
        req = FBARPenaltyRequest(
            violation_type="willful",
            years_of_violation=1,
            max_account_balance=300_000.0,
            filed_late=False,
            voluntary_disclosure=True,
        )
        result = calculate_fbar_penalties(req)
        assert result.min_penalty < result.max_penalty


class TestFBARFraud:
    """Fraud / criminal scenarios."""

    def test_fraud_criminal_risk(self):
        req = FBARPenaltyRequest(
            violation_type="fraud",
            years_of_violation=2,
            max_account_balance=500_000.0,
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        assert result.criminal_risk is True
        assert result.streamlined_eligible is False
        assert result.max_penalty == pytest.approx(FRAUD_MAX_FINE * 2, rel=0.01)
        assert "attorney" in result.recommendation.lower()

    def test_fraud_penalty_breakdown_has_items(self):
        req = FBARPenaltyRequest(
            violation_type="fraud",
            years_of_violation=1,
            max_account_balance=100_000.0,
            filed_late=True,
            voluntary_disclosure=False,
        )
        result = calculate_fbar_penalties(req)
        assert len(result.penalty_breakdown) >= 2
