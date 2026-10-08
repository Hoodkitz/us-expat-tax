"""
Form 8990 Router — Business Interest Expense Limitation.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8990 import (
    Form8990Input,
    Form8990Result,
    calculate_form8990,
    get_form8990_overview,
)

router = APIRouter()


class Form8990Request(BaseModel):
    business_interest_expense: str = Field(..., description="Business interest expense")
    adjusted_taxable_income: str = Field(..., description="Adjusted taxable income")
    floor_plan_financing_interest: str = Field("0", description="Floor plan financing interest")
    small_business_exception: bool = Field(False, description="Small business exception")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8990Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8990 business interest expense limitation."""
    try:
        inp = Form8990Input(
            business_interest_expense=Decimal(payload.business_interest_expense),
            adjusted_taxable_income=Decimal(payload.adjusted_taxable_income),
            floor_plan_financing_interest=Decimal(payload.floor_plan_financing_interest),
            small_business_exception=payload.small_business_exception,
            tax_year=payload.tax_year,
        )
        result = calculate_form8990(inp)
        return {
            "limitation": str(result.limitation),
            "deductible_interest": str(result.deductible_interest),
            "excess_interest": str(result.excess_interest),
            "carryforward": str(result.carryforward),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8990 overview."""
    return get_form8990_overview()
