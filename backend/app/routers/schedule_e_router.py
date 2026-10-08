"""
Schedule E Router — Supplemental Income and Loss.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_e import (
    ScheduleEInput,
    ScheduleEResult,
    calculate_schedule_e,
    get_schedule_e_overview,
)

router = APIRouter()


class ScheduleERequest(BaseModel):
    rental_income: str = Field("0", description="Rental income")
    royalty_income: str = Field("0", description="Royalty income")
    rental_expenses: str = Field("0", description="Rental expenses")
    royalty_expenses: str = Field("0", description="Royalty expenses")
    passive_loss_carryforward: str = Field("0", description="Passive loss carryforward")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: ScheduleERequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule E supplemental income and loss."""
    try:
        inp = ScheduleEInput(
            rental_income=Decimal(payload.rental_income),
            royalty_income=Decimal(payload.royalty_income),
            rental_expenses=Decimal(payload.rental_expenses),
            royalty_expenses=Decimal(payload.royalty_expenses),
            passive_loss_carryforward=Decimal(payload.passive_loss_carryforward),
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_e(inp)
        return {
            "total_income": str(result.total_income),
            "total_expenses": str(result.total_expenses),
            "net_income": str(result.net_income),
            "passive_loss": str(result.passive_loss),
            "suspended_loss": str(result.suspended_loss),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule E overview."""
    return get_schedule_e_overview()
