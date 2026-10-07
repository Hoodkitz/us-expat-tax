"""
Form 3520-A Foreign Trust Annual Information Return Router.

POST /api/v1/form3520a/filing-requirement  – JWT-protected: determine filing obligation
POST /api/v1/form3520a/income-distribution – JWT-protected: calculate income distributions
POST /api/v1/form3520a/foreign-grantor-statement – JWT-protected: generate grantor trust statement
POST /api/v1/form3520a/penalty-calculator  – JWT-protected: calculate §6677 penalties
GET  /api/v1/form3520a/overview            – static overview of Form 3520-A
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant
from app.modules.form3520a import (
    TrustType,
    FilerRole,
    IncomeType,
    determine_filing_requirement,
    IncomeDistributionItem,
    calculate_income_distribution,
    generate_foreign_grantor_statement,
    calculate_form3520a_penalties,
    get_form3520a_overview,
)

router = APIRouter(tags=["form3520a"])

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class FilingRequirementRequest(BaseModel):
    is_us_owner: bool = Field(..., examples=[True], description="Trust has at least one U.S. owner (grantor)")
    is_us_beneficiary: bool = Field(..., examples=[False], description="Trust has at least one U.S. beneficiary")
    trust_type: TrustType = Field(..., examples=["FOREIGN_GRANTOR"])
    received_distribution: bool = Field(..., examples=[False], description="Beneficiary received a distribution")
    distribution_amount_usd: float = Field(default=0.0, ge=0, examples=[0.0])


class DistributionItem(BaseModel):
    income_type: IncomeType = Field(..., examples=["DIVIDENDS"])
    gross_amount_usd: float = Field(..., ge=0, examples=[25000.0])
    withholding_tax_usd: float = Field(default=0.0, ge=0, examples=[3750.0])
    distribution_date: str = Field(..., examples=["2024-06-15"], description="YYYY-MM-DD")
    source_country: str = Field(..., examples=["CH"], description="ISO country code")


class IncomeDistributionRequest(BaseModel):
    trust_type: TrustType = Field(..., examples=["NON_GRANTOR"])
    distributions: list[DistributionItem] = Field(..., min_length=1)


class ForeignGrantorStatementRequest(BaseModel):
    trust_name: str = Field(..., examples=["Swiss Family Trust"], max_length=200)
    trust_ein: str = Field(..., examples=["98-7654321"], description="Trust EIN (if any)")
    trust_country: str = Field(..., examples=["CH"], description="ISO country code")
    us_owner_name: str = Field(..., examples=["John Doe"], max_length=200)
    us_owner_ssn: str = Field(..., examples=["123-45-6789"])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    trust_assets_usd: float = Field(..., ge=0, examples=[500000.0])
    trust_income_usd: float = Field(..., ge=0, examples=[45000.0])
    trust_distributions_usd: float = Field(default=0.0, ge=0, examples=[20000.0])


class PenaltyCalculatorRequest(BaseModel):
    filing_deadline: str = Field(..., examples=["2024-03-15"], description="YYYY-MM-DD (typically March 15 + extension)")
    actual_filing_date: str | None = Field(default=None, examples=["2024-09-15"], description="YYYY-MM-DD or null if not filed")
    trust_gross_value_usd: float = Field(..., ge=0, examples=[500000.0], description="Gross value of trust assets")
    is_initial_failure: bool = Field(default=True, examples=[True])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/filing-requirement")
def filing_requirement(
    req: FilingRequirementRequest,
    tenant_id: Annotated[str, Depends(get_current_tenant)],
):
    """
    Determine whether Form 3520-A must be filed and by whom.

    Form 3520-A is filed BY the foreign trust (or its U.S. agent), but the
    filing requirement depends on whether there are U.S. owners or beneficiaries.
    """
    result = determine_filing_requirement(
        is_us_owner=req.is_us_owner,
        is_us_beneficiary=req.is_us_beneficiary,
        trust_type=req.trust_type,
        received_distribution=req.received_distribution,
        distribution_amount_usd=req.distribution_amount_usd,
    )
    return {"tenant_id": tenant_id, "result": result}


@router.post("/income-distribution")
def income_distribution(
    req: IncomeDistributionRequest,
    tenant_id: Annotated[str, Depends(get_current_tenant)],
):
    """
    Calculate total income distribution from foreign trust to U.S. beneficiaries.

    For non-grantor trusts, distributions are taxable to the beneficiary.
    For grantor trusts, income is taxed to the grantor regardless of distributions.
    """
    distributions = [
        IncomeDistributionItem(
            income_type=d.income_type,
            gross_amount_usd=d.gross_amount_usd,
            withholding_tax_usd=d.withholding_tax_usd,
            distribution_date=d.distribution_date,
            source_country=d.source_country,
        )
        for d in req.distributions
    ]

    result = calculate_income_distribution(
        distributions=distributions,
        trust_type=req.trust_type,
    )
    return {"tenant_id": tenant_id, "result": result}


@router.post("/foreign-grantor-statement")
def foreign_grantor_statement(
    req: ForeignGrantorStatementRequest,
    tenant_id: Annotated[str, Depends(get_current_tenant)],
):
    """
    Generate Foreign Grantor Trust Owner Statement.

    A U.S. owner of a foreign grantor trust must:
    1. Ensure the trust files Form 3520-A
    2. Provide a Foreign Grantor Trust Owner Statement to all beneficiaries
    3. Report the trust's income on their personal return
    """
    result = generate_foreign_grantor_statement(
        trust_name=req.trust_name,
        trust_ein=req.trust_ein,
        trust_country=req.trust_country,
        us_owner_name=req.us_owner_name,
        us_owner_ssn=req.us_owner_ssn,
        tax_year=req.tax_year,
        trust_assets_usd=req.trust_assets_usd,
        trust_income_usd=req.trust_income_usd,
        trust_distributions_usd=req.trust_distributions_usd,
    )
    return {"tenant_id": tenant_id, "result": result}


@router.post("/penalty-calculator")
def penalty_calculator(
    req: PenaltyCalculatorRequest,
    tenant_id: Annotated[str, Depends(get_current_tenant)],
):
    """
    Calculate penalties for failure to file Form 3520-A under IRC §6677.

    Penalties:
    - Initial failure: 5% of gross value of trust assets
    - Continued failure after 90 days: Additional 5% per 30-day period (max 25% total)
    """
    result = calculate_form3520a_penalties(
        filing_deadline=req.filing_deadline,
        actual_filing_date=req.actual_filing_date,
        trust_gross_value_usd=req.trust_gross_value_usd,
        is_initial_failure=req.is_initial_failure,
    )
    return {"tenant_id": tenant_id, "result": result}


@router.get("/overview")
def overview():
    """
    Return static overview of Form 3520-A requirements.

    No authentication required (public information).
    """
    return get_form3520a_overview()
