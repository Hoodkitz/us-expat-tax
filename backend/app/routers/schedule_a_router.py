"""
Schedule A API Router.
POST /api/v1/schedule-a/calculate – Calculate itemized deductions
GET /api/v1/schedule-a/overview – Get Schedule A law summary
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_a import (
    FilingStatus,
    ScheduleAInput,
    ScheduleAResult,
    calculate_schedule_a,
    get_schedule_a_overview,
)

router = APIRouter(tags=["schedule-a"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ScheduleACalculateRequest(BaseModel):
    """Request for Schedule A calculation."""
    adjusted_gross_income: float = Field(
        ...,
        description="Adjusted Gross Income (AGI)",
        examples=[85_000.0],
    )
    medical_expenses: float = Field(
        default=0.0,
        ge=0,
        description="Total medical and dental expenses",
        examples=[5_000.0],
    )
    state_local_taxes: float = Field(
        default=0.0,
        ge=0,
        description="State and local taxes paid (SALT)",
        examples=[12_000.0],
    )
    mortgage_interest: float = Field(
        default=0.0,
        ge=0,
        description="Mortgage interest paid",
        examples=[8_000.0],
    )
    mortgage_debt: float = Field(
        default=0.0,
        ge=0,
        description="Total mortgage debt principal",
        examples=[400_000.0],
    )
    charitable_contributions: float = Field(
        default=0.0,
        ge=0,
        description="Charitable cash contributions",
        examples=[3_000.0],
    )
    casualty_theft_losses: float = Field(
        default=0.0,
        ge=0,
        description="Casualty/theft losses (federal disasters only)",
        examples=[0.0],
    )
    filing_status: FilingStatus = Field(
        default="single",
        description="Tax filing status",
        examples=["single"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate", response_model=ScheduleAResult)
async def schedule_a_calculate(
    req: ScheduleACalculateRequest,
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> ScheduleAResult:
    """
    Calculate Schedule A itemized deductions.

    Applies 2025 tax rules:
    - Medical expenses: Only amount exceeding 7.5% of AGI
    - SALT: Capped at $10,000 ($5,000 if MFS)
    - Mortgage interest: Deductible on up to $750,000 of debt
    - Charitable contributions: Up to 60% of AGI
    - Casualty/theft losses: Federally declared disasters only

    **Authentication**: JWT required
    """
    input_data = ScheduleAInput(
        adjusted_gross_income=req.adjusted_gross_income,
        medical_expenses=req.medical_expenses,
        state_local_taxes=req.state_local_taxes,
        mortgage_interest=req.mortgage_interest,
        mortgage_debt=req.mortgage_debt,
        charitable_contributions=req.charitable_contributions,
        casualty_theft_losses=req.casualty_theft_losses,
        filing_status=req.filing_status,
    )
    return calculate_schedule_a(input_data)


@router.get("/overview")
async def schedule_a_overview(
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> dict:
    """
    Get Schedule A law summary and calculation overview.

    Returns statutory authority, deduction rules, standard deduction amounts,
    and calculation steps for Schedule A (Itemized Deductions).

    **Authentication**: JWT required
    """
    return get_schedule_a_overview()