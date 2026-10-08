"""
Form 8606 Router — Nondeductible IRAs.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8606 import (
    Form8606Input,
    Form8606Result,
    calculate_form8606,
    get_form8606_overview,
)

router = APIRouter()


class Form8606Request(BaseModel):
    nondeductible_contributions: str = Field(..., description="Nondeductible contributions")
    traditional_ira_basis: str = Field(..., description="Traditional IRA basis")
    distributions: str = Field(..., description="Distributions")
    ira_balance: str = Field(..., description="IRA balance")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8606Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8606 nondeductible IRA distributions."""
    try:
        inp = Form8606Input(
            nondeductible_contributions=Decimal(payload.nondeductible_contributions),
            traditional_ira_basis=Decimal(payload.traditional_ira_basis),
            distributions=Decimal(payload.distributions),
            ira_balance=Decimal(payload.ira_balance),
            tax_year=payload.tax_year,
        )
        result = calculate_form8606(inp)
        return {
            "total_basis": str(result.total_basis),
            "taxable_distribution": str(result.taxable_distribution),
            "nontaxable_distribution": str(result.nontaxable_distribution),
            "remaining_basis": str(result.remaining_basis),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8606 overview."""
    return get_form8606_overview()
