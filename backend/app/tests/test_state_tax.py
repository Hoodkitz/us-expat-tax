"""
Tests for State Tax Filing Obligations helper.
Pure unit tests — no HTTP client or JWT required.
"""
from __future__ import annotations

import pytest

from app.modules.state_tax import (
    ObligationsRequest,
    DomicileAnalysisRequest,
    analyze_obligations,
    analyze_domicile,
    list_states,
    STATE_DATA,
    HIGH_RISK_STATES,
    NO_INCOME_TAX_STATES,
    CA_SAFE_HARBOR_DAYS,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def make_obligations(
    state: str = "TX",
    days_in_state: int = 30,
    domicile_state: str = "TX",
    income_source: str = "employment",
    moved_abroad_year: int = 2022,
    maintained_home: bool = False,
    driver_license_state: str | None = None,
    voter_reg_state: str | None = None,
) -> ObligationsRequest:
    return ObligationsRequest(
        state=state,
        days_in_state=days_in_state,
        domicile_state=domicile_state,
        income_source=income_source,
        moved_abroad_year=moved_abroad_year,
        maintained_home=maintained_home,
        driver_license_state=driver_license_state,
        voter_reg_state=voter_reg_state,
    )


def make_domicile(
    original_state: str = "CA",
    years_abroad: float = 3.0,
    maintained_home: bool = False,
    voter_registered: bool = False,
    driver_license: bool = False,
    bank_accounts: bool = False,
    family_in_state: bool = False,
    return_days: int = 10,
    intent_to_return: bool = False,
    business_ties: bool = False,
    vehicle_registered: bool = False,
) -> DomicileAnalysisRequest:
    return DomicileAnalysisRequest(
        original_state=original_state,
        years_abroad=years_abroad,
        maintained_home=maintained_home,
        voter_registered_in_state=voter_registered,
        driver_license_in_state=driver_license,
        bank_accounts_in_state=bank_accounts,
        family_in_state=family_in_state,
        returned_to_state_days_per_year=return_days,
        intent_to_return=intent_to_return,
        business_ties_in_state=business_ties,
        vehicle_registered_in_state=vehicle_registered,
    )


# ===========================================================================
# test_states_endpoint_returns_50
# ===========================================================================

def test_states_endpoint_returns_50():
    """list_states() must return exactly 50 entries."""
    states = list_states()
    assert len(states) == 50


# ===========================================================================
# test_no_tax_state_florida
# ===========================================================================

def test_no_tax_state_florida():
    """Florida has no income tax — filing_required must be False."""
    result = analyze_obligations(make_obligations(state="FL", domicile_state="FL", days_in_state=200))
    assert result.filing_required is False
    assert result.nexus_type == "none"
    assert "no state income tax" in result.reason.lower()


# ===========================================================================
# test_california_safe_harbor
# ===========================================================================

def test_california_safe_harbor():
    """CA safe harbor is 546 days over 2 years (not the standard 183)."""
    state_data = STATE_DATA["CA"]
    assert state_data["safe_harbor_days"] == CA_SAFE_HARBOR_DAYS
    assert CA_SAFE_HARBOR_DAYS == 546

    # Below safe harbor, no domicile, no maintained home → nonresident or none
    result = analyze_obligations(
        make_obligations(state="CA", domicile_state="TX", days_in_state=100, maintained_home=False)
    )
    # CA still taxes source income but nexus is nonresident or none
    assert result.nexus_type in ("nonresident", "none")
    assert result.safe_harbor_days == 546


# ===========================================================================
# test_new_york_statutory_resident
# ===========================================================================

def test_new_york_statutory_resident():
    """NY 183+ days + maintained home = statutory_resident even without domicile."""
    result = analyze_obligations(
        make_obligations(
            state="NY",
            domicile_state="FL",
            days_in_state=200,
            maintained_home=True,
        )
    )
    assert result.filing_required is True
    assert result.nexus_type == "statutory_resident"
    assert "183" in result.reason or "permanent place of abode" in result.reason.lower()


# ===========================================================================
# test_domicile_analysis_abandoned
# ===========================================================================

def test_domicile_analysis_abandoned():
    """Clear domicile abandonment scenario: no ties to original state."""
    result = analyze_domicile(make_domicile(
        original_state="NY",
        years_abroad=4.0,
        maintained_home=False,
        voter_registered=False,
        driver_license=False,
        bank_accounts=False,
        family_in_state=False,
        return_days=5,
        intent_to_return=False,
        business_ties=False,
        vehicle_registered=False,
    ))
    assert result.domicile_abandoned is True
    assert result.risk_score < 40
    assert len(result.factors_for) > 0


# ===========================================================================
# test_domicile_analysis_retained
# ===========================================================================

def test_domicile_analysis_retained():
    """Strong retained domicile: home, voter, license, family, intent."""
    result = analyze_domicile(make_domicile(
        original_state="CA",
        years_abroad=1.0,
        maintained_home=True,
        voter_registered=True,
        driver_license=True,
        bank_accounts=True,
        family_in_state=True,
        return_days=90,
        intent_to_return=True,
        business_ties=True,
        vehicle_registered=True,
    ))
    assert result.domicile_abandoned is False
    assert result.risk_score >= 40
    assert len(result.factors_against) > 0


# ===========================================================================
# test_obligations_no_filing_required
# ===========================================================================

def test_obligations_no_filing_required():
    """No domicile, few days, investment income, no maintained home → no filing."""
    result = analyze_obligations(
        make_obligations(
            state="CO",
            domicile_state="TX",
            days_in_state=30,
            income_source="investment",
            maintained_home=False,
        )
    )
    assert result.filing_required is False
    assert result.nexus_type == "none"


# ===========================================================================
# test_obligations_filing_required
# ===========================================================================

def test_obligations_filing_required():
    """Domicile in a tax state → filing required."""
    result = analyze_obligations(
        make_obligations(state="IL", domicile_state="IL", days_in_state=10)
    )
    assert result.filing_required is True
    assert result.nexus_type == "domicile"


# ===========================================================================
# test_high_risk_california
# ===========================================================================

def test_high_risk_california():
    """CA is in HIGH_RISK_STATES and must produce warning flags."""
    assert "CA" in HIGH_RISK_STATES
    result = analyze_obligations(
        make_obligations(
            state="CA",
            domicile_state="CA",
            days_in_state=100,
            maintained_home=True,
        )
    )
    assert result.filing_required is True
    assert len(result.warning_flags) > 0
    # Must mention CA FTB / aggressive
    combined = " ".join(result.warning_flags + result.recommendations).lower()
    assert "california" in combined or "ftb" in combined or "ca" in combined


# ===========================================================================
# test_safe_harbor_days_remaining
# ===========================================================================

def test_safe_harbor_days_remaining():
    """days_remaining_safe_harbor must equal safe_harbor_days minus days_in_state."""
    days = 80
    result = analyze_obligations(
        make_obligations(state="OH", domicile_state="TX", days_in_state=days)
    )
    state_safe_harbor = STATE_DATA["OH"]["safe_harbor_days"]
    assert result.days_remaining_safe_harbor == max(0, state_safe_harbor - days)


# ===========================================================================
# test_warning_flags_present
# ===========================================================================

def test_warning_flags_present():
    """Driver license in same state must generate a warning flag."""
    result = analyze_obligations(
        make_obligations(
            state="NJ",
            domicile_state="TX",
            days_in_state=50,
            driver_license_state="NJ",
        )
    )
    combined = " ".join(result.warning_flags).lower()
    assert "driver" in combined or "license" in combined


# ===========================================================================
# test_texas_no_income_tax
# ===========================================================================

def test_texas_no_income_tax():
    """Texas has no income tax — must be in NO_INCOME_TAX_STATES."""
    assert "TX" in NO_INCOME_TAX_STATES
    result = analyze_obligations(make_obligations(state="TX", domicile_state="TX", days_in_state=365))
    assert result.filing_required is False
    assert result.nexus_type == "none"


# ===========================================================================
# test_all_states_present_in_data
# ===========================================================================

def test_all_states_present_in_data():
    """STATE_DATA must have exactly 50 entries covering all US states."""
    assert len(STATE_DATA) == 50
    # Spot-check a few key states
    for code in ["CA", "NY", "TX", "FL", "AK", "WY"]:
        assert code in STATE_DATA, f"{code} missing from STATE_DATA"
