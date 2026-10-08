"""
Form 1040 Router — U.S. Individual Income Tax Return.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form1040 import (
    Form1040Input,
    Form1040Result,
    calculate_form1040,
    get_form1040_overview,
)

router = APIRouter()


class Form1040Request(BaseModel):
    filing_status: str = Field(..., description="Filing status")
    gross_income: str = Field(..., description="Gross income")
    adjustments: str = Field("0", description="Adjustments to income")
    deductions: str = Field("0", description="Deductions")
    credits: str = Field("0", description="Tax credits")
    withholding: str = Field("0", description="Tax withholding")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form1040Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 1040 income tax."""
    try:
        inp = Form1040Input(
            filing_status=payload.filing_status,
            gross_income=Decimal(payload.gross_income),
            adjustments=Decimal(payload.adjustments),
            deductions=Decimal(payload.deductions),
            credits=Decimal(payload.credits),
            withholding=Decimal(payload.withholding),
            tax_year=payload.tax_year,
        )
        result = calculate_form1040(inp)
        return {
            "agi": str(result.agi),
            "taxable_income": str(result.taxable_income),
            "tax_before_credits": str(result.tax_before_credits),
            "total_tax": str(result.total_tax),
            "effective_tax_rate": str(result.effective_tax_rate),
            "marginal_tax_rate": str(result.marginal_tax_rate),
            "balance_due": str(result.balance_due),
            "refund": str(result.refund),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 1040 overview."""
    return get_form1040_overview()
