"""
Form 2441 Router — Child and Dependent Care Expenses.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form2441 import (
    Form2441Input,
    Form2441Result,
    calculate_form2441,
    get_form2441_overview,
)

router = APIRouter()


class Form2441Request(BaseModel):
    num_dependents: int = Field(..., description="Number of qualifying dependents")
    care_expenses: str = Field(..., description="Total care expenses")
    agi: str = Field(..., description="Adjusted gross income")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form2441Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 2441 child and dependent care credit."""
    try:
        inp = Form2441Input(
            num_dependents=payload.num_dependents,
            care_expenses=Decimal(payload.care_expenses),
            agi=Decimal(payload.agi),
            tax_year=payload.tax_year,
        )
        result = calculate_form2441(inp)
        return {
            "max_expenses": str(result.max_expenses),
            "applicable_percentage": str(result.applicable_percentage),
            "credit_amount": str(result.credit_amount),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 2441 overview."""
    return get_form2441_overview()
