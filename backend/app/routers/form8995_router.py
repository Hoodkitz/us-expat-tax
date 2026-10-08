"""
Form 8995 Router — Qualified Business Income Deduction.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8995 import (
    Form8995Input,
    Form8995Result,
    calculate_form8995,
    get_form8995_overview,
)

router = APIRouter()


class Form8995Request(BaseModel):
    qualified_business_income: str = Field(..., description="Qualified business income")
    agi: str = Field(..., description="Adjusted gross income")
    filing_status: str = Field(..., description="Filing status")
    specified_service_business: bool = Field(False, description="Specified service business")
    w2_wages: str = Field("0", description="W-2 wages")
    ubia: str = Field("0", description="Unadjusted basis immediately after acquisition")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8995Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8995 QBI deduction."""
    try:
        inp = Form8995Input(
            qualified_business_income=Decimal(payload.qualified_business_income),
            agi=Decimal(payload.agi),
            filing_status=payload.filing_status,
            specified_service_business=payload.specified_service_business,
            w2_wages=Decimal(payload.w2_wages),
            ubia=Decimal(payload.ubia),
            tax_year=payload.tax_year,
        )
        result = calculate_form8995(inp)
        return {
            "qbi_deduction": str(result.qbi_deduction),
            "phaseout_applied": result.phaseout_applied,
            "wage_limit_applied": result.wage_limit_applied,
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8995 overview."""
    return get_form8995_overview()
