"""
Form 4868 API Router.

POST /api/v1/form4868/calculate – Calculate extension deadline and penalties
POST /api/v1/form4868/status – Get extension status
POST /api/v1/form4868/abroad-check – Check abroad extension eligibility
GET  /api/v1/form4868/overview – Get Form 4868 law summary
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form4868 import (
    ExtensionInput,
    calculate_extension,
    get_extension_status,
    check_abroad_extension_eligible,
    get_form4868_overview,
)

router = APIRouter(tags=["form4868"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ExtensionCalculateRequest(BaseModel):
    """Request for extension calculation."""
    filing_status: str = Field(
        ...,
        description="Tax filing status",
        examples=["single"],
    )
    tax_year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Tax year",
        examples=[2025],
    )
    original_deadline: str = Field(
        ...,
        description="Original filing deadline in YYYY-MM-DD format",
        examples=["2025-04-15"],
    )
    extension_months: int = Field(
        default=6,
        ge=1,
        le=12,
        description="Extension period in months",
        examples=[6],
    )
    estimated_tax_liability: str = Field(
        default="0",
        description="Estimated total tax liability in USD",
        examples=["15000.00"],
    )
    amount_paid: str = Field(
        default="0",
        description="Amount already paid in USD",
        examples=["5000.00"],
    )
    reason: str = Field(
        default="automatic",
        description="Reason for extension",
        examples=["automatic"],
    )


class ExtensionStatusRequest(BaseModel):
    """Request for extension status check."""
    extension_filed: bool = Field(
        ...,
        description="Has extension been filed?",
        examples=[True],
    )
    tax_year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Tax year",
        examples=[2025],
    )


class AbroadCheckRequest(BaseModel):
    """Request to check abroad extension eligibility."""
    country: str = Field(
        ...,
        description="Country of residence",
        examples=["Germany"],
    )
    tax_year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Tax year",
        examples=[2025],
    )
    living_abroad: bool = Field(
        ...,
        description="Is taxpayer living outside the US?",
        examples=[True],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate")
async def calculate_extension_endpoint(
    payload: ExtensionCalculateRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate extension deadline and associated penalties.

    Under IRC §6081:
    - Automatic 6-month extension available
    - Extension to file is NOT extension to pay
    - Taxes owed must still be paid by original deadline

    **Authentication**: JWT required
    """
    try:
        original_deadline = date.fromisoformat(payload.original_deadline)
        estimated_tax_liability = Decimal(payload.estimated_tax_liability)
        amount_paid = Decimal(payload.amount_paid)
    except Exception as e:
        return {"error": f"Invalid input: {e}"}

    inp = ExtensionInput(
        filing_status=payload.filing_status,
        tax_year=payload.tax_year,
        original_deadline=original_deadline,
        extension_months=payload.extension_months,
        estimated_tax_liability=estimated_tax_liability,
        amount_paid=amount_paid,
        reason=payload.reason,
    )

    result = calculate_extension(inp)

    return {
        "extended_deadline": result.extended_deadline.isoformat(),
        "days_extended": result.days_extended,
        "extension_granted": result.extension_granted,
        "balance_due": str(result.balance_due),
        "payment_deadline": result.payment_deadline.isoformat(),
        "penalty_if_not_filed": str(result.penalty_if_not_filed),
        "interest_if_not_paid": str(result.interest_if_not_paid),
        "explanation": result.explanation,
    }


@router.post("/status")
async def extension_status_endpoint(
    payload: ExtensionStatusRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Get current status of extension request.

    Returns days remaining and filing/payment status.

    **Authentication**: JWT required
    """
    result = get_extension_status(
        extension_filed=payload.extension_filed,
        tax_year=payload.tax_year,
    )

    return {
        "extension_filed": result.extension_filed,
        "original_deadline": result.original_deadline.isoformat(),
        "extended_deadline": result.extended_deadline.isoformat(),
        "days_remaining": result.days_remaining,
        "filing_status": result.filing_status,
        "payment_status": result.payment_status,
    }


@router.post("/abroad-check")
async def abroad_check_endpoint(
    payload: AbroadCheckRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Check if taxpayer qualifies for special abroad extension.

    Under IRC §6081 and §7508:
    - Taxpayers living outside the US get automatic 2-month extension to June 15
    - Can also file Form 4868 for additional extension to October 15

    **Authentication**: JWT required
    """
    result = check_abroad_extension_eligible(
        country=payload.country,
        tax_year=payload.tax_year,
        living_abroad=payload.living_abroad,
    )

    return result


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 4868 — no authentication required.
    """
    return get_form4868_overview()
