"""
Form 8863 Router — Education Credits.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8863 import (
    Form8863Input,
    Form8863Result,
    calculate_form8863,
    get_form8863_overview,
)

router = APIRouter()


class Form8863Request(BaseModel):
    credit_type: str = Field(..., description="Credit type (aotc or llc)")
    qualified_expenses: str = Field(..., description="Qualified education expenses")
    agi: str = Field(..., description="Adjusted gross income")
    filing_status: str = Field(..., description="Filing status")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8863Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8863 education credits."""
    try:
        inp = Form8863Input(
            credit_type=payload.credit_type,
            qualified_expenses=Decimal(payload.qualified_expenses),
            agi=Decimal(payload.agi),
            filing_status=payload.filing_status,
            tax_year=payload.tax_year,
        )
        result = calculate_form8863(inp)
        return {
            "credit_amount": str(result.credit_amount),
            "refundable_amount": str(result.refundable_amount),
            "nonrefundable_amount": str(result.nonrefundable_amount),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8863 overview."""
    return get_form8863_overview()
