"""
Schedule 3 Router — Additional Credits and Payments.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_3 import (
    Schedule3Input,
    Schedule3Result,
    calculate_schedule_3,
    get_schedule_3_overview,
)

router = APIRouter()


class Schedule3Request(BaseModel):
    foreign_tax_credit: str = Field("0", description="Foreign tax credit")
    child_dependent_care_credit: str = Field("0", description="Child and dependent care credit")
    education_credits: str = Field("0", description="Education credits")
    retirement_savings_credit: str = Field("0", description="Retirement savings credit")
    residential_energy_credit: str = Field("0", description="Residential energy credit")
    other_credits: str = Field("0", description="Other credits")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Schedule3Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule 3 additional credits and payments."""
    try:
        inp = Schedule3Input(
            foreign_tax_credit=Decimal(payload.foreign_tax_credit),
            child_dependent_care_credit=Decimal(payload.child_dependent_care_credit),
            education_credits=Decimal(payload.education_credits),
            retirement_savings_credit=Decimal(payload.retirement_savings_credit),
            residential_energy_credit=Decimal(payload.residential_energy_credit),
            other_credits=Decimal(payload.other_credits),
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_3(inp)
        return {
            "total_credits": str(result.total_credits),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule 3 overview."""
    return get_schedule_3_overview()
