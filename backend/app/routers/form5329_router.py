"""
Form 5329 Router — Additional Taxes on Qualified Plans.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form5329 import (
    Form5329Input,
    Form5329Result,
    calculate_form5329,
    get_form5329_overview,
)

router = APIRouter()


class Form5329Request(BaseModel):
    early_distribution: str = Field("0", description="Early distribution amount")
    excess_ira_contribution: str = Field("0", description="Excess IRA contribution")
    excess_hsa_contribution: str = Field("0", description="Excess HSA contribution")
    excess_rmd: str = Field("0", description="Excess RMD amount")
    tax_year: int = Field(2025, description="Tax year")


@router.post("/calculate")
async def calculate(
    payload: Form5329Request,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Calculate Form 5329 additional taxes."""
    try:
        inp = Form5329Input(
            early_distribution=Decimal(payload.early_distribution),
            excess_ira_contribution=Decimal(payload.excess_ira_contribution),
            excess_hsa_contribution=Decimal(payload.excess_hsa_contribution),
            excess_rmd=Decimal(payload.excess_rmd),
            tax_year=payload.tax_year,
        )
        result = calculate_form5329(inp)
        return {
            "early_distribution_penalty": str(result.early_distribution_penalty),
            "excess_ira_penalty": str(result.excess_ira_penalty),
            "excess_hsa_penalty": str(result.excess_hsa_penalty),
            "excess_rmd_penalty": str(result.excess_rmd_penalty),
            "total_penalty": str(result.total_penalty),
            "explanation": result.explanation,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/overview")
async def overview(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Get Form 5329 overview."""
    return get_form5329_overview()
