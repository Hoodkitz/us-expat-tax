"""
Form 8812 Router — Credits for Qualifying Children.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8812 import (
    Form8812Input,
    Form8812Result,
    calculate_form8812,
    get_form8812_overview,
)

router = APIRouter()


class Form8812Request(BaseModel):
    num_qualifying_children: int = Field(..., description="Number of qualifying children")
    num_other_dependents: int = Field(0, description="Number of other dependents")
    agi: str = Field(..., description="Adjusted gross income")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8812Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8812 child tax credit."""
    try:
        inp = Form8812Input(
            num_qualifying_children=payload.num_qualifying_children,
            num_other_dependents=payload.num_other_dependents,
            agi=Decimal(payload.agi),
            tax_year=payload.tax_year,
        )
        result = calculate_form8812(inp)
        return {
            "child_tax_credit": str(result.child_tax_credit),
            "credit_for_other_dependents": str(result.credit_for_other_dependents),
            "refundable_credit": str(result.refundable_credit),
            "total_credit": str(result.total_credit),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8812 overview."""
    return get_form8812_overview()
