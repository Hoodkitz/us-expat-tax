"""
Schedule D Router — Capital Gains and Losses.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_d import (
    ScheduleDInput,
    ScheduleDResult,
    calculate_schedule_d,
    get_schedule_d_overview,
)

router = APIRouter()


class ScheduleDRequest(BaseModel):
    short_term_gains: str = Field("0", description="Short-term gains")
    short_term_losses: str = Field("0", description="Short-term losses")
    long_term_gains: str = Field("0", description="Long-term gains")
    long_term_losses: str = Field("0", description="Long-term losses")
    capital_loss_carryforward: str = Field("0", description="Capital loss carryforward")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: ScheduleDRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule D capital gains and losses."""
    try:
        inp = ScheduleDInput(
            short_term_gains=Decimal(payload.short_term_gains),
            short_term_losses=Decimal(payload.short_term_losses),
            long_term_gains=Decimal(payload.long_term_gains),
            long_term_losses=Decimal(payload.long_term_losses),
            capital_loss_carryforward=Decimal(payload.capital_loss_carryforward),
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_d(inp)
        return {
            "net_short_term": str(result.net_short_term),
            "net_long_term": str(result.net_long_term),
            "net_capital_gain": str(result.net_capital_gain),
            "deductible_loss": str(result.deductible_loss),
            "carryforward": str(result.carryforward),
            "tax_rate": str(result.tax_rate),
            "tax": str(result.tax),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule D overview."""
    return get_schedule_d_overview()
