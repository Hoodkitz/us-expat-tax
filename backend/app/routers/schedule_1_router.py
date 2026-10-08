"""
Schedule 1 Router — Additional Income and Adjustments to Income.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.schedule_1 import (
    Schedule1Input,
    Schedule1Result,
    calculate_schedule_1,
    get_schedule_1_overview,
)

router = APIRouter()


class Schedule1Request(BaseModel):
    alimony_received: str = Field("0", description="Alimony received")
    business_income: str = Field("0", description="Business income")
    other_gains: str = Field("0", description="Other gains")
    rental_income: str = Field("0", description="Rental income")
    farm_income: str = Field("0", description="Farm income")
    unemployment_compensation: str = Field("0", description="Unemployment compensation")
    other_income: str = Field("0", description="Other income")
    educator_expenses: str = Field("0", description="Educator expenses")
    hsa_deduction: str = Field("0", description="HSA deduction")
    student_loan_interest: str = Field("0", description="Student loan interest")
    ira_deduction: str = Field("0", description="IRA deduction")
    self_employment_tax_deduction: str = Field("0", description="Self-employment tax deduction")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Schedule1Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Schedule 1 additional income and adjustments."""
    try:
        inp = Schedule1Input(
            alimony_received=Decimal(payload.alimony_received),
            business_income=Decimal(payload.business_income),
            other_gains=Decimal(payload.other_gains),
            rental_income=Decimal(payload.rental_income),
            farm_income=Decimal(payload.farm_income),
            unemployment_compensation=Decimal(payload.unemployment_compensation),
            other_income=Decimal(payload.other_income),
            educator_expenses=Decimal(payload.educator_expenses),
            hsa_deduction=Decimal(payload.hsa_deduction),
            student_loan_interest=Decimal(payload.student_loan_interest),
            ira_deduction=Decimal(payload.ira_deduction),
            self_employment_tax_deduction=Decimal(payload.self_employment_tax_deduction),
            tax_year=payload.tax_year,
        )
        result = calculate_schedule_1(inp)
        return {
            "total_additional_income": str(result.total_additional_income),
            "total_adjustments": str(result.total_adjustments),
            "net_adjustment": str(result.net_adjustment),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Schedule 1 overview."""
    return get_schedule_1_overview()
