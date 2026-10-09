"""
Form 8919 Router — Uncollected Social Security and Medicare Tax on Wages.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8919 import (
    Form8919Input,
    Form8919Result,
    calculate_form8919,
    get_form8919_overview,
)

router = APIRouter()


class Form8919Request(BaseModel):
    wages: str = Field(..., description="Wages subject to Social Security and Medicare tax")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8919Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8919 uncollected Social Security and Medicare tax."""
    try:
        inp = Form8919Input(
            wages=Decimal(payload.wages),
            tax_year=payload.tax_year,
        )
        result = calculate_form8919(inp)
        return {
            "social_security_tax": str(result.social_security_tax),
            "medicare_tax": str(result.medicare_tax),
            "total_tax": str(result.total_tax),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8919 overview."""
    return get_form8919_overview()
