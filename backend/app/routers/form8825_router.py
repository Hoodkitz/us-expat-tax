"""
Form 8825 API Router.

Endpoints:
- POST /api/v1/form8825/filing-requirement — Check if Form 8825 filing is required
- POST /api/v1/form8825/income-summary — Calculate rental income summary
- POST /api/v1/form8825/expense-calculation — Calculate rental expenses
- GET  /api/v1/form8825/overview — Get overview of Form 8825 requirements
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.auth.utils import get_current_tenant
from app.modules.form8825 import (
    FilingRequirementInput,
    FilingRequirementResult,
    IncomeSummaryInput,
    IncomeSummaryResult,
    ExpenseCalculationInput,
    ExpenseCalculationResult,
    Form8825Overview,
    check_filing_requirement,
    calculate_income_summary,
    calculate_expenses,
    get_overview,
)

router = APIRouter(
    tags=["form8825"],
)


@router.post("/filing-requirement", response_model=FilingRequirementResult)
def filing_requirement(
    inp: FilingRequirementInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FilingRequirementResult:
    """
    Check if the taxpayer has a filing requirement for Form 8825.

    Returns filing requirement status, passive loss calculations, and recommendations.
    """
    try:
        return check_filing_requirement(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/income-summary", response_model=IncomeSummaryResult)
def income_summary(
    inp: IncomeSummaryInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> IncomeSummaryResult:
    """
    Calculate rental income summary for Form 8825.

    Returns total rental income including advance rents, security deposits,
    and tenant-paid expenses.
    """
    try:
        return calculate_income_summary(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/expense-calculation", response_model=ExpenseCalculationResult)
def expense_calculation(
    inp: ExpenseCalculationInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExpenseCalculationResult:
    """
    Calculate rental expenses for Form 8825.

    Returns total expenses, breakdown by category, and deductible amounts.
    """
    try:
        return calculate_expenses(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/overview", response_model=Form8825Overview)
def overview() -> Form8825Overview:
    """
    Get overview of Form 8825 requirements.

    Returns information about filing thresholds, income types, expense categories,
    and passive loss rules.
    """
    return get_overview()
