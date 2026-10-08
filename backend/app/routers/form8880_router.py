"""
Form 8880 Router — Credit for Retirement Savings.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8880 import (
    Form8880Input,
    Form8880Result,
    calculate_form8880,
    get_form8880_overview,
)

router = APIRouter()


class Form8880Request(BaseModel):
    retirement_contributions: str = Field(..., description="Retirement contributions")
    agi: str = Field(..., description="Adjusted gross income")
    filing_status: str = Field(..., description="Filing status")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8880Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8880 retirement savings credit."""
    try:
        inp = Form8880Input(
            retirement_contributions=Decimal(payload.retirement_contributions),
            agi=Decimal(payload.agi),
            filing_status=payload.filing_status,
            tax_year=payload.tax_year,
        )
        result = calculate_form8880(inp)
        return {
            "credit_rate": str(result.credit_rate),
            "credit_amount": str(result.credit_amount),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8880 overview."""
    return get_form8880_overview()
