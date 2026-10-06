"""
IRS Streamlined Filing Compliance Procedures Router.
Rev. Proc. 2014-55 + updated 2019 guidance.

POST /api/v1/streamlined/eligibility         – Determine SFOP or SDOP qualification
POST /api/v1/streamlined/penalty-calculation – SDOP miscellaneous offshore penalty
GET  /api/v1/streamlined/overview            – Procedure summary & key facts
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant

router = APIRouter(tags=["streamlined"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class EligibilityRequest(BaseModel):
    """Inputs needed to assess Streamlined Filing eligibility."""

    days_in_us_per_year: list[int] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Number of days present in the US for each of the last 3 calendar years (oldest→newest).",
        examples=[[30, 25, 20]],
    )
    had_filing_requirement: bool = Field(
        ...,
        description="Taxpayer had a US filing requirement during the unreported years.",
    )
    filed_returns: bool = Field(
        ...,
        description="Taxpayer already filed US tax returns for the relevant years.",
    )
    filed_fbars: bool = Field(
        ...,
        description="Taxpayer filed required FBARs (FinCEN 114) for the relevant years.",
    )
    is_willful: bool = Field(
        ...,
        description="Non-compliance was willful (disqualifies from both procedures).",
    )
    account_balance_usd: float = Field(
        ...,
        ge=0,
        description="Highest aggregate foreign account balance in USD (for SDOP penalty base).",
        examples=[150000.0],
    )
    years_unreported: int = Field(
        ...,
        ge=0,
        le=50,
        description="Number of years with unreported foreign income/accounts.",
        examples=[3],
    )


class PenaltyCalculationRequest(BaseModel):
    """Inputs for SDOP miscellaneous offshore penalty calculation."""

    account_balances_by_year: dict[str, float] = Field(
        ...,
        description="Map of tax year (str) to highest aggregate foreign account balance in USD.",
        examples=[{"2021": 120000.0, "2022": 150000.0, "2023": 130000.0}],
    )
    years: list[str] = Field(
        ...,
        description="List of tax years to analyze (must match keys in account_balances_by_year).",
        examples=[["2021", "2022", "2023"]],
    )


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------

_SFOP_STEPS = [
    "Certify non-willful conduct on Form 14653 (Certification by U.S. Person Residing Outside of the United States).",
    "File amended/original tax returns for the 3 most recent tax years with all required information returns (Forms 8938, 5471, etc.).",
    "File delinquent or amended FBARs (FinCEN 114) for the 6 most recent FBAR periods.",
    "Pay all taxes and interest shown on amended returns.",
    "No miscellaneous offshore penalty applies under SFOP.",
    "Submit all documents to the IRS address specified for Streamlined Foreign Offshore Procedures.",
]

_SDOP_STEPS = [
    "Certify non-willful conduct on Form 14654 (Certification by U.S. Person Residing in the United States).",
    "File amended/original tax returns for the 3 most recent tax years with all required information returns.",
    "File delinquent or amended FBARs (FinCEN 114) for the 6 most recent FBAR periods.",
    "Pay all taxes and interest shown on amended returns.",
    "Pay 5% miscellaneous offshore penalty on the highest aggregate balance of unreported foreign assets.",
    "Submit all documents to the IRS address specified for Streamlined Domestic Offshore Procedures.",
]


def _is_nonresident(days_in_us: list[int]) -> bool:
    """
    SFOP non-residency test: taxpayer must NOT have been present in the US
    for more than 35 days in ANY of the 3 preceding calendar years.
    IRC § 7701(b) / Rev. Proc. 2014-55 §4.01.
    """
    return all(d <= 35 for d in days_in_us)


def _assess_eligibility(req: EligibilityRequest) -> dict:
    warnings: list[str] = []

    # Willfulness is an absolute bar for both procedures
    if req.is_willful:
        return {
            "qualifies_sfop": False,
            "qualifies_sdop": False,
            "procedure": "none",
            "penalty_rate": 0.0,
            "estimated_penalty_usd": 0.0,
            "required_returns": 3,
            "required_fbars": 6,
            "non_willful_certification_required": False,
            "steps": [],
            "revenue_procedure": "Rev. Proc. 2014-55",
            "warnings": [
                "Willful non-compliance is NOT eligible for either Streamlined procedure. "
                "Consult an attorney; Offshore Voluntary Disclosure Program (OVDP) may apply."
            ],
        }

    non_resident = _is_nonresident(req.days_in_us_per_year)

    qualifies_sfop = non_resident and not req.is_willful
    qualifies_sdop = (not non_resident) and not req.is_willful

    if req.filed_returns and req.filed_fbars:
        warnings.append(
            "Returns and FBARs already filed: Streamlined procedures still allow amendments "
            "but ensure unreported income/accounts are the basis for the submission."
        )

    if not req.had_filing_requirement:
        warnings.append(
            "If no filing requirement existed, consult a tax professional — "
            "Streamlined eligibility may not be necessary."
        )

    if qualifies_sfop:
        procedure = "SFOP"
        penalty_rate = 0.0
        estimated_penalty = 0.0
        steps = _SFOP_STEPS
    elif qualifies_sdop:
        procedure = "SDOP"
        penalty_rate = 0.05
        estimated_penalty = round(req.account_balance_usd * penalty_rate, 2)
        steps = _SDOP_STEPS
    else:
        procedure = "none"
        penalty_rate = 0.0
        estimated_penalty = 0.0
        steps = []
        warnings.append("Unable to determine qualification. Please verify residency status.")

    return {
        "qualifies_sfop": qualifies_sfop,
        "qualifies_sdop": qualifies_sdop,
        "procedure": procedure,
        "penalty_rate": penalty_rate,
        "estimated_penalty_usd": estimated_penalty,
        "required_returns": 3,
        "required_fbars": 6,
        "non_willful_certification_required": qualifies_sfop or qualifies_sdop,
        "steps": steps,
        "revenue_procedure": "Rev. Proc. 2014-55",
        "warnings": warnings,
    }


def _calculate_penalty(req: PenaltyCalculationRequest) -> dict:
    balances = {yr: req.account_balances_by_year.get(yr, 0.0) for yr in req.years}
    highest = max(balances.values()) if balances else 0.0
    penalty_rate = 0.05
    penalty_amount = round(highest * penalty_rate, 2)

    return {
        "highest_aggregate_balance": highest,
        "penalty_rate": penalty_rate,
        "penalty_amount": penalty_amount,
        "years_analyzed": req.years,
        "explanation": (
            f"SDOP miscellaneous offshore penalty is 5% of the highest aggregate balance "
            f"of unreported foreign financial assets. Highest balance across analyzed years "
            f"({', '.join(req.years)}): ${highest:,.2f}. "
            f"Penalty: 5% × ${highest:,.2f} = ${penalty_amount:,.2f}."
        ),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/eligibility")
async def check_eligibility(
    payload: EligibilityRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Determine whether a taxpayer qualifies for the Streamlined Foreign
    Offshore Procedure (SFOP) or Streamlined Domestic Offshore Procedure
    (SDOP) per Rev. Proc. 2014-55.
    Requires a valid JWT.
    """
    return _assess_eligibility(payload)


