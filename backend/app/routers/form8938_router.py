"""
Form 8938 FATCA Router.

Endpoints:
- POST /api/v1/form8938/filing-requirement — Check if Form 8938 filing is required
- POST /api/v1/form8938/penalty-calculator — Calculate penalties for non-filing
- GET  /api/v1/form8938/overview — Get overview of Form 8938 requirements
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.modules.form8938 import (
    FilingRequirementInput,
    FilingRequirementResult,
    PenaltyCalculationInput,
    PenaltyResult,
    Form8938Overview,
    check_filing_requirement,
    calculate_penalty,
    get_overview,
)

router = APIRouter(
    prefix="/api/v1/form8938",
    tags=["form8938"],
)


@router.post("/filing-requirement", response_model=FilingRequirementResult)
def filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Check if Form 8938 filing is required based on filing status and foreign accounts.

    Returns whether filing is required, the applicable threshold, total value,
    reasons for the requirement, and the penalty if not filed.
    """
    try:
        return check_filing_requirement(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/penalty-calculator", response_model=PenaltyResult)
def penalty_calculator(inp: PenaltyCalculationInput) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8938.

    Includes base penalty, continued failure penalty (after IRS notice),
    and willful failure penalty.
    """
    try:
        return calculate_penalty(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/overview", response_model=Form8938Overview)
def overview() -> Form8938Overview:
    """
    Get overview of Form 8938 FATCA reporting requirements.

    Returns filing thresholds, penalty amounts, account types, and recommendations.
    """
    return get_overview()
