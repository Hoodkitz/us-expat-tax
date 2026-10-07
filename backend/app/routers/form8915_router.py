"""
Form 8915 — Qualified Disaster Retirement Plan Distributions and Repayments.

POST /api/v1/form8915/filing-requirement – JWT-protected: check eligibility
POST /api/v1/form8915/repayment-schedule  – JWT-protected: calculate repayment schedule
POST /api/v1/form8915/penalty-waiver      – JWT-protected: check penalty waiver
GET  /api/v1/form8915/overview             – public: static overview of Form 8915
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8915 import (
    FilingRequirementInput,
    RepaymentScheduleInput,
    PenaltyWaiverInput,
    check_filing_requirement,
    calculate_repayment_schedule,
    check_penalty_waiver,
    MAX_DISTRIBUTION_LIMIT,
    EARLY_WITHDRAWAL_PENALTY_RATE,
    STANDARD_REPAYMENT_YEARS,
    QUALIFIED_DISASTER_TYPES,
)

router = APIRouter(tags=["form8915"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FilingRequirementRequest(BaseModel):
    """Request to check filing requirement eligibility."""
    disaster_area: str = Field(
        ..., 
        examples=["Hurricane Ian, Florida"], 
        description="Disaster area or disaster type"
    )
    distribution_date: str = Field(
        ..., 
        examples=["2024-09-28"], 
        description="Distribution date in YYYY-MM-DD format"
    )
    home_destroyed: bool = Field(
        default=False, 
        examples=[True], 
        description="Was principal residence destroyed?"
    )
    economic_loss_amt: str = Field(
        ..., 
        examples=["50000.00"], 
        description="Economic loss amount in USD"
    )


class RepaymentScheduleRequest(BaseModel):
    """Request to calculate repayment schedule."""
    distribution_amt: str = Field(
        ..., 
        examples=["75000.00"], 
        description="Distribution amount in USD"
    )
    repayment_years: int = Field(
        default=3, 
        ge=1, 
        le=3, 
        examples=[3], 
        description="Number of years to repay (max 3)"
    )


class PenaltyWaiverRequest(BaseModel):
    """Request to check penalty waiver."""
    age: int = Field(
        ..., 
        ge=18, 
        le=100, 
        examples=[45], 
        description="Taxpayer age"
    )
    distribution_amt: str = Field(
        ..., 
        examples=["60000.00"], 
        description="Distribution amount in USD"
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filing-requirement")
async def filing_requirement(
    payload: FilingRequirementRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Check if taxpayer is eligible for qualified disaster distribution treatment
    under IRC §72(t)(2)(G) and §1400Q.
    
    Requires a valid JWT (Bearer token).
    """
    try:
        economic_loss = Decimal(payload.economic_loss_amt)
    except Exception as e:
        return {"error": f"Invalid economic_loss_amt: {e}"}
    
    inp = FilingRequirementInput(
        disaster_area=payload.disaster_area,
        distribution_date=payload.distribution_date,
        home_destroyed=payload.home_destroyed,
        economic_loss_amt=economic_loss,
    )
    
    result = check_filing_requirement(inp)
    
    return {
        "eligible": result.eligible,
        "disaster_type": result.disaster_type,
        "distribution_within_window": result.distribution_within_window,
        "economic_loss_threshold_met": result.economic_loss_threshold_met,
        "max_distribution_limit": str(result.max_distribution_limit),
        "explanation": result.explanation,
    }


@router.post("/repayment-schedule")
async def repayment_schedule(
    payload: RepaymentScheduleRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate the 3-year repayment schedule for a qualified disaster distribution.
    
    Under IRC §1400Q:
    - Taxpayer has 3 years to repay the distribution
    - If NOT repaid, income is spread equally over 3 years (1/3 per year)
    - No 10% early withdrawal penalty applies
    
    Requires a valid JWT (Bearer token).
    """
    try:
        distribution = Decimal(payload.distribution_amt)
    except Exception as e:
        return {"error": f"Invalid distribution_amt: {e}"}
    
    inp = RepaymentScheduleInput(
        distribution_amt=distribution,
        repayment_years=payload.repayment_years,
    )
    
    result = calculate_repayment_schedule(inp)
    
    return {
        "total_distribution": str(result.total_distribution),
        "annual_repayment": str(result.annual_repayment),
        "repayment_schedule": result.repayment_schedule,
        "tax_spread_per_year": str(result.tax_spread_per_year),
        "explanation": result.explanation,
    }


@router.post("/penalty-waiver")
async def penalty_waiver(
    payload: PenaltyWaiverRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Check if the 10% early withdrawal penalty is waived for a qualified disaster distribution.
    
    Under IRC §72(t)(2)(G):
    - The 10% early withdrawal penalty does NOT apply to qualified disaster distributions
    - Applies regardless of taxpayer age
    - Waiver is automatic for distributions meeting Form 8915 requirements
    
    Requires a valid JWT (Bearer token).
    """
    try:
        distribution = Decimal(payload.distribution_amt)
    except Exception as e:
        return {"error": f"Invalid distribution_amt: {e}"}
    
    inp = PenaltyWaiverInput(
        age=payload.age,
        distribution_amt=distribution,
    )
    
    result = check_penalty_waiver(inp)
    
    return {
        "waiver_eligible": result.waiver_eligible,
        "standard_penalty_rate": str(result.standard_penalty_rate),
        "waived_penalty_amount": str(result.waived_penalty_amount),
        "explanation": result.explanation,
    }


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 8915 — no authentication required.
    """
    return {
        "form": "Form 8915",
        "title": "Qualified Disaster Retirement Plan Distributions and Repayments",
        "purpose": (
            "Form 8915 is used to report qualified disaster distributions from retirement plans "
            "and to calculate repayment amounts. Taxpayers who suffered economic loss due to a "
            "federally-declared disaster may be eligible for penalty relief and favorable tax treatment."
        ),
        "qualified_disaster_types": list(QUALIFIED_DISASTER_TYPES.values()),
        "max_distribution_limit": str(MAX_DISTRIBUTION_LIMIT),
        "repayment_period_years": STANDARD_REPAYMENT_YEARS,
        "tax_spread": {
            "period_years": STANDARD_REPAYMENT_YEARS,
            "annual_inclusion": "1/3 of distribution per year if NOT repaid",
        },
        "penalty_waiver": {
            "standard_penalty_rate": str(EARLY_WITHDRAWAL_PENALTY_RATE),
            "waiver_applies": True,
            "age_requirement": "None (waiver applies regardless of age)",
        },
        "key_requirements": [
            "Distribution from qualified retirement plan (401k, IRA, etc.)",
            "Federally-declared qualified disaster",
            "Principal residence in disaster area OR economic loss ≥ threshold",
            "Distribution within qualified disaster period (typically disaster date + 180 days)",
            f"Total distributions ≤ ${MAX_DISTRIBUTION_LIMIT:,}",
        ],
        "benefits": [
            "10% early withdrawal penalty waived",
            "Income spread over 3 years (1/3 per year)",
            "3-year repayment window to restore retirement savings",
            "No age restriction (even under 59½)",
        ],
        "filing_deadline": "April 15 (or October 15 with extension)",
        "statutory_references": [
            "IRC §72(t)(2)(G) — Penalty waiver for qualified disaster distributions",
            "IRC §1400Q — Special rules for qualified disaster distributions",
        ],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8915",
    }
