"""
Schedule B Router — Interest and Ordinary Dividends.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_b import (
    ScheduleBInput,
    ScheduleBResult,
    calculate_schedule_b,
    get_schedule_b_overview,
)

router = APIRouter()


class ScheduleBRequest(BaseModel):
    interest_income: str = Field(..., description="Interest income")
    ordinary_dividends: str = Field(..., description="Ordinary dividends")
    foreign_accounts: bool = Field(False, description="Foreign accounts")
    foreign_trusts: bool = Field(False, description="Foreign trusts")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: ScheduleBRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule B interest and dividends."""
    try:
        inp = ScheduleBInput(
            interest_income=Decimal(payload.interest_income),
            ordinary_dividends=Decimal(payload.ordinary_dividends),
            foreign_accounts=payload.foreign_accounts,
            foreign_trusts=payload.foreign_trusts,
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_b(inp)
        return {
            "total_interest": str(result.total_interest),
            "total_dividends": str(result.total_dividends),
            "total_income": str(result.total_income),
            "filing_required": result.filing_required,
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule B overview."""
    return get_schedule_b_overview()
