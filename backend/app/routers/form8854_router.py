"""
Form 8854 Expatriation Tax API Router
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.modules.form8854 import (
    FilingRequirementTest,
    ExitTaxCalculator,
    PenaltyCalculator,
    get_form8854_overview,
)
from app.auth.utils import get_current_tenant


router = APIRouter(prefix="/api/v1/form8854", tags=["Form 8854"])


# Request/Response Models
class FilingRequirementRequest(BaseModel):
    net_worth: float = Field(..., description="Total net worth in USD")
    five_year_avg_tax: float = Field(..., description="5-year average tax liability")
    years_of_residence: int = Field(..., description="Years as U.S. resident in last 15 years")
    year: int = Field(2025, description="Tax year")


class FilingRequirementResponse(BaseModel):
    covered_expatriate: bool
    net_worth_test: dict
    tax_liability_test: dict
    long_term_resident_test: dict


class ExitTaxRequest(BaseModel):
    fair_market_value: float = Field(..., description="Fair market value of assets")
    adjusted_basis: float = Field(..., description="Adjusted tax basis of assets")
    capital_gains_rate: float = Field(0.20, description="Capital gains tax rate")
    year: int = Field(2025, description="Tax year")


class ExitTaxResponse(BaseModel):
    fair_market_value: float
    adjusted_basis: float
    unrealized_gain: float
    exemption: float
    exemption_used: float
    taxable_gain: float
    capital_gains_rate: float
    exit_tax: float


class PenaltyRequest(BaseModel):
    failed_to_file: bool = Field(..., description="Whether Form 8854 was not filed")
    months_late: int = Field(0, description="Number of months late")


class PenaltyResponse(BaseModel):
    total_penalties: float
    penalties: list


@router.post("/filing-requirement", response_model=FilingRequirementResponse)
def calculate_filing_requirement(
    request: FilingRequirementRequest,
    current_tenant: str = Depends(get_current_tenant)
):
    """
    Test if individual is a covered expatriate.
    
    Covered Expatriate Test:
    - Net Worth > $2M, OR
    - 5-year avg tax liability > $206k (2025), OR
    - Failure to certify tax compliance (not implemented here)
    
    Also tests Long-Term Resident status (>=8 of last 15 years).
    """
    try:
        result = FilingRequirementTest.is_covered_expatriate(
            net_worth=request.net_worth,
            five_year_avg_tax=request.five_year_avg_tax,
            years_of_residence=request.years_of_residence,
            year=request.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/exit-tax-calculation", response_model=ExitTaxResponse)
def calculate_exit_tax(
    request: ExitTaxRequest,
    current_tenant: str = Depends(get_current_tenant)
):
    """
    Calculate exit tax under mark-to-market regime.
    
    Mark-to-Market:
    - Assets deemed sold on day before expatriation
    - Unrealized gains taxed as capital gains
    - $866k exemption (2025)
    - Typically 20% long-term capital gains rate
    """
    try:
        result = ExitTaxCalculator.calculate_exit_tax(
            fair_market_value=request.fair_market_value,
            adjusted_basis=request.adjusted_basis,
            capital_gains_rate=request.capital_gains_rate,
            year=request.year,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/penalty-calculator", response_model=PenaltyResponse)
def calculate_penalties(
    request: PenaltyRequest,
    current_tenant: str = Depends(get_current_tenant)
):
    """
    Calculate penalties for Form 8854 non-compliance.
    
    Failure-to-File Penalty: $10,000
    """
    try:
        result = PenaltyCalculator.estimate_total_penalties(
            failed_to_file=request.failed_to_file,
            months_late=request.months_late,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overview")
def get_overview(current_tenant: str = Depends(get_current_tenant)):
    """
    Get overview of Form 8854 requirements, thresholds, and penalties.
    """
    try:
        return get_form8854_overview()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
