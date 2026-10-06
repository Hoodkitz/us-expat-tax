"""
Form 3520 Foreign Gift & Trust Reporting Assistant Router.

POST /api/v1/form3520/filing-requirement  – JWT-protected: determine filing obligation
POST /api/v1/form3520/gift-calculator     – JWT-protected: calculate reportable gifts & penalty risk
POST /api/v1/form3520/trust-reporting     – JWT-protected: foreign trust beneficiary reporting
GET  /api/v1/form3520/overview            – static overview of Form 3520
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant

router = APIRouter(tags=["form3520"])

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

INDIVIDUAL_GIFT_THRESHOLD_USD = 100_000.0          # non-resident alien individuals
CORP_PARTNERSHIP_GIFT_THRESHOLD_USD = 16_815.0      # foreign corps / partnerships (inflation-adjusted)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

DonorType = Literal["INDIVIDUAL", "CORPORATION", "PARTNERSHIP"]


class FilingRequirementRequest(BaseModel):
    received_foreign_gifts_usd: float = Field(..., ge=0, examples=[120_000.0])
    received_from_foreign_person: bool = Field(..., examples=[True])
    received_from_foreign_corporation_or_partnership: bool = Field(..., examples=[False])
    is_beneficiary_of_foreign_trust: bool = Field(..., examples=[False])
    transferred_to_foreign_trust: bool = Field(..., examples=[False])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class GiftItem(BaseModel):
    donor_type: DonorType = Field(..., examples=["INDIVIDUAL"])
    amount_usd: float = Field(..., ge=0, examples=[50_000.0])
    date_received: str = Field(..., examples=["2024-06-15"])
    donor_country: str = Field(..., examples=["DE"])


class GiftCalculatorRequest(BaseModel):
    gifts: list[GiftItem] = Field(..., min_length=0)
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class TrustReportingRequest(BaseModel):
    trust_name: str = Field(..., min_length=1, examples=["Zurich Family Trust"])
    trust_country: str = Field(..., examples=["CH"])
    distributions_received_usd: float = Field(..., ge=0, examples=[25_000.0])
    is_grantor: bool = Field(..., examples=[False])
    is_beneficiary: bool = Field(..., examples=[True])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------

def _determine_filing_requirement(req: FilingRequirementRequest) -> dict:
    must_file = False
    reasons: list[str] = []

    # Individual foreign gifts
    if req.received_from_foreign_person and req.received_foreign_gifts_usd > INDIVIDUAL_GIFT_THRESHOLD_USD:
        must_file = True
        reasons.append(
            f"Received ${req.received_foreign_gifts_usd:,.2f} in gifts from a foreign individual, "
            f"exceeding the ${INDIVIDUAL_GIFT_THRESHOLD_USD:,.0f} threshold (IRC §6039F)."
        )

    # Corp / partnership gifts
    if req.received_from_foreign_corporation_or_partnership and req.received_foreign_gifts_usd > CORP_PARTNERSHIP_GIFT_THRESHOLD_USD:
        must_file = True
        reasons.append(
            f"Received ${req.received_foreign_gifts_usd:,.2f} in gifts from a foreign corporation or partnership, "
            f"exceeding the ${CORP_PARTNERSHIP_GIFT_THRESHOLD_USD:,.2f} inflation-adjusted threshold."
        )

    # Foreign trust beneficiary
    if req.is_beneficiary_of_foreign_trust:
        must_file = True
        reasons.append(
            "You are a beneficiary of a foreign trust; distributions must be reported on Form 3520 Part III."
        )

    # Transfer to foreign trust
    if req.transferred_to_foreign_trust:
        must_file = True
        reasons.append(
            "You transferred money or property to a foreign trust; reportable under Form 3520 Part I."
        )

    if not reasons:
        reasons.append("No Form 3520 filing obligation identified based on provided information.")

    applicable_thresholds = {
        "individual_foreign_gifts_usd": INDIVIDUAL_GIFT_THRESHOLD_USD,
        "corp_or_partnership_gifts_usd": CORP_PARTNERSHIP_GIFT_THRESHOLD_USD,
    }

    penalties_if_not_filed = (
        "Gifts: 5% of gift value per month not reported, up to 25% of the unreported amount (minimum $10,000). "
        "Trust distributions: greater of $10,000 or 35% of the gross reportable amount."
    )

    due_month = "April 15" if req.tax_year else "April 15"
    form_due_date = f"{due_month}, {req.tax_year + 1} (same as Form 1040; automatic extension to October 15 if Form 4868 filed)"

    return {
        "must_file": must_file,
        "applicable_thresholds": applicable_thresholds,
        "reasons": reasons,
        "penalties_if_not_filed": penalties_if_not_filed,
        "form_due_date": form_due_date,
    }


def _calculate_gifts(req: GiftCalculatorRequest) -> dict:
    individual_gifts: list[dict] = []
    corp_gifts: list[dict] = []  # CORPORATION + PARTNERSHIP

    for g in req.gifts:
        entry = {
            "donor_type": g.donor_type,
            "amount_usd": g.amount_usd,
            "date_received": g.date_received,
            "donor_country": g.donor_country,
        }
        if g.donor_type == "INDIVIDUAL":
            individual_gifts.append(entry)
        else:
            corp_gifts.append(entry)

    total_individual = sum(g["amount_usd"] for g in individual_gifts)
    total_corp = sum(g["amount_usd"] for g in corp_gifts)

    individual_required = total_individual > INDIVIDUAL_GIFT_THRESHOLD_USD
    corp_required = total_corp > CORP_PARTNERSHIP_GIFT_THRESHOLD_USD
    reporting_required = individual_required or corp_required

    # Penalty exposure: 5% per month up to 25% of unreported amount
    penalty_base = 0.0
    if individual_required:
        penalty_base += total_individual
    if corp_required:
        penalty_base += total_corp
    penalty_exposure_usd = round(penalty_base * 0.25, 2)  # max penalty (25%)

    return {
        "total_individual_gifts": round(total_individual, 2),
        "total_corp_gifts": round(total_corp, 2),
        "reporting_required": reporting_required,
        "gifts_by_category": {
            "individual": individual_gifts,
            "corporation_or_partnership": corp_gifts,
        },
        "penalty_exposure_usd": penalty_exposure_usd,
        "penalty_formula": (
            "5% of the unreported gift amount per month not reported, "
            "up to a maximum of 25% of the total unreported amount. "
            f"Individual threshold: ${INDIVIDUAL_GIFT_THRESHOLD_USD:,.0f}; "
            f"Corp/Partnership threshold: ${CORP_PARTNERSHIP_GIFT_THRESHOLD_USD:,.2f}."
        ),
    }


def _trust_reporting(req: TrustReportingRequest) -> dict:
    applicable_sections: list[str] = []
    recommendations: list[str] = []

    if req.is_grantor:
        applicable_sections.append("Part I: Transfers by U.S. Persons to Foreign Trusts")
        recommendations.append(
            "As a grantor, you must report any transfers to the foreign trust and provide ownership information."
        )

    if req.is_beneficiary:
        applicable_sections.append("Part III: Distributions from Foreign Trusts to U.S. Persons")
        if req.distributions_received_usd > 0:
            recommendations.append(
                f"Report ${req.distributions_received_usd:,.2f} in distributions received from {req.trust_name}."
            )

    if req.is_grantor or req.is_beneficiary:
        applicable_sections.append("Part II: U.S. Owners of Foreign Trusts (if applicable)")

    annual_report_requirement = req.distributions_received_usd > 0 or req.is_grantor

    reporting_required = req.is_grantor or req.is_beneficiary

    penalty_structure = (
        "Failure to report trust distributions: greater of $10,000 or 35% of the gross reportable amount. "
        "Failure to report as owner/grantor: $10,000 per violation per year, "
        "up to 25% of the trust asset value for continued non-compliance."
    )

    if not recommendations:
        recommendations.append(
            "No specific trust reporting obligations identified. "
            "Verify your grantor/beneficiary status with a qualified tax professional."
        )

    return {
        "reporting_required": reporting_required,
        "applicable_sections": applicable_sections,
        "annual_report_requirement": annual_report_requirement,
        "penalty_structure": penalty_structure,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filing-requirement")
async def filing_requirement(
    payload: FilingRequirementRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Determine whether a U.S. person must file Form 3520.
    Requires a valid JWT (Bearer token).
    """
    return _determine_filing_requirement(payload)


