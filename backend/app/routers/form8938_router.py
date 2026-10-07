"""
Form 8938 FATCA Router.

Endpoints:
- POST /api/v1/form8938/filing-requirement — Check if Form 8938 filing is required
- POST /api/v1/form8938/penalty-calculator — Calculate penalties for non-filing
- GET  /api/v1/form8938/overview — Get overview of Form 8938 requirements
- POST /api/v1/form8938/trust-reporting — Check foreign trust reporting requirements
- POST /api/v1/form8938/joint-filing-check — Check joint filing thresholds (domestic/abroad)
- POST /api/v1/form8938/accuracy-penalty — Calculate 40% accuracy-related penalty
- POST /api/v1/form8938/statute-of-limitations — Determine statute of limitations (3 vs 6 years)
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
from app.modules.form8938_extended import (
    ForeignTrustInput,
    ForeignTrustResult,
    JointFilingThresholdInput,
    JointFilingThresholdResult,
    AccuracyPenaltyInput,
    AccuracyPenaltyResult,
    StatuteOfLimitationsInput,
    StatuteOfLimitationsResult,
    check_foreign_trust_reporting,
    check_joint_filing_threshold,
    calculate_accuracy_penalty,
    check_statute_of_limitations,
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


@router.post("/trust-reporting", response_model=ForeignTrustResult)
def trust_reporting(inp: ForeignTrustInput) -> ForeignTrustResult:
    """
    Check foreign trust reporting requirements under IRC §§671-679.
    
    Returns required forms, penalties, and grantor trust determination.
    """
    try:
        return check_foreign_trust_reporting(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/joint-filing-check", response_model=JointFilingThresholdResult)
def joint_filing_check(inp: JointFilingThresholdInput) -> JointFilingThresholdResult:
    """
    Check filing requirement with proper joint filing thresholds.
    
    Thresholds differ for domestic vs abroad residency:
    - MFJ abroad: $400k year-end / $600k any time
    - Single abroad: $200k year-end / $300k any time
    """
    try:
        return check_joint_filing_threshold(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/accuracy-penalty", response_model=AccuracyPenaltyResult)
def accuracy_penalty(inp: AccuracyPenaltyInput) -> AccuracyPenaltyResult:
    """
    Calculate 40% accuracy-related penalty for undisclosed foreign assets.
    
    IRC §6662(j): This penalty applies in addition to Form 8938 filing penalties.
    """
    try:
        return calculate_accuracy_penalty(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/statute-of-limitations", response_model=StatuteOfLimitationsResult)
def statute_of_limitations(inp: StatuteOfLimitationsInput) -> StatuteOfLimitationsResult:
    """
    Determine statute of limitations for IRS assessment.
    
    Returns 3 years (normal) or 6 years (extended for unreported foreign assets).
    """
    try:
        return check_statute_of_limitations(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
