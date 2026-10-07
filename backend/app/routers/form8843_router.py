"""
Form 8843 — Statement for Exempt Individuals and Individuals with a Medical Condition.

POST /api/v1/form8843/exempt-status       – JWT-protected: check exempt individual status
POST /api/v1/form8843/substantial-presence – JWT-protected: Substantial Presence Test
GET  /api/v1/form8843/overview             – public: static overview of Form 8843
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form8843 import (
    ExemptIndividualInput,
    ExemptIndividualResult,
    check_exempt_status,
)

router = APIRouter(tags=["form8843"])

# ---------------------------------------------------------------------------
# Constants & Thresholds
# ---------------------------------------------------------------------------

SPT_DAYS_THRESHOLD = 183
SPT_MIN_CURRENT_YEAR_DAYS = 31

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ExemptStatusRequest(BaseModel):
    """Request to check exempt individual status."""
    us_days_present: int = Field(..., ge=0, le=366, examples=[120], description="Days present in the US in the current tax year")
    foreign_days_present: int = Field(..., ge=0, le=366, examples=[245], description="Days present outside the US in the current tax year")
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    visa_type: Literal["F", "J", "M", "Q", "P", "H", "L", "O", "B", "E", "other"] = Field(..., examples=["F"], description="Visa type")
    is_student: bool = Field(default=False, examples=[True], description="Is the individual a student?")
    is_teacher: bool = Field(default=False, examples=[False], description="Is the individual a teacher?")
    is_trainee: bool = Field(default=False, examples=[False], description="Is the individual a trainee?")
    is_researcher: bool = Field(default=False, examples=[False], description="Is the individual a researcher?")


class SubstantialPresenceRequest(BaseModel):
    """Request to calculate the Substantial Presence Test."""
    us_days_present: int = Field(..., ge=0, le=366, examples=[120], description="Days present in the US in the current tax year")
    prior_year_us_days: int = Field(..., ge=0, le=366, examples=[60], description="Days present in the US in the prior tax year")
    two_years_ago_us_days: int = Field(..., ge=0, le=366, examples=[30], description="Days present in the US two years ago")
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    is_exempt: bool = Field(default=False, examples=[False], description="Is the individual an Exempt Individual?")


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------


def _check_exempt_status(req: ExemptStatusRequest) -> dict:
    """Check if an individual qualifies as an Exempt Individual."""
    inp = ExemptIndividualInput(
        us_days_present=req.us_days_present,
        foreign_days_present=req.foreign_days_present,
        tax_year=req.tax_year,
        visa_type=req.visa_type,
        is_student=req.is_student,
        is_teacher=req.is_teacher,
        is_trainee=req.is_trainee,
        is_researcher=req.is_researcher,
    )
    result = check_exempt_status(inp)
    return {
        "exempt_status": result.exempt_status,
        "days_counted": result.days_counted,
        "substantial_presence_test": result.substantial_presence_test,
        "required_forms": result.required_forms,
        "explanation": result.explanation,
    }


def _calculate_substantial_presence(req: SubstantialPresenceRequest) -> dict:
    """
    Calculate the Substantial Presence Test under IRC §7701(b)(1)-(3).

    Formula:
    - Current year days: 1 day each
    - Prior year days: 1/3 day each
    - Year before prior: 1/6 day each

    Threshold: 183 days
    """
    if req.is_exempt:
        return {
            "applies": False,
            "current_year_days": req.us_days_present,
            "prior_year_days_weighted": 0,
            "two_years_ago_days_weighted": 0,
            "total_days_counted": 0,
            "threshold": SPT_DAYS_THRESHOLD,
            "meets_threshold": False,
            "explanation": (
                "Substantial Presence Test does not apply to Exempt Individuals "
                "under IRC §7701(b)(5)."
            ),
        }

    # Calculate weighted days
    current_year_days = req.us_days_present
    prior_year_days_weighted = req.prior_year_us_days / 3
    two_years_ago_days_weighted = req.two_years_ago_us_days / 6

    total_days_counted = (
        current_year_days +
        prior_year_days_weighted +
        two_years_ago_days_weighted
    )

    meets_threshold = total_days_counted >= SPT_DAYS_THRESHOLD

    return {
        "applies": True,
        "current_year_days": current_year_days,
        "prior_year_days_weighted": round(prior_year_days_weighted, 2),
        "two_years_ago_days_weighted": round(two_years_ago_days_weighted, 2),
        "total_days_counted": round(total_days_counted, 2),
        "threshold": SPT_DAYS_THRESHOLD,
        "meets_threshold": meets_threshold,
        "explanation": (
            f"Total days counted: {round(total_days_counted, 2)}. "
            f"Threshold: {SPT_DAYS_THRESHOLD} days. "
            f"{'Meets' if meets_threshold else 'Does not meet'} the Substantial Presence Test."
        ),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/exempt-status")
async def exempt_status(
    payload: ExemptStatusRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Check if an individual qualifies as an Exempt Individual under IRC §7701(b)(5).
    Requires a valid JWT (Bearer token).
    """
    return _check_exempt_status(payload)


@router.post("/substantial-presence")
async def substantial_presence(
    payload: SubstantialPresenceRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate the Substantial Presence Test under IRC §7701(b)(1)-(3).
    Requires a valid JWT (Bearer token).
    """
    return _calculate_substantial_presence(payload)


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 8843 — no authentication required.
    """
    return {
        "form": "Form 8843",
        "title": "Statement for Exempt Individuals and Individuals with a Medical Condition",
        "purpose": (
            "Form 8843 is filed by individuals who are exempt from the "
            "Substantial Presence Test under IRC §7701(b)(5). "
            "This includes students, teachers, trainees, researchers, and athletes "
            "on qualifying visas (F, J, M, Q, P)."
        ),
        "who_must_file": [
            "Students (F, J, M, Q visas)",
            "Teachers/Trainees (J, Q visas)",
            "Researchers (J, Q visas)",
            "Athletes (P visas)",
            "Individuals with a medical condition",
        ],
        "exempt_visa_types": ["F", "J", "M", "Q", "P"],
        "substantial_presence_test": {
            "threshold_days": SPT_DAYS_THRESHOLD,
            "min_current_year_days": SPT_MIN_CURRENT_YEAR_DAYS,
            "formula": "Current year days + (Prior year days / 3) + (Two years ago days / 6)",
            "statutory_reference": "IRC §7701(b)(1)-(3)",
        },
        "key_requirements": [
            "Must be present in the US on a qualifying visa (F, J, M, Q, P)",
            "Must be a student, teacher, trainee, researcher, or athlete",
            "Must file Form 8843 to claim exempt status",
            "Exempt Individuals are NOT subject to the Substantial Presence Test",
        ],
        "filing_deadline": "April 15 (or June 15 if abroad)",
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8843",
    }
