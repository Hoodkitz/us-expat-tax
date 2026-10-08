"""
Form 8959 Router — Additional Medicare Tax.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8959 import (
    Form8959Input,
    Form8959Result,
    calculate_form8959,
    get_form8959_overview,
)

router = APIRouter()


class Form8959Request(BaseModel):
    wages: str = Field(..., description="Wages")
    self_employment_income: str = Field("0", description="Self-employment income")
    filing_status: str = Field(..., description="Filing status")
    medicare_withholding: str = Field("0", description="Medicare withholding")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8959Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8959 Additional Medicare Tax."""
    try:
        inp = Form8959Input(
            wages=Decimal(payload.wages),
            self_employment_income=Decimal(payload.self_employment_income),
            filing_status=payload.filing_status,
            medicare_withholding=Decimal(payload.medicare_withholding),
            tax_year=payload.tax_year,
        )
        result = calculate_form8959(inp)
        return {
            "threshold": str(result.threshold),
            "excess_wages": str(result.excess_wages),
            "additional_medicare_tax": str(result.additional_medicare_tax),
            "total_tax": str(result.total_tax),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8959 overview."""
    return get_form8959_overview()
