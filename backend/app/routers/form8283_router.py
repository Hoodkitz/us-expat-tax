"""
Form 8283 Router — Noncash Charitable Contributions.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8283 import (
    Form8283Input,
    Form8283Result,
    calculate_form8283,
    get_form8283_overview,
)

router = APIRouter()


class Form8283Request(BaseModel):
    property_type: str = Field(..., description="Type of property")
    fair_market_value: str = Field(..., description="Fair market value")
    cost_basis: str = Field(..., description="Cost basis")
    appraisal_required: bool = Field(False, description="Appraisal required")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8283Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8283 noncash charitable contributions."""
    try:
        inp = Form8283Input(
            property_type=payload.property_type,
            fair_market_value=Decimal(payload.fair_market_value),
            cost_basis=Decimal(payload.cost_basis),
            appraisal_required=payload.appraisal_required,
            tax_year=payload.tax_year,
        )
        result = calculate_form8283(inp)
        return {
            "deductible_amount": str(result.deductible_amount),
            "appraisal_required": result.appraisal_required,
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8283 overview."""
    return get_form8283_overview()
