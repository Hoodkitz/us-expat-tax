"""
Schedule SE API Router.
POST /api/v1/schedule-se/calculate – Calculate self-employment tax
POST /api/v1/schedule-se/deduction – Calculate SE tax deduction
GET /api/v1/schedule-se/overview – Get Schedule SE law summary
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_se import (
    FilingStatus,
    ScheduleSEInput,
    ScheduleSEResult,
    calculate_schedule_se,
    calculate_se_deduction,
    get_schedule_se_overview,
)

router = APIRouter(tags=["schedule-se"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ScheduleSECalculateRequest(BaseModel):
    """Request for Schedule SE calculation."""
    net_self_employment_income: float = Field(
        ...,
        description="Net profit from self-employment (Schedule C/F)",
        examples=[75_000.0],
    )
    filing_status: FilingStatus = Field(
        default="single",
        description="Tax filing status",
        examples=["single"],
    )
    tax_year: int = Field(
        default=2025,
        ge=2025,
        le=2025,
        description="Tax year (only 2025 supported)",
        examples=[2025],
    )


class ScheduleSEDeductionRequest(BaseModel):
    """Request for SE tax deduction calculation."""
    total_self_employment_tax: float = Field(
        ...,
        ge=0,
        description="Total self-employment tax from Schedule SE",
        examples=[10_597.50],
    )


class ScheduleSEDeductionResponse(BaseModel):
    """Response for SE tax deduction."""
    total_self_employment_tax: float
    deductible_se_tax: float
    description: str = "One-half of self-employment tax (IRC §164(f))"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate", response_model=ScheduleSEResult)
async def schedule_se_calculate(
    req: ScheduleSECalculateRequest,
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> ScheduleSEResult:
    """
    Calculate self-employment tax (Schedule SE).
    
    Applies IRC §1401 and §1402 rules:
    - 92.35% of net self-employment income = net earnings
    - 12.4% Social Security tax up to $168,600 (2025)
    - 2.9% Medicare tax on all earnings
    - 0.9% Additional Medicare tax above threshold ($200k/$250k)
    
    **Authentication**: JWT required
    """
    input_data = ScheduleSEInput(
        net_self_employment_income=req.net_self_employment_income,
        filing_status=req.filing_status,
        tax_year=req.tax_year,
    )
    return calculate_schedule_se(input_data)


@router.post("/deduction", response_model=ScheduleSEDeductionResponse)
async def schedule_se_deduction(
    req: ScheduleSEDeductionRequest,
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> ScheduleSEDeductionResponse:
    """
    Calculate the deductible portion of self-employment tax (IRC §164(f)).
    
    Returns exactly 50% of the total SE tax, which reduces AGI on Form 1040
    Schedule 1, Line 15.
    
    **Authentication**: JWT required
    """
    deductible = calculate_se_deduction(req.total_self_employment_tax)
    return ScheduleSEDeductionResponse(
        total_self_employment_tax=req.total_self_employment_tax,
        deductible_se_tax=deductible,
    )


@router.get("/overview")
async def schedule_se_overview(
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> dict:
    """
    Get Schedule SE law summary and calculation overview.
    
    Returns statutory authority, tax rates, calculation steps, and notes
    for Schedule SE (Self-Employment Tax).
    
    **Authentication**: JWT required
    """
    return get_schedule_se_overview()