@router.post("/penalty-calculation")
async def penalty_calculation(
    payload: PenaltyCalculationRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate the SDOP 5% miscellaneous offshore penalty based on the
    highest aggregate foreign financial asset balance across specified years.
    Requires a valid JWT.
    """
    return _calculate_penalty(payload)


@router.get("/overview")
async def streamlined_overview() -> dict:
    """
    Public overview of IRS Streamlined Filing Compliance Procedures.
    No authentication required.
    """
    return {
        "title": "IRS Streamlined Filing Compliance Procedures",
        "authority": "Rev. Proc. 2014-55 (updated 2019 guidance)",
        "purpose": (
            "Provide US taxpayers with a simplified method to correct "
            "unintentional failures to report foreign financial assets and pay "
            "associated tax. Available only for NON-WILLFUL non-compliance."
        ),
        "procedures": {
            "SFOP": {
                "name": "Streamlined Foreign Offshore Procedures",
                "eligibility": [
                    "US citizen, lawful permanent resident, or person meeting the substantial presence test.",
                    "Was NOT present in the US for more than 35 days in ANY of the 3 most recent tax years.",
                    "Non-willful conduct certified on Form 14653.",
                ],
                "requirements": {
                    "amended_returns": 3,
                    "fbar_periods": 6,
                    "penalty": "No miscellaneous offshore penalty (0%).",
                    "taxes_and_interest": "Full payment of back taxes and interest required.",
                },
                "certification_form": "Form 14653",
            },
            "SDOP": {
                "name": "Streamlined Domestic Offshore Procedures",
                "eligibility": [
                    "US citizen, lawful permanent resident, or person meeting the substantial presence test.",
                    "Does NOT meet the SFOP non-residency test (present >35 days/year in at least one year).",
                    "Non-willful conduct certified on Form 14654.",
                ],
                "requirements": {
                    "amended_returns": 3,
                    "fbar_periods": 6,
                    "penalty": "5% miscellaneous offshore penalty on highest aggregate foreign account balance.",
                    "taxes_and_interest": "Full payment of back taxes and interest required.",
                },
                "certification_form": "Form 14654",
            },
        },
        "disqualifying_factors": [
            "Willful non-compliance.",
            "Currently under IRS civil examination or criminal investigation.",
            "Previously opted into OVDP (Offshore Voluntary Disclosure Program).",
        ],
        "key_facts": [
            "Streamlined procedures provide protection from penalties normally applicable to delinquent returns.",
            "SFOP participants pay zero offshore penalty; SDOP participants pay 5%.",
            "Both procedures require 3 years of amended returns and 6 years of FBARs.",
            "Submission does not close an audit; IRS retains right to examine returns.",
            "Non-willful certification must be accurate — false statements carry serious penalties.",
        ],
        "irs_resources": [
            "https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures",
            "https://www.irs.gov/pub/irs-pdf/f14653.pdf",
            "https://www.irs.gov/pub/irs-pdf/f14654.pdf",
        ],
    }
