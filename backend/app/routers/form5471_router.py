"""
Form 5471 CFC Reporting Assistant Router.

POST /api/v1/form5471/filing-requirement  – JWT-protected: determine Form 5471 filing obligation
POST /api/v1/form5471/income-calculation  – JWT-protected: combined Subpart F + GILTI income calculation
POST /api/v1/form5471/subpart-f-income    – JWT-protected: calculate Subpart F income inclusions
POST /api/v1/form5471/gilti-calculator    – JWT-protected: GILTI inclusion calculator
GET  /api/v1/form5471/overview            – static overview of Form 5471 / CFC rules
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.utils import get_current_tenant
from app.modules.form5471 import (
    BASE_PENALTY_USD,
    CATEGORY_DESCRIPTIONS,
    CONTINUATION_PENALTY_PER_30_DAYS,
    GILTI_HIGH_TAX_THRESHOLD_PCT,
    MAX_CONTINUATION_PENALTIES,
    FilingRequirementRequest,
    GiltiCalculatorRequest,
    IncomeCalculationRequest,
    SubpartFIncomeRequest,
    calculate_gilti,
    calculate_income,
    calculate_subpart_f,
    determine_filing_requirement,
)

router = APIRouter(tags=["form5471"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/filing-requirement")
async def filing_requirement(
    payload: FilingRequirementRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Determine whether a U.S. person must file Form 5471.
    Requires a valid JWT (Bearer token).
    """
    return determine_filing_requirement(payload)


@router.post("/income-calculation")
async def income_calculation(
    payload: IncomeCalculationRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Combined income calculation: Subpart F + GILTI inclusion.
    Requires a valid JWT (Bearer token).
    """
    return calculate_income(payload)


@router.post("/subpart-f-income")
async def subpart_f_income(
    payload: SubpartFIncomeRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate Subpart F income inclusions for a CFC.
    Requires a valid JWT (Bearer token).
    """
    return calculate_subpart_f(payload)


@router.post("/gilti-calculator")
async def gilti_calculator(
    payload: GiltiCalculatorRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate GILTI inclusion amount under IRC §951A.
    Requires a valid JWT (Bearer token).
    """
    return calculate_gilti(payload)


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 5471 and CFC rules — no authentication required.
    """
    return {
        "form": "Form 5471",
        "title": "Information Return of U.S. Persons With Respect to Certain Foreign Corporations",
        "irc_section": "IRC §6038",
        "purpose": (
            "U.S. persons with interests in or control over certain foreign corporations must file "
            "Form 5471 to report ownership, transactions, and income. The form encompasses "
            "Controlled Foreign Corporation (CFC) reporting including Subpart F income (IRC §951) "
            "and GILTI (IRC §951A, added by the Tax Cuts and Jobs Act of 2017)."
        ),
        "categories_of_filers": CATEGORY_DESCRIPTIONS,
        "key_concepts": {
            "CFC": (
                "A Controlled Foreign Corporation is a foreign corporation where U.S. shareholders "
                "(each owning ≥10%) collectively own more than 50% of the vote or value on any day "
                "during the tax year (IRC §957)."
            ),
            "Subpart_F": (
                "Subpart F income (IRC §951-§965) is certain passive or mobile income earned by CFCs "
                "that is included in U.S. shareholders' gross income in the year earned, "
                "regardless of actual distribution."
            ),
            "GILTI": (
                "Global Intangible Low-Taxed Income (IRC §951A) is a minimum tax on CFC income in excess "
                "of a 10% return on qualified business asset investment (QBAI). Added by TCJA 2017."
            ),
        },
        "penalties": {
            "initial_failure_to_file": f"${BASE_PENALTY_USD:,} per annual accounting period per CFC.",
            "continuation_penalty": (
                f"${CONTINUATION_PENALTY_PER_30_DAYS:,} per 30-day period (up to "
                f"{MAX_CONTINUATION_PENALTIES} periods = up to $60,000 total) after 90-day IRS notice."
            ),
            "willful_failure": "Criminal penalties may apply under IRC §7203.",
            "reduction_of_foreign_tax_credits": (
                "10% reduction in foreign tax credits for each year Form 5471 is not filed (IRC §6038(c))."
            ),
        },
        "due_date": (
            "Same as the filer's income tax return (April 15 for individuals; March 15 for calendar-year "
            "corporations); automatic extensions apply if the underlying return is extended."
        ),
        "gilti_high_tax_threshold_pct": GILTI_HIGH_TAX_THRESHOLD_PCT,
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-5471",
    }
