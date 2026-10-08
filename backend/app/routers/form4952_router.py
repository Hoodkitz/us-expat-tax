"""
Form 4952 Router — Investment Interest Expense Deduction.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form4952 import (
    Form4952Input,
    Form4952Result,
    calculate_form4952,
    get_form4952_overview,
)

router = APIRouter()


class Form4952Request(BaseModel):
    investment_interest_expense: str = Field(..., description="Investment interest expense")
    investment_income: str = Field(..., description="Net investment income")
    disallowed_interest_carryforward: str = Field("0", description="Disallowed interest carryforward")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form4952Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 4952 investment interest deduction."""
    try:
        inp = Form4952Input(
            investment_interest_expense=Decimal(payload.investment_interest_expense),
            investment_income=Decimal(payload.investment_income),
            disallowed_interest_carryforward=Decimal(payload.disallowed_interest_carryforward),
            tax_year=payload.tax_year,
        )
        result = calculate_form4952(inp)
        return {
            "deductible_interest": str(result.deductible_interest),
            "disallowed_interest": str(result.disallowed_interest),
            "carryforward": str(result.carryforward),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 4952 overview."""
    return get_form4952_overview()
