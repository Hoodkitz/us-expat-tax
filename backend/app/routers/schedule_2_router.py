"""
Schedule 2 Router — Additional Taxes.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_2 import (
    Schedule2Input,
    Schedule2Result,
    calculate_schedule_2,
    get_schedule_2_overview,
)

router = APIRouter()


class Schedule2Request(BaseModel):
    alternative_minimum_tax: str = Field("0", description="Alternative minimum tax")
    excess_advance_premium_tax_credit: str = Field("0", description="Excess advance premium tax credit")
    self_employment_tax: str = Field("0", description="Self-employment tax")
    additional_medicare_tax: str = Field("0", description="Additional Medicare tax")
    net_investment_income_tax: str = Field("0", description="Net investment income tax")
    recapture_taxes: str = Field("0", description="Recapture taxes")
    other_taxes: str = Field("0", description="Other taxes")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Schedule2Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule 2 additional taxes."""
    try:
        inp = Schedule2Input(
            alternative_minimum_tax=Decimal(payload.alternative_minimum_tax),
            excess_advance_premium_tax_credit=Decimal(payload.excess_advance_premium_tax_credit),
            self_employment_tax=Decimal(payload.self_employment_tax),
            additional_medicare_tax=Decimal(payload.additional_medicare_tax),
            net_investment_income_tax=Decimal(payload.net_investment_income_tax),
            recapture_taxes=Decimal(payload.recapture_taxes),
            other_taxes=Decimal(payload.other_taxes),
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_2(inp)
        return {
            "total_additional_taxes": str(result.total_additional_taxes),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule 2 overview."""
    return get_schedule_2_overview()
