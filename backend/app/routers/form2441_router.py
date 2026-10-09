"""
Form 2441 Router — Child and Dependent Care Expenses.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form2441 import (
    Form2441Input,
    QualifyingPerson,
    calculate_form2441,
    get_form2441_overview,
)

router = APIRouter()


class QualifyingPersonRequest(BaseModel):
    """A qualifying person for Form 2441."""
    name: str = Field(..., description="Name of qualifying person")
    relationship: str = Field(..., description="Relationship: child, spouse, or dependent")
    age: int = Field(..., description="Age of qualifying person")
    is_disabled: bool = Field(False, description="Whether the person is disabled")
    care_expenses: str = Field("0", description="Care expenses for this person")


class Form2441Request(BaseModel):
    """Request model for Form 2441 calculation."""
    num_dependents: int = Field(..., description="Number of qualifying dependents")
    care_expenses: str = Field(..., description="Total care expenses")
    agi: str = Field(..., description="Adjusted gross income")
    tax_year: int = Field(2025, description="Tax year")
    earned_income: str | None = Field(None, description="Earned income (optional)")
    filing_status: str = Field("single", description="Filing status")
    qualifying_persons: list[QualifyingPersonRequest] = Field(
        default_factory=list, description="List of qualifying persons"
    )


@router.post("/calculate")
async def calculate(
    payload: Form2441Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 2441 child and dependent care credit."""
    try:
        persons = [
            QualifyingPerson(
                name=p.name,
                relationship=p.relationship,
                age=p.age,
                is_disabled=p.is_disabled,
                care_expenses=Decimal(p.care_expenses),
            )
            for p in payload.qualifying_persons
        ]
        inp = Form2441Input(
            num_dependents=payload.num_dependents,
            care_expenses=Decimal(payload.care_expenses),
            agi=Decimal(payload.agi),
            tax_year=payload.tax_year,
            earned_income=Decimal(payload.earned_income) if payload.earned_income else None,
            filing_status=payload.filing_status,
            qualifying_persons=persons,
        )
        result = calculate_form2441(inp)
        return {
            "max_expenses": str(result.max_expenses),
            "applicable_percentage": str(result.applicable_percentage),
            "credit_amount": str(result.credit_amount),
            "explanation": result.explanation,
            "eligible_expenses": str(result.eligible_expenses),
            "earned_income_limit": str(result.earned_income_limit) if result.earned_income_limit else None,
            "is_eligible": result.is_eligible,
            "num_qualifying_persons": result.num_qualifying_persons,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 2441 overview."""
    return get_form2441_overview()
