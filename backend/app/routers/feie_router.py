"""
Form 2555 FEIE API Router.
POST /api/v1/feie/calculate  – JWT-protected full calculation
POST /api/v1/feie/check-eligibility – public eligibility pre-check
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.feie import FEIEInput, calculate_feie, check_feie_eligibility

router = APIRouter(tags=["feie"])

FilingStatusLiteral = Literal[
    "single",
    "married_filing_jointly",
    "married_filing_separately",
]


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FEIECalculateRequest(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    foreign_earned_income: float = Field(..., ge=0, examples=[100_000.0])
    housing_costs: float = Field(0.0, ge=0, examples=[24_000.0])
    days_in_foreign_country: int = Field(..., ge=0, le=366, examples=[335])
    bona_fide_resident: bool = Field(False, examples=[False])
    filing_status: FilingStatusLiteral = Field("single", examples=["single"])
    employer_provided_housing: float = Field(0.0, ge=0, examples=[0.0])


class EligibilityCheckRequest(BaseModel):
    days_outside_us: int = Field(..., ge=0, le=366, examples=[335])
    bona_fide_resident: bool = Field(False, examples=[False])
    us_citizen_or_green_card: bool = Field(True, examples=[True])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate")
async def feie_calculate(
    payload: FEIECalculateRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate FEIE and housing exclusion amounts for Form 2555.
    Requires a valid JWT (Bearer token).
    """
    inp = FEIEInput(
        tax_year=payload.tax_year,
        foreign_earned_income=payload.foreign_earned_income,
        housing_costs=payload.housing_costs,
        days_in_foreign_country=payload.days_in_foreign_country,
        bona_fide_resident=payload.bona_fide_resident,
        filing_status=payload.filing_status,
        employer_provided_housing=payload.employer_provided_housing,
    )
    result = calculate_feie(inp)
    return {
        "qualifies_pp": result.qualifies_pp,
        "qualifies_bfr": result.qualifies_bfr,
        "qualifies": result.qualifies,
        "feie_limit": result.feie_limit,
        "feie_exclusion": result.feie_exclusion,
        "housing_exclusion": result.housing_exclusion,
        "housing_base_amount": result.housing_base_amount,
        "total_exclusion": result.total_exclusion,
        "taxable_income_estimate": result.taxable_income_estimate,
        "form_2555_required": result.form_2555_required,
        "notes": result.notes,
    }


@router.post("/check-eligibility")
async def feie_check_eligibility(payload: EligibilityCheckRequest) -> dict:
    """
    Quick eligibility pre-check – no JWT required.
    Returns eligible, test_passed, and a human-readable reason.
    """
    return check_feie_eligibility(
        days_outside_us=payload.days_outside_us,
        bona_fide_resident=payload.bona_fide_resident,
        us_citizen_or_green_card=payload.us_citizen_or_green_card,
    )
