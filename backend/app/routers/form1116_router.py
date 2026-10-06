"""
Form 1116 Foreign Tax Credit (FTC) Router.

POST /api/v1/form1116/calculate           – JWT-protected FTC calculation
POST /api/v1/form1116/feie-vs-ftc-compare – compare FEIE vs FTC strategies
GET  /api/v1/form1116/overview            – explanation of Form 1116
POST /api/v1/form1116/carryover-tracker   – JWT-protected: save carryover
GET  /api/v1/form1116/carryover-tracker   – JWT-protected: list carryovers
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form1116 import (
    FTCInput,
    FeieVsFtcInput,
    IncomeCategoryLiteral,
    INCOME_CATEGORY_EXPLANATIONS,
    CARRYFORWARD_YEARS,
    CARRYBACK_YEARS,
    calculate_ftc,
    compare_feie_vs_ftc,
    save_carryover,
    get_carryovers,
)

router = APIRouter(tags=["form1116"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class FTCCalculateRequest(BaseModel):
    foreign_taxes_paid: float = Field(..., ge=0, examples=[15_000.0])
    foreign_income: float = Field(..., ge=0, examples=[80_000.0])
    total_income: float = Field(..., gt=0, examples=[100_000.0])
    us_tax_before_credit: float = Field(..., ge=0, examples=[18_000.0])
    income_category: IncomeCategoryLiteral = Field("general", examples=["general"])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class FeieVsFtcCompareRequest(BaseModel):
    foreign_income: float = Field(..., ge=0, examples=[80_000.0])
    foreign_taxes_paid: float = Field(..., ge=0, examples=[15_000.0])
    total_us_income: float = Field(..., gt=0, examples=[100_000.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class CarryoverCreateRequest(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    excess_credit: float = Field(..., ge=0, examples=[3_500.0])
    income_category: IncomeCategoryLiteral = Field("general", examples=["general"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/calculate")
async def ftc_calculate(
    payload: FTCCalculateRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate Form 1116 Foreign Tax Credit limitation and allowable credit.
    Requires a valid JWT (Bearer token).
    """
    inp = FTCInput(
        foreign_taxes_paid=payload.foreign_taxes_paid,
        foreign_income=payload.foreign_income,
        total_income=payload.total_income,
        us_tax_before_credit=payload.us_tax_before_credit,
        income_category=payload.income_category,
        tax_year=payload.tax_year,
    )
    result = calculate_ftc(inp)
    return result.model_dump()


@router.post("/feie-vs-ftc-compare")
async def feie_vs_ftc_compare(
    payload: FeieVsFtcCompareRequest,
) -> dict:
    """
    Compare FEIE (Form 2555) vs FTC (Form 1116) for a given income scenario.
    Public endpoint — no JWT required.
    """
    inp = FeieVsFtcInput(
        foreign_income=payload.foreign_income,
        foreign_taxes_paid=payload.foreign_taxes_paid,
        total_us_income=payload.total_us_income,
        tax_year=payload.tax_year,
    )
    result = compare_feie_vs_ftc(inp)
    return result.model_dump()


@router.get("/overview")
async def form1116_overview() -> dict:
    """
    Returns a structured explanation of Form 1116, income categories,
    carryover rules, and key limitations.
    Public endpoint — no JWT required.
    """
    return {
        "form": "Form 1116",
        "title": "Foreign Tax Credit",
        "purpose": (
            "Form 1116 allows US citizens and residents living abroad to claim a credit "
            "for income taxes paid (or accrued) to a foreign country, reducing the risk "
            "of double taxation on the same income."
        ),
        "limitation_formula": (
            "FTC Limitation = US Tax Before Credit × (Foreign Income / Total Income). "
            "The allowable credit is the lesser of foreign taxes paid and the FTC limitation."
        ),
        "carryover_rules": {
            "carryback_years": CARRYBACK_YEARS,
            "carryforward_years": CARRYFORWARD_YEARS,
            "explanation": (
                f"Excess credits (foreign taxes paid > FTC limitation) may be carried back "
                f"{CARRYBACK_YEARS} year or carried forward up to {CARRYFORWARD_YEARS} years "
                "to offset US tax on future foreign-source income."
            ),
        },
        "income_categories": {
            category: explanation
            for category, explanation in INCOME_CATEGORY_EXPLANATIONS.items()
        },
        "key_notes": [
            "You cannot claim both FEIE (Form 2555) and FTC on the same income.",
            "FTC is generally advantageous when your foreign tax rate exceeds the US rate.",
            "FEIE is generally advantageous when your foreign tax rate is lower than the US rate.",
            "The FTC cannot exceed your US tax liability on foreign-source income.",
            "Section 901(j) income from sanctioned countries is generally ineligible for FTC.",
        ],
        "related_forms": ["Form 1040", "Form 2555 (FEIE)", "FinCEN 114 (FBAR)"],
    }


@router.post("/carryover-tracker", status_code=201)
async def create_carryover(
    payload: CarryoverCreateRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Store an FTC carryover record for the authenticated tenant.
    Requires a valid JWT (Bearer token).
    """
    tenant_id: str = current_tenant["tenant_id"]
    record = save_carryover(
        tenant_id=tenant_id,
        tax_year=payload.tax_year,
        excess_credit=payload.excess_credit,
        income_category=payload.income_category,
    )
    return record


@router.get("/carryover-tracker")
async def list_carryovers(
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    List all FTC carryover records for the authenticated tenant,
    including expiry dates.
    Requires a valid JWT (Bearer token).
    """
    tenant_id: str = current_tenant["tenant_id"]
    records = get_carryovers(tenant_id=tenant_id)
    return {
        "count": len(records),
        "carryover_rules": {
            "carryback_years": CARRYBACK_YEARS,
            "carryforward_years": CARRYFORWARD_YEARS,
        },
        "carryovers": records,
    }
