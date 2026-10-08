"""
Form 8889 Router — Health Savings Accounts.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8889 import (
    Form8889Input,
    Form8889Result,
    calculate_form8889,
    get_form8889_overview,
)

router = APIRouter()


class Form8889Request(BaseModel):
    coverage_type: str = Field(..., description="Coverage type (self_only or family)")
    employee_contributions: str = Field(..., description="Employee contributions")
    employer_contributions: str = Field(..., description="Employer contributions")
    catch_up_contributions: str = Field("0", description="Catch-up contributions")
    distributions: str = Field("0", description="Distributions")
    qualified_medical_expenses: str = Field("0", description="Qualified medical expenses")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form8889Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 8889 HSA contributions and distributions."""
    try:
        inp = Form8889Input(
            coverage_type=payload.coverage_type,
            employee_contributions=Decimal(payload.employee_contributions),
            employer_contributions=Decimal(payload.employer_contributions),
            catch_up_contributions=Decimal(payload.catch_up_contributions),
            distributions=Decimal(payload.distributions),
            qualified_medical_expenses=Decimal(payload.qualified_medical_expenses),
            tax_year=payload.tax_year,
        )
        result = calculate_form8889(inp)
        return {
            "contribution_limit": str(result.contribution_limit),
            "total_contributions": str(result.total_contributions),
            "excess_contributions": str(result.excess_contributions),
            "deduction": str(result.deduction),
            "taxable_distribution": str(result.taxable_distribution),
            "penalty": str(result.penalty),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 8889 overview."""
    return get_form8889_overview()
