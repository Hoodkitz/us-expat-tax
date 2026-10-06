"""
Form 8865 API Router.

Endpoints:
- POST /api/v1/form8865/filing-requirement — Check if Form 8865 filing is required
- POST /api/v1/form8865/income-summary — Summarize partnership income (Subpart F, GILTI, QBI)
- POST /api/v1/form8865/penalty-calculation — Calculate penalties for non-filing
- GET  /api/v1/form8865/overview — Get overview of Form 8865 requirements
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.auth.utils import get_current_tenant
from app.modules.form8865 import (
    FilingRequirementInput,
    FilingRequirementResult,
    IncomeSummaryInput,
    IncomeSummaryResult,
    PenaltyCalculationInput,
    PenaltyResult,
    Form8865Overview,
    check_filing_requirement,
    summarize_income,
    calculate_penalty,
    get_overview,
)

router = APIRouter(
    tags=["form8865"],
)


@router.post("/filing-requirement", response_model=FilingRequirementResult)
def filing_requirement(
    inp: FilingRequirementInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FilingRequirementResult:
    """
    Check if the taxpayer has a filing requirement for Form 8865.

    Returns which categories (1-5) apply, reasons, and recommendations.
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
    Summarize partnership income for tax reporting.

    Includes Subpart F, GILTI, QBI (§199A), ordinary income, capital gains,
    and foreign tax credit eligibility.
    """
    try:
        return summarize_income(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/penalty-calculation", response_model=PenaltyResult)
def penalty_calculation(
    inp: PenaltyCalculationInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8865.

    Returns base penalty, continued failure penalty, willful penalty, and total.
    """
    try:
        return calculate_penalty(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/overview", response_model=Form8865Overview)
def overview() -> Form8865Overview:
    """
    Get overview of Form 8865 requirements.

    Returns information about Categories 1-5, penalties, filing deadline,
    and general recommendations.
    """
    return get_overview()
