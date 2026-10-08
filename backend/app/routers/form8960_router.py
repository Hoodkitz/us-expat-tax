"""
Form 8960 Router — Net Investment Income Tax.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8960 import (
    Form8960Input,
    Form8960Result,
    calculate_form8960,
    get_form8960_overview,
)

router = APIRouter()


class Form8960Request(BaseModel):
    filing_status: str = Field(..., description="Filing status")
    magi: str = Field(..., description="Modified adjusted gross income")
    net_investment_income: str = Field(..., description="Net investment income")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8960Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8960 Net Investment Income Tax."""
    try:
        inp = Form8960Input(
            filing_status=payload.filing_status,
            magi=Decimal(payload.magi),
            net_investment_income=Decimal(payload.net_investment_income),
            tax_year=payload.tax_year,
        )
        result = calculate_form8960(inp)
        return {
            "threshold": str(result.threshold),
            "excess_magi": str(result.excess_magi),
            "niit": str(result.niit),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8960 overview."""
    return get_form8960_overview()
