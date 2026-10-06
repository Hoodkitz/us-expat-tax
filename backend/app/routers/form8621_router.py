"""
Form 8621 PFIC Reporting Router.

POST /api/v1/form8621/filing-requirement  – Check if Form 8621 filing is required
POST /api/v1/form8621/mtm-calculation      – Mark-to-Market election calculation (§1296)
POST /api/v1/form8621/qef-calculation      – QEF election calculation (§1293)
POST /api/v1/form8621/excess-distribution  – Excess distribution calculation (§1291 default regime)
GET  /api/v1/form8621/overview             – Form 8621 overview and explanation
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.form8621 import (
    FilingRequirementInput,
    MTMCalculationInput,
    QEFCalculationInput,
    ExcessDistributionInput,
    check_filing_requirement,
    calculate_mtm,
    calculate_qef,
    calculate_excess_distribution,
    get_overview,
)

router = APIRouter(tags=["form8621"])

# ---------------------------------------------------------------------------
# Request models (re-export for router consistency)
# ---------------------------------------------------------------------------

class FilingRequirementRequest(BaseModel):
    has_pfic_interest: bool = Field(..., examples=[True])
    had_sale_or_distribution: bool = Field(..., examples=[False])
    received_excess_distribution: bool = Field(..., examples=[False])

class MTMCalculationRequest(BaseModel):
    beginning_fmv: float = Field(..., ge=0, examples=[100_000.0])
    ending_fmv: float = Field(..., ge=0, examples=[115_000.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])

class QEFCalculationRequest(BaseModel):
    ordinary_earnings: float = Field(..., ge=0, examples=[5_000.0])
    net_capital_gain: float = Field(..., ge=0, examples=[2_000.0])
    ownership_percentage: float = Field(..., ge=0, le=100, examples=[10.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])

class ExcessDistributionRequest(BaseModel):
    total_distribution: float = Field(..., ge=0, examples=[20_000.0])
    holding_period_years: int = Field(..., ge=1, examples=[5])
    prior_distributions: list[float] = Field(default_factory=list, examples=[[8_000.0, 7_500.0, 9_000.0]])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filing-requirement")
async def filing_requirement(payload: FilingRequirementRequest) -> dict:
    """
    Check if Form 8621 filing is required.
    
    Returns filing requirement status, reasons, and penalty information.
    Public endpoint — no JWT required.
    """
    inp = FilingRequirementInput(
        has_pfic_interest=payload.has_pfic_interest,
        had_sale_or_distribution=payload.had_sale_or_distribution,
        received_excess_distribution=payload.received_excess_distribution,
    )
    result = check_filing_requirement(inp)
    return result.model_dump()

@router.post("/mtm-calculation")
async def mtm_calculation(payload: MTMCalculationRequest) -> dict:
    """
    Calculate Mark-to-Market election (§1296).
    
    Returns unrealized gain/loss treated as ordinary income/loss.
    Public endpoint — no JWT required.
    """
    inp = MTMCalculationInput(
        beginning_fmv=payload.beginning_fmv,
        ending_fmv=payload.ending_fmv,
        tax_year=payload.tax_year,
    )
    result = calculate_mtm(inp)
    return result.model_dump()

@router.post("/qef-calculation")
async def qef_calculation(payload: QEFCalculationRequest) -> dict:
    """
    Calculate QEF (Qualified Electing Fund) election (§1293).
    
    Returns pro-rata share of ordinary earnings and net capital gain.
    Public endpoint — no JWT required.
    """
    inp = QEFCalculationInput(
        ordinary_earnings=payload.ordinary_earnings,
        net_capital_gain=payload.net_capital_gain,
        ownership_percentage=payload.ownership_percentage,
        tax_year=payload.tax_year,
    )
    result = calculate_qef(inp)
    return result.model_dump()

@router.post("/excess-distribution")
async def excess_distribution(payload: ExcessDistributionRequest) -> dict:
    """
    Calculate excess distribution under default regime (§1291).
    
    Returns deferred tax amount and interest charge.
    Public endpoint — no JWT required.
    """
    inp = ExcessDistributionInput(
        total_distribution=payload.total_distribution,
        holding_period_years=payload.holding_period_years,
        prior_distributions=payload.prior_distributions,
        tax_year=payload.tax_year,
    )
    result = calculate_excess_distribution(inp)
    return result.model_dump()

@router.get("/overview")
async def overview() -> dict:
    """
    Return Form 8621 overview: filing requirements, regimes, penalties.
    
    Public endpoint — no JWT required.
    """
    result = get_overview()
    return result.model_dump()
