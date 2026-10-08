"""
Form 4562 Router — Depreciation and Amortization.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form4562 import (
    Form4562Input,
    Form4562Result,
    calculate_form4562,
    get_form4562_overview,
)

router = APIRouter()


class Form4562Request(BaseModel):
    asset_cost: str = Field(..., description="Cost of asset")
    asset_type: str = Field(..., description="Type of asset (5, 7, 15, 27.5, 39 year)")
    business_use_percentage: str = Field("100", description="Business use percentage")
    section_179_election: str = Field("0", description="Section 179 election amount")
    bonus_depreciation: str = Field("0", description="Bonus depreciation amount")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form4562Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 4562 depreciation."""
    try:
        inp = Form4562Input(
            asset_cost=Decimal(payload.asset_cost),
            asset_type=payload.asset_type,
            business_use_percentage=Decimal(payload.business_use_percentage),
            section_179_election=Decimal(payload.section_179_election),
            bonus_depreciation=Decimal(payload.bonus_depreciation),
            tax_year=payload.tax_year,
        )
        result = calculate_form4562(inp)
        return {
            "section_179_deduction": str(result.section_179_deduction),
            "bonus_depreciation": str(result.bonus_depreciation),
            "regular_depreciation": str(result.regular_depreciation),
            "total_depreciation": str(result.total_depreciation),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 4562 overview."""
    return get_form4562_overview()
