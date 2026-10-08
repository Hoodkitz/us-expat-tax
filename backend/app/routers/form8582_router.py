"""
Form 8582 Router — Passive Activity Loss Limitations.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8582 import (
    Form8582Input,
    Form8582Result,
    calculate_form8582,
    get_form8582_overview,
)

router = APIRouter()


class Form8582Request(BaseModel):
    passive_income: str = Field("0", description="Passive income")
    passive_losses: str = Field(..., description="Passive losses")
    agi: str = Field(..., description="Adjusted gross income")
    active_participation: bool = Field(False, description="Active participation")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8582Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8582 passive activity loss."""
    try:
        inp = Form8582Input(
            passive_income=Decimal(payload.passive_income),
            passive_losses=Decimal(payload.passive_losses),
            agi=Decimal(payload.agi),
            active_participation=payload.active_participation,
            tax_year=payload.tax_year,
        )
        result = calculate_form8582(inp)
        return {
            "deductible_loss": str(result.deductible_loss),
            "suspended_loss": str(result.suspended_loss),
            "special_allowance": str(result.special_allowance),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8582 overview."""
    return get_form8582_overview()
