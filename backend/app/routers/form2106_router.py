"""
Form 2106 Router — Employee Business Expenses.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form2106 import (
    Form2106Input,
    Form2106Result,
    calculate_form2106,
    get_form2106_overview,
)

router = APIRouter()


class Form2106Request(BaseModel):
    employee_expenses: str = Field(..., description="Total employee expenses")
    travel_expenses: str = Field("0", description="Travel expenses")
    meal_expenses: str = Field("0", description="Meal expenses")
    vehicle_expenses: str = Field("0", description="Vehicle expenses")
    agi: str = Field("0", description="Adjusted gross income")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form2106Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 2106 employee business expenses."""
    try:
        inp = Form2106Input(
            employee_expenses=Decimal(payload.employee_expenses),
            travel_expenses=Decimal(payload.travel_expenses),
            meal_expenses=Decimal(payload.meal_expenses),
            vehicle_expenses=Decimal(payload.vehicle_expenses),
            agi=Decimal(payload.agi),
            tax_year=payload.tax_year,
        )
        result = calculate_form2106(inp)
        return {
            "total_expenses": str(result.total_expenses),
            "deductible_meals": str(result.deductible_meals),
            "deductible_expenses": str(result.deductible_expenses),
            "agi_floor": str(result.agi_floor),
            "net_deduction": str(result.net_deduction),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 2106 overview."""
    return get_form2106_overview()
