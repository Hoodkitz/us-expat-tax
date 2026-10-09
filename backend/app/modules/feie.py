"""
Form 2555 – Foreign Earned Income Exclusion (FEIE) calculation module.
Pure deterministic logic, no HTTP dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# IRS FEIE limits per tax year (IRC §911(b)(2)(D)(i))
FEIE_LIMITS: dict[int, float] = {
    2020: 107_600.0,
    2021: 108_700.0,
    2022: 112_000.0,
    2023: 120_000.0,
    2024: 126_500.0,
}
DEFAULT_FEIE_LIMIT = 126_500.0

FilingStatus = Literal[
    "single",
    "married_filing_jointly",
    "married_filing_separately",
]


@dataclass
class FEIEInput:
    tax_year: int
    foreign_earned_income: float
    housing_costs: float
    days_in_foreign_country: int
    bona_fide_resident: bool
    filing_status: FilingStatus
    employer_provided_housing: float = 0.0


@dataclass
class FEIEResult:
    qualifies_pp: bool
    qualifies_bfr: bool
    qualifies: bool
    feie_limit: float
    feie_exclusion: float
    housing_exclusion: float
    housing_base_amount: float
    total_exclusion: float
    taxable_income_estimate: float
    form_2555_required: bool
    notes: list[str] = field(default_factory=list)


def calculate_feie(inp: FEIEInput) -> FEIEResult:
    """
    Compute FEIE and housing exclusion amounts for Form 2555.

    Physical Presence Test: ≥ 330 full days in a foreign country
    during any 12-month period.
    Bona Fide Residence Test: bona_fide_resident flag (taxpayer's
    own assertion, must be verified with IRS Form 2555 Part II).
    """
    notes: list[str] = []

    # Qualification tests
    qualifies_pp = inp.days_in_foreign_country >= 330
    qualifies_bfr = inp.bona_fide_resident
    qualifies = qualifies_pp or qualifies_bfr

    feie_limit = FEIE_LIMITS.get(inp.tax_year, DEFAULT_FEIE_LIMIT)

    if not qualifies:
        notes.append(
            "Neither the Physical Presence Test (≥330 days) nor the "
            "Bona Fide Residence Test was met. No exclusion applies."
        )
        return FEIEResult(
            qualifies_pp=qualifies_pp,
            qualifies_bfr=qualifies_bfr,
            qualifies=False,
            feie_limit=feie_limit,
            feie_exclusion=0.0,
            housing_exclusion=0.0,
            housing_base_amount=0.0,
            total_exclusion=0.0,
            taxable_income_estimate=max(0.0, inp.foreign_earned_income),
            form_2555_required=False,
            notes=notes,
        )

    # FEIE exclusion (capped at annual limit)
    feie_exclusion = min(inp.foreign_earned_income, feie_limit)

    # Housing exclusion (IRC §911(c))
    # Base amount = 16% of the FEIE limit
    housing_base = feie_limit * 0.16
    # Max housing exclusion = 30% of FEIE limit (simplified; actual limits
    # vary by location but 30% is the statutory ceiling before location
    # adjustments)
    housing_ceiling = feie_limit * 0.30
    net_housing_costs = inp.housing_costs - inp.employer_provided_housing
    housing_exclusion = max(
        0.0, min(net_housing_costs - housing_base, housing_ceiling)
    ) if qualifies else 0.0

    # Total exclusion cannot exceed foreign earned income
    total_exclusion = min(inp.foreign_earned_income, feie_exclusion + housing_exclusion)
    taxable_income_estimate = max(0.0, inp.foreign_earned_income - total_exclusion)

    # Notes / warnings
    if qualifies_pp and qualifies_bfr:
        notes.append(
            "Both Physical Presence Test and Bona Fide Residence Test met. "
            "You may choose either on Form 2555."
        )
    elif qualifies_pp:
        notes.append("Qualified via Physical Presence Test (≥330 days abroad).")
    else:
        notes.append("Qualified via Bona Fide Residence Test.")

    if inp.foreign_earned_income > feie_limit:
        notes.append(
            f"Foreign earned income (${inp.foreign_earned_income:,.2f}) exceeds the "
            f"{inp.tax_year} FEIE limit (${feie_limit:,.2f}). "
            f"Excess ${inp.foreign_earned_income - feie_limit:,.2f} remains taxable."
        )

    if inp.tax_year not in FEIE_LIMITS:
        notes.append(
            f"Tax year {inp.tax_year} is not in the pre-loaded limit table; "
            f"default limit ${DEFAULT_FEIE_LIMIT:,.2f} used. Verify with IRS Publication 54."
        )

    if inp.filing_status == "married_filing_separately":
        notes.append(
            "Married Filing Separately: each spouse claims their own FEIE "
            "independently. Community property rules may apply."
        )

    if housing_exclusion > 0:
        notes.append(
            "Housing exclusion claimed. Attach Form 2555 Part VII. "
            "Location-specific housing limits (IRS Notice 2024-18 or current year) "
            "may further reduce the housing exclusion."
        )

    return FEIEResult(
        qualifies_pp=qualifies_pp,
        qualifies_bfr=qualifies_bfr,
        qualifies=qualifies,
        feie_limit=feie_limit,
        feie_exclusion=feie_exclusion,
        housing_exclusion=housing_exclusion,
        housing_base_amount=housing_base,
        total_exclusion=total_exclusion,
        taxable_income_estimate=taxable_income_estimate,
        form_2555_required=True,
        notes=notes,
    )


def check_feie_eligibility(
    days_outside_us: int,
    bona_fide_resident: bool,
    us_citizen_or_green_card: bool,
) -> dict:
    """
    Quick eligibility pre-check before running the full calculation.
    Returns eligible flag, which test passed, and a plain-language reason.
    """
    if not us_citizen_or_green_card:
        return {
            "eligible": False,
            "test_passed": "none",
            "reason": (
                "FEIE is only available to U.S. citizens and lawful permanent "
                "residents (green card holders). Non-resident aliens do not qualify."
            ),
        }

    passes_pp = days_outside_us >= 330
    passes_bfr = bona_fide_resident

    if passes_pp and passes_bfr:
        return {
            "eligible": True,
            "test_passed": "physical_presence",
            "reason": (
                f"Both tests passed. Physical Presence Test: {days_outside_us} days "
                "outside the US (≥330 required). Bona Fide Residence Test also met."
            ),
        }
    if passes_pp:
        return {
            "eligible": True,
            "test_passed": "physical_presence",
            "reason": (
                f"Physical Presence Test passed: {days_outside_us} days outside "
                "the US (≥330 required)."
            ),
        }
    if passes_bfr:
        return {
            "eligible": True,
            "test_passed": "bona_fide_residence",
            "reason": (
                "Bona Fide Residence Test passed. You established bona fide "
                "residence in a foreign country."
            ),
        }

    return {
        "eligible": False,
        "test_passed": "none",
        "reason": (
            f"Neither test passed. Physical Presence Test requires ≥330 days "
            f"outside the US (you had {days_outside_us}). "
            "Bona Fide Residence Test was not asserted."
        ),
    }
