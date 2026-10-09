"""
Schedule R API Router.
POST /api/v1/schedule-r/calculate — Calculate credit for the elderly or disabled
GET /api/v1/schedule-r/overview — Get Schedule R law summary
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_r import (
    FilingStatus,
    ScheduleRInput,
    ScheduleRResult,
    calculate_schedule_r,
    get_schedule_r_overview,
)

router = APIRouter(tags=["schedule-r"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ScheduleRCalculateRequest(BaseModel):
    """Request for Schedule R calculation."""

    filing_status: FilingStatus = Field(
        default="single",
        description="Tax filing status",
        examples=["single"],
    )
    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Taxpayer age (must be 65+ or disabled)",
        examples=[67],
    )
    spouse_age: int | None = Field(
        default=None,
        ge=0,
        le=120,
        description="Spouse age (if married filing jointly)",
        examples=[65],
    )
    is_disabled: bool = Field(
        default=False,
        description="Whether taxpayer is permanently and totally disabled",
        examples=[False],
    )
    spouse_is_disabled: bool = Field(
        default=False,
        description="Whether spouse is permanently and totally disabled",
        examples=[False],
    )
    agi: float = Field(
        ...,
        ge=0,
        description="Adjusted gross income",
        examples=[12000.0],
    )
    nontaxable_social_security: float = Field(
        default=0.0,
        ge=0,
        description="Nontaxable Social Security benefits",
        examples=[0.0],
    )
    nontaxable_pension: float = Field(
        default=0.0,
        ge=0,
        description="Nontaxable pension or annuity income",
        examples=[0.0],
    )
    nontaxable_other: float = Field(
        default=0.0,
        ge=0,
        description="Other nontaxable income (e.g., nontaxable railroad retirement)",
        examples=[0.0],
    )
    tax_year: int = Field(
        default=2025,
        ge=2025,
        le=2025,
        description="Tax year (only 2025 supported)",
        examples=[2025],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate", response_model=ScheduleRResult)
async def schedule_r_calculate(
    req: ScheduleRCalculateRequest,
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> ScheduleRResult:
    """
    Calculate Schedule R credit for the elderly or disabled.

    Applies IRC §22 rules:
    - Base amount: $5,000 single, $7,500 MFJ (both 65+), $3,750 MFS
    - Reduced by 50% of AGI over $7,500 single / $10,000 MFJ
    - Also reduced by nontaxable Social Security and pensions
    - Final credit = 15% of remaining amount

    **Authentication**: JWT required
    """
    input_data = ScheduleRInput(
        filing_status=req.filing_status,
        age=req.age,
        spouse_age=req.spouse_age,
        is_disabled=req.is_disabled,
        spouse_is_disabled=req.spouse_is_disabled,
        agi=req.agi,
        nontaxable_social_security=req.nontaxable_social_security,
        nontaxable_pension=req.nontaxable_pension,
        nontaxable_other=req.nontaxable_other,
        tax_year=req.tax_year,
    )
    return calculate_schedule_r(input_data)


@router.get("/overview")
async def schedule_r_overview(
    tenant: Annotated[str, Depends(get_current_tenant)],
) -> dict:
    """
    Get Schedule R law summary and calculation overview.

    Returns statutory authority, base amounts, AGI thresholds, calculation
    steps, and notes for Schedule R (Credit for the Elderly or the Disabled).

    **Authentication**: JWT required
    """
    return get_schedule_r_overview()
