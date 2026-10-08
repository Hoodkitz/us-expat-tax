"""
Form 8917 Router — Tuition and Fees Deduction.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8917 import (
    Form8917Input,
    Form8917Result,
    calculate_form8917,
    get_form8917_overview,
)

router = APIRouter()


class Form8917Request(BaseModel):
    qualified_expenses: str = Field(..., description="Qualified education expenses")
    agi: str = Field(..., description="Adjusted gross income")
    filing_status: str = Field(..., description="Filing status")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8917Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8917 tuition and fees deduction."""
    try:
        inp = Form8917Input(
            qualified_expenses=Decimal(payload.qualified_expenses),
            agi=Decimal(payload.agi),
            filing_status=payload.filing_status,
            tax_year=payload.tax_year,
        )
        result = calculate_form8917(inp)
        return {
            "deduction": str(result.deduction),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8917 overview."""
    return get_form8917_overview()
