"""
Form 8965 Router — Health Coverage Exemptions.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8965 import (
    Form8965Input,
    Form8965Result,
    calculate_form8965,
    get_form8965_overview,
)

router = APIRouter()


class Form8965Request(BaseModel):
    exemption_type: str = Field(..., description="Exemption type")
    months_without_coverage: int = Field(..., description="Months without coverage")
    household_income: str = Field(..., description="Household income")
    filing_threshold: str = Field(..., description="Filing threshold")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8965Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8965 health coverage exemptions."""
    try:
        inp = Form8965Input(
            exemption_type=payload.exemption_type,
            months_without_coverage=payload.months_without_coverage,
            household_income=Decimal(payload.household_income),
            filing_threshold=Decimal(payload.filing_threshold),
            tax_year=payload.tax_year,
        )
        result = calculate_form8965(inp)
        return {
            "exemption_approved": result.exemption_approved,
            "penalty": str(result.penalty),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8965 overview."""
    return get_form8965_overview()
