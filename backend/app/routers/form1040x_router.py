"""
Form 1040-X Router — Amended U.S. Individual Income Tax Return.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form1040x import (
    Form1040XInput,
    Form1040XResult,
    calculate_form1040x,
    get_form1040x_overview,
)

router = APIRouter()


class Form1040XRequest(BaseModel):
    original_tax: str = Field(..., description="Original tax liability")
    corrected_tax: str = Field(..., description="Corrected tax liability")
    original_payments: str = Field("0", description="Original payments")
    corrected_payments: str = Field("0", description="Corrected payments")
    explanation: str = Field("", description="Explanation of changes")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form1040XRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 1040-X amended return."""
    try:
        inp = Form1040XInput(
            original_tax=Decimal(payload.original_tax),
            corrected_tax=Decimal(payload.corrected_tax),
            original_payments=Decimal(payload.original_payments),
            corrected_payments=Decimal(payload.corrected_payments),
            explanation=payload.explanation,
            tax_year=payload.tax_year,
        )
        result = calculate_form1040x(inp)
        return {
            "additional_tax_due": str(result.additional_tax_due),
            "refund_due": str(result.refund_due),
            "penalty": str(result.penalty),
            "interest": str(result.interest),
            "total_due": str(result.total_due),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 1040-X overview."""
    return get_form1040x_overview()
