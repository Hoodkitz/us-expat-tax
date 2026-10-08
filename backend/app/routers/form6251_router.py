"""
Form 6251 Router — Alternative Minimum Tax.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form6251 import (
    Form6251Input,
    Form6251Result,
    calculate_form6251,
    get_form6251_overview,
)

router = APIRouter()


class Form6251Request(BaseModel):
    filing_status: str = Field(..., description="Filing status")
    regular_taxable_income: str = Field(..., description="Regular taxable income")
    tax_preferences: str = Field("0", description="Tax preference items")
    adjustments: str = Field("0", description="AMT adjustments")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form6251Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 6251 AMT."""
    try:
        inp = Form6251Input(
            filing_status=payload.filing_status,
            regular_taxable_income=Decimal(payload.regular_taxable_income),
            tax_preferences=Decimal(payload.tax_preferences),
            adjustments=Decimal(payload.adjustments),
            tax_year=payload.tax_year,
        )
        result = calculate_form6251(inp)
        return {
            "amt_income": str(result.amt_income),
            "exemption": str(result.exemption),
            "amt_base": str(result.amt_base),
            "amt": str(result.amt),
            "regular_tax": str(result.regular_tax),
            "amt_due": str(result.amt_due),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 6251 overview."""
    return get_form6251_overview()
