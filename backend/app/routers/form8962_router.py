"""
Form 8962 Router — Premium Tax Credit.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8962 import (
    Form8962Input,
    Form8962Result,
    calculate_form8962,
    get_form8962_overview,
)

router = APIRouter()


class Form8962Request(BaseModel):
    household_income: str = Field(..., description="Household income")
    federal_poverty_line: str = Field(..., description="Federal poverty line")
    advance_premium_tax_credit: str = Field(..., description="Advance premium tax credit")
    benchmark_plan_premium: str = Field(..., description="Benchmark plan premium")
    actual_premium_paid: str = Field(..., description="Actual premium paid")
    family_size: int = Field(..., description="Family size")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8962Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8962 Premium Tax Credit."""
    try:
        inp = Form8962Input(
            household_income=Decimal(payload.household_income),
            federal_poverty_line=Decimal(payload.federal_poverty_line),
            advance_premium_tax_credit=Decimal(payload.advance_premium_tax_credit),
            benchmark_plan_premium=Decimal(payload.benchmark_plan_premium),
            actual_premium_paid=Decimal(payload.actual_premium_paid),
            family_size=payload.family_size,
            tax_year=payload.tax_year,
        )
        result = calculate_form8962(inp)
        return {
            "fpl_percentage": str(result.fpl_percentage),
            "expected_contribution": str(result.expected_contribution),
            "premium_tax_credit": str(result.premium_tax_credit),
            "repayment": str(result.repayment),
            "net_credit": str(result.net_credit),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8962 overview."""
    return get_form8962_overview()
