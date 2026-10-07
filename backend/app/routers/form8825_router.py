"""
Form 8825 API Router.

Endpoints:
- POST /api/v1/form8825/filing-requirement — Check if Form 8825 filing is required
- POST /api/v1/form8825/penalty-calculation — Calculate penalties for non-filing
- GET  /api/v1/form8825/overview — Get overview of Form 8825 requirements
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.auth.utils import get_current_tenant
from app.modules.form8825 import (
    FilingRequirementInput,
    FilingRequirementResult,
    PenaltyCalculationInput,
    PenaltyResult,
    Form8825Overview,
    check_filing_requirement,
    calculate_penalty,
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

    Returns filing requirement status, reasons, and recommendations.
    """
    try:
        return check_filing_requirement(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/penalty-calculation", response_model=PenaltyResult)
def penalty_calculation(
    inp: PenaltyCalculationInput,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8825.

    Returns base penalty, continued failure penalty, and total.
    """
    try:
        return calculate_penalty(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/overview", response_model=Form8825Overview)
def overview() -> Form8825Overview:
    """
    Get overview of Form 8825 requirements.

    Returns information about filing thresholds, penalties, and related forms.
    """
    return get_overview()