@router.post("/gift-calculator")
async def gift_calculator(
    payload: GiftCalculatorRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate reportable foreign gift amounts and penalty exposure.
    Requires a valid JWT (Bearer token).
    """
    return _calculate_gifts(payload)


@router.post("/trust-reporting")
async def trust_reporting(
    payload: TrustReportingRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Determine Form 3520 reporting requirements for foreign trust beneficiaries.
    Requires a valid JWT (Bearer token).
    """
    return _trust_reporting(payload)


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 3520 — no authentication required.
    """
    return {
        "form": "Form 3520",
        "title": "Annual Return To Report Transactions With Foreign Trusts and Receipt of Certain Foreign Gifts",
        "purpose": (
            "U.S. persons use Form 3520 to report: "
            "(1) certain transactions with foreign trusts, "
            "(2) ownership of foreign trusts, and "
            "(3) receipt of large gifts or bequests from foreign persons."
        ),
        "who_must_file": [
            "U.S. persons who receive more than $100,000 in gifts or bequests from a nonresident alien individual or foreign estate.",
            f"U.S. persons who receive more than ${CORP_PARTNERSHIP_GIFT_THRESHOLD_USD:,.2f} (inflation-adjusted) in gifts from foreign corporations or partnerships.",
            "U.S. persons who are treated as the owner of any part of a foreign trust (grantor rules).",
            "U.S. beneficiaries who receive distributions from a foreign trust.",
            "U.S. persons who transfer property to a foreign trust.",
        ],
        "key_thresholds": {
            "individual_or_estate_gifts_usd": INDIVIDUAL_GIFT_THRESHOLD_USD,
            "corp_or_partnership_gifts_usd_inflation_adjusted": CORP_PARTNERSHIP_GIFT_THRESHOLD_USD,
            "minimum_trust_penalty_usd": 10_000,
        },
        "penalties": {
            "gifts_not_reported": "5% of the gift value per month not reported, up to 25% of the unreported amount.",
            "trust_distribution_not_reported": "Greater of $10,000 or 35% of the gross reportable amount.",
            "grantor_trust_not_reported": "$10,000 per year for each year of non-compliance; up to 25% of trust asset value.",
        },
        "due_date": "Same as Form 1040 (April 15); automatic extension to October 15 if Form 4868 is filed.",
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-3520",
    }
