"""
Form 1040-ES API Router.

POST /api/v1/form1040es/calculate – Calculate estimated tax
POST /api/v1/form1040es/quarterly-schedule – Get quarterly payment schedule
GET  /api/v1/form1040es/overview – Get Form 1040-ES law summary
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form1040es import (
    EstimatedTaxInput,
    calculate_estimated_tax,
    calculate_quarterly_schedule,
    get_form1040es_overview,
)

router = APIRouter(tags=["form1040es"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class EstimatedTaxRequest(BaseModel):
    """Request for estimated tax calculation."""
    filing_status: str = Field(
        ...,
        description="Tax filing status",
        examples=["single"],
    )
    annual_income: str = Field(
        ...,
        description="Annual income in USD",
        examples=["85000.00"],
    )
    withholding: str = Field(
        default="0",
        description="Total withholding in USD",
        examples=["5000.00"],
    )
    deductions: str = Field(
        default="0",
        description="Total deductions in USD (standard deduction applied if higher)",
        examples=["0"],
    )
    credits: str = Field(
        default="0",
        description="Total tax credits in USD",
        examples=["0"],
    )
    prior_year_tax: str = Field(
        ...,
        description="Prior year total tax liability in USD",
        examples=["12000.00"],
    )
    current_year_tax: str | None = Field(
        default=None,
        description="Current year tax liability (if known)",
        examples=["15000.00"],
    )
    quarters_paid: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Number of quarterly payments already made",
        examples=[0],
    )
    amount_paid: str = Field(
        default="0",
        description="Total estimated tax already paid in USD",
        examples=["0"],
    )


class QuarterlyScheduleRequest(BaseModel):
    """Request for quarterly payment schedule."""
    filing_status: str = Field(
        ...,
        description="Tax filing status",
        examples=["single"],
    )
    annual_income: str = Field(
        ...,
        description="Annual income in USD",
        examples=["85000.00"],
    )
    withholding: str = Field(
        default="0",
        description="Total withholding in USD",
        examples=["5000.00"],
    )
    deductions: str = Field(
        default="0",
        description="Total deductions in USD",
        examples=["0"],
    )
    credits: str = Field(
        default="0",
        description="Total tax credits in USD",
        examples=["0"],
    )
    prior_year_tax: str = Field(
        ...,
        description="Prior year total tax liability in USD",
        examples=["12000.00"],
    )
    quarters_paid: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Number of quarterly payments already made",
        examples=[0],
    )
    amount_paid: str = Field(
        default="0",
        description="Total estimated tax already paid in USD",
        examples=["0"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate")
async def calculate_estimated_tax_endpoint(
    payload: EstimatedTaxRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate estimated tax liability and quarterly payments.

    Applies 2025 tax rules:
    - Progressive tax brackets
    - Safe harbor rules (90% current year or 100%/110% prior year)
    - Underpayment penalty calculation

    **Authentication**: JWT required
    """
    try:
        annual_income = Decimal(payload.annual_income)
        withholding = Decimal(payload.withholding)
        deductions = Decimal(payload.deductions)
        credits = Decimal(payload.credits)
        prior_year_tax = Decimal(payload.prior_year_tax)
        current_year_tax = Decimal(payload.current_year_tax) if payload.current_year_tax else None
        amount_paid = Decimal(payload.amount_paid)
    except Exception as e:
        return {"error": f"Invalid numeric input: {e}"}

    inp = EstimatedTaxInput(
        filing_status=payload.filing_status,
        annual_income=annual_income,
        withholding=withholding,
        deductions=deductions,
        credits=credits,
        prior_year_tax=prior_year_tax,
        current_year_tax=current_year_tax,
        quarters_paid=payload.quarters_paid,
        amount_paid=amount_paid,
    )

    result = calculate_estimated_tax(inp)

    return {
        "total_tax_liability": str(result.total_tax_liability),
        "total_payments": str(result.total_payments),
        "balance_due": str(result.balance_due),
        "quarterly_payment": str(result.quarterly_payment),
        "safe_harbor_met": result.safe_harbor_met,
        "safe_harbor_amount": str(result.safe_harbor_amount),
        "underpayment_penalty": str(result.underpayment_penalty),
        "underpayment_quarters": result.underpayment_quarters,
        "effective_tax_rate": str(result.effective_tax_rate),
        "marginal_tax_rate": str(result.marginal_tax_rate),
        "explanation": result.explanation,
    }


@router.post("/quarterly-schedule")
async def quarterly_schedule_endpoint(
    payload: QuarterlyScheduleRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate quarterly estimated tax payment schedule.

    Shows cumulative due dates and remaining balance for each quarter.

    **Authentication**: JWT required
    """
    try:
        annual_income = Decimal(payload.annual_income)
        withholding = Decimal(payload.withholding)
        deductions = Decimal(payload.deductions)
        credits = Decimal(payload.credits)
        prior_year_tax = Decimal(payload.prior_year_tax)
        amount_paid = Decimal(payload.amount_paid)
    except Exception as e:
        return {"error": f"Invalid numeric input: {e}"}

    inp = EstimatedTaxInput(
        filing_status=payload.filing_status,
        annual_income=annual_income,
        withholding=withholding,
        deductions=deductions,
        credits=credits,
        prior_year_tax=prior_year_tax,
        quarters_paid=payload.quarters_paid,
        amount_paid=amount_paid,
    )

    result = calculate_quarterly_schedule(inp)

    return {
        "payments": [
            {
                "quarter": p.quarter,
                "due_date": p.due_date,
                "amount_due": str(p.amount_due),
                "cumulative_due": str(p.cumulative_due),
                "paid": str(p.paid),
                "balance": str(p.balance),
            }
            for p in result.payments
        ],
        "total_due": str(result.total_due),
        "total_paid": str(result.total_paid),
        "remaining_balance": str(result.remaining_balance),
    }


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 1040-ES — no authentication required.
    """
    return get_form1040es_overview()
