"""
Form 3520-A Foreign Trust Annual Information Return Router.

POST /api/v1/form3520a/filing-requirement    – JWT-protected: determine filing obligation (§6048)
POST /api/v1/form3520a/trust-activity        – JWT-protected: calculate trust accounting & distributions
POST /api/v1/form3520a/beneficiary-reporting – JWT-protected: beneficiary statement obligations
POST /api/v1/form3520a/penalty-calculator    – JWT-protected: IRC §6677 penalty calculations
GET  /api/v1/form3520a/overview              – static overview of Form 3520-A
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.utils import get_current_tenant

router = APIRouter(tags=["form3520a"])

# ---------------------------------------------------------------------------
# Constants & Thresholds
# ---------------------------------------------------------------------------

BASE_PENALTY_USD = 10_000.0
PENALTY_RATE_PER_MONTH = 0.05  # 5% of trust corpus per month
ENHANCED_PENALTY_RATE = 0.35   # 35% if no US Agent + books/records denied
MARCH_15_DEADLINE = "March 15"

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

TrustType = Literal["GRANTOR", "NON_GRANTOR", "SIMPLE", "COMPLEX"]
DistributionType = Literal["INCOME", "PRINCIPAL", "MIXED"]


class FilingRequirementRequest(BaseModel):
    """Determine if Form 3520-A is required."""
    is_us_owner: bool = Field(..., examples=[True], description="Is there a US owner of the foreign trust?")
    is_us_beneficiary: bool = Field(..., examples=[True], description="Is there a US beneficiary?")
    trust_name: str = Field(..., min_length=1, examples=["Luxembourg Family Trust"])
    trust_country: str = Field(..., examples=["LU"])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])
    has_us_agent: bool = Field(default=False, examples=[False], description="Has the trust designated a US agent?")


class TrustActivityRequest(BaseModel):
    """Trust accounting & distributions for Form 3520-A."""
    trust_type: TrustType = Field(..., examples=["COMPLEX"])
    trust_corpus_usd: float = Field(..., ge=0, examples=[500_000.0], description="Total trust corpus/assets")
    gross_income_usd: float = Field(..., ge=0, examples=[25_000.0])
    trust_expenses_usd: float = Field(..., ge=0, examples=[5_000.0])
    distributions_to_us_beneficiaries_usd: float = Field(..., ge=0, examples=[15_000.0])
    distributions_to_foreign_beneficiaries_usd: float = Field(..., ge=0, examples=[0.0])
    capital_gains_usd: float = Field(default=0.0, ge=0, examples=[10_000.0])
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class BeneficiaryItem(BaseModel):
    """Individual US beneficiary."""
    name: str = Field(..., min_length=1, examples=["John Doe"])
    ssn_or_itin: str = Field(..., examples=["123-45-6789"])
    distribution_amount_usd: float = Field(..., ge=0, examples=[15_000.0])
    distribution_type: DistributionType = Field(..., examples=["INCOME"])
    is_income_distribution: bool = Field(..., examples=[True])


class BeneficiaryReportingRequest(BaseModel):
    """Beneficiary Statement obligations (provided to each US beneficiary by March 15)."""
    beneficiaries: list[BeneficiaryItem] = Field(..., min_length=1)
    trust_name: str = Field(..., min_length=1, examples=["Luxembourg Family Trust"])
    trust_ein: str = Field(..., examples=["12-3456789"], description="Trust EIN (if applicable)")
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


class PenaltyCalculatorRequest(BaseModel):
    """Calculate IRC §6677 penalties for Form 3520-A non-compliance."""
    trust_corpus_usd: float = Field(..., ge=0, examples=[500_000.0])
    months_late: int = Field(..., ge=0, le=60, examples=[6], description="Months past the deadline")
    has_us_agent: bool = Field(..., examples=[False])
    books_and_records_provided: bool = Field(..., examples=[False], description="Were books/records provided upon IRS request?")
    tax_year: int = Field(..., ge=2000, le=2099, examples=[2024])


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------

def _determine_filing_requirement(req: FilingRequirementRequest) -> dict:
    """
    Form 3520-A must be filed by the foreign trust if it has a US owner.
    The trust must also furnish Beneficiary Statements to all US beneficiaries by March 15.
    IRC § 6048(b).
    """
    must_file = False
    reasons: list[str] = []

    if req.is_us_owner:
        must_file = True
        reasons.append(
            f"Form 3520-A is REQUIRED: {req.trust_name} has a US owner. "
            "Under IRC § 6048(b), the foreign trust must file Form 3520-A annually."
        )

    if req.is_us_beneficiary:
        reasons.append(
            f"The foreign trust must provide a Beneficiary Statement (Part III of Form 3520-A) "
            f"to each US beneficiary by {MARCH_15_DEADLINE} following the tax year end."
        )

    if not req.has_us_agent:
        reasons.append(
            "⚠ WARNING: No US agent designated. Failure to designate a US agent and provide books/records "
            "to the IRS can trigger a 35% penalty on gross reportable amounts (IRC § 6677(a))."
        )

    if not reasons:
        reasons.append(
            "No Form 3520-A filing obligation identified. "
            "Verify US ownership/beneficiary status with a qualified tax professional."
        )

    due_date = f"{MARCH_15_DEADLINE}, {req.tax_year + 1} (15th day of 3rd month after tax year end; 6-month extension available via Form 7004)"

    return {
        "must_file": must_file,
        "trust_name": req.trust_name,
        "trust_country": req.trust_country,
        "reasons": reasons,
        "filing_deadline": due_date,
        "statutory_reference": "IRC § 6048(b)",
        "beneficiary_statement_deadline": f"{MARCH_15_DEADLINE}, {req.tax_year + 1}",
    }


def _calculate_trust_activity(req: TrustActivityRequest) -> dict:
    """
    Calculate trust accounting income and distributions.
    Form 3520-A Part I: Trust Information & Accounting.
    """
    net_income = req.gross_income_usd - req.trust_expenses_usd + req.capital_gains_usd
    total_distributions = req.distributions_to_us_beneficiaries_usd + req.distributions_to_foreign_beneficiaries_usd

    distributable_net_income = max(net_income - req.capital_gains_usd, 0.0)
    
    # Simple trust: must distribute all income annually
    # Complex trust: may accumulate income
    is_simple = req.trust_type == "SIMPLE"
    
    undistributed_income = max(net_income - total_distributions, 0.0) if not is_simple else 0.0

    reporting_items = [
        f"Gross Income: {_fmt_usd(req.gross_income_usd)}",
        f"Trust Expenses: {_fmt_usd(req.trust_expenses_usd)}",
        f"Capital Gains: {_fmt_usd(req.capital_gains_usd)}",
        f"Net Income: {_fmt_usd(net_income)}",
        f"Distributable Net Income (DNI): {_fmt_usd(distributable_net_income)}",
        f"Distributions to US Beneficiaries: {_fmt_usd(req.distributions_to_us_beneficiaries_usd)}",
        f"Distributions to Foreign Beneficiaries: {_fmt_usd(req.distributions_to_foreign_beneficiaries_usd)}",
    ]

    if undistributed_income > 0:
        reporting_items.append(
            f"⚠ Undistributed Income: {_fmt_usd(undistributed_income)} (accumulated in trust)"
        )

    return {
        "trust_type": req.trust_type,
        "trust_corpus_usd": round(req.trust_corpus_usd, 2),
        "gross_income_usd": round(req.gross_income_usd, 2),
        "net_income_usd": round(net_income, 2),
        "distributable_net_income_usd": round(distributable_net_income, 2),
        "total_distributions_usd": round(total_distributions, 2),
        "distributions_to_us_beneficiaries_usd": round(req.distributions_to_us_beneficiaries_usd, 2),
        "distributions_to_foreign_beneficiaries_usd": round(req.distributions_to_foreign_beneficiaries_usd, 2),
        "undistributed_income_usd": round(undistributed_income, 2),
        "reporting_items": reporting_items,
        "form_section": "Form 3520-A Part I: Trust Information, Accounting Income and Balance Sheet",
    }


def _beneficiary_reporting(req: BeneficiaryReportingRequest) -> dict:
    """
    Generate Beneficiary Statement obligations.
    Each US beneficiary must receive a Foreign Grantor Trust Beneficiary Statement by March 15.
    """
    total_distributed = sum(b.distribution_amount_usd for b in req.beneficiaries)
    
    beneficiary_summaries = []
    for b in req.beneficiaries:
        beneficiary_summaries.append({
            "name": b.name,
            "ssn_or_itin": b.ssn_or_itin,
            "distribution_amount_usd": round(b.distribution_amount_usd, 2),
            "distribution_type": b.distribution_type,
            "is_income_distribution": b.is_income_distribution,
        })

    statement_requirements = [
        f"The trust must provide a Foreign Grantor Trust Beneficiary Statement to each US beneficiary by {MARCH_15_DEADLINE}, {req.tax_year + 1}.",
        "The statement must include: trust name, EIN (if any), trust address, amount and type of distribution, and whether it is income or corpus.",
        "US beneficiaries use this statement to complete Part III of their personal Form 3520.",
        "Failure to provide the statement can result in the trust being subject to penalties under IRC § 6677.",
    ]

    return {
        "trust_name": req.trust_name,
        "trust_ein": req.trust_ein,
        "beneficiary_count": len(req.beneficiaries),
        "total_distributions_usd": round(total_distributed, 2),
        "beneficiaries": beneficiary_summaries,
        "statement_deadline": f"{MARCH_15_DEADLINE}, {req.tax_year + 1}",
        "statement_requirements": statement_requirements,
        "form_reference": "Form 3520-A Part III: Beneficiary Statement",
    }


def _calculate_penalty(req: PenaltyCalculatorRequest) -> dict:
    """
    Calculate IRC § 6677 penalties for late/non-filing of Form 3520-A.
    
    Base penalty: $10,000
    Additional penalty: 5% of trust corpus per month (or part thereof) that the return is late
    Enhanced penalty: 35% if no US Agent designated AND books/records not provided upon IRS examination
    """
    base_penalty = BASE_PENALTY_USD
    
    # 5% per month penalty
    monthly_penalty = req.trust_corpus_usd * PENALTY_RATE_PER_MONTH * req.months_late
    
    # Enhanced penalty if no US Agent + books/records denied
    enhanced_penalty = 0.0
    enhanced_applicable = False
    if not req.has_us_agent and not req.books_and_records_provided:
        enhanced_penalty = req.trust_corpus_usd * ENHANCED_PENALTY_RATE
        enhanced_applicable = True

    # Total penalty is the GREATER of base + monthly OR enhanced
    total_penalty_standard = base_penalty + monthly_penalty
    total_penalty = max(total_penalty_standard, enhanced_penalty) if enhanced_applicable else total_penalty_standard

    penalty_breakdown = [
        f"Base Penalty: {_fmt_usd(base_penalty)} (IRC § 6677(a))",
        f"Monthly Penalty: {_fmt_usd(monthly_penalty)} ({req.months_late} months × 5% of corpus)",
    ]

    if enhanced_applicable:
        penalty_breakdown.append(
            f"⚠ ENHANCED PENALTY APPLIES: {_fmt_usd(enhanced_penalty)} (35% of trust corpus) — "
            "No US Agent designated AND books/records not provided during IRS examination."
        )
        penalty_breakdown.append(
            f"Total Penalty: {_fmt_usd(total_penalty)} (greater of standard or enhanced penalty)"
        )
    else:
        penalty_breakdown.append(f"Total Penalty: {_fmt_usd(total_penalty)}")

    mitigation_steps = []
    if req.months_late > 0:
        mitigation_steps.append("File Form 3520-A immediately to stop penalty accrual.")
    if not req.has_us_agent:
        mitigation_steps.append("Designate a US Agent (authorized to accept IRS service and provide books/records).")
    if not req.books_and_records_provided:
        mitigation_steps.append("Provide all requested books and records to the IRS to avoid the 35% enhanced penalty.")
    if not mitigation_steps:
        mitigation_steps.append("Trust is in compliance; no immediate action required.")

    return {
        "base_penalty_usd": round(base_penalty, 2),
        "monthly_penalty_usd": round(monthly_penalty, 2),
        "enhanced_penalty_usd": round(enhanced_penalty, 2) if enhanced_applicable else 0.0,
        "enhanced_penalty_applicable": enhanced_applicable,
        "total_penalty_usd": round(total_penalty, 2),
        "months_late": req.months_late,
        "penalty_breakdown": penalty_breakdown,
        "mitigation_steps": mitigation_steps,
        "statutory_reference": "IRC § 6677(a) and (b)",
    }


def _fmt_usd(val: float) -> str:
    """Format USD amounts."""
    return f"${val:,.2f}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/filing-requirement")
async def filing_requirement(
    payload: FilingRequirementRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Determine whether a foreign trust must file Form 3520-A.
    Requires a valid JWT (Bearer token).
    """
    return _determine_filing_requirement(payload)


@router.post("/trust-activity")
async def trust_activity(
    payload: TrustActivityRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate trust accounting income, distributions, and reporting items for Form 3520-A Part I.
    Requires a valid JWT (Bearer token).
    """
    return _calculate_trust_activity(payload)


@router.post("/beneficiary-reporting")
async def beneficiary_reporting(
    payload: BeneficiaryReportingRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Generate Beneficiary Statement obligations (Form 3520-A Part III).
    Requires a valid JWT (Bearer token).
    """
    return _beneficiary_reporting(payload)


@router.post("/penalty-calculator")
async def penalty_calculator(
    payload: PenaltyCalculatorRequest,
    current_tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """
    Calculate IRC § 6677 penalties for late/non-filing of Form 3520-A.
    Requires a valid JWT (Bearer token).
    """
    return _calculate_penalty(payload)


@router.get("/overview")
async def overview() -> dict:
    """
    Static overview of Form 3520-A — no authentication required.
    """
    return {
        "form": "Form 3520-A",
        "title": "Annual Information Return of Foreign Trust With a U.S. Owner",
        "purpose": (
            "Form 3520-A is filed by a foreign trust that has at least one U.S. owner. "
            "The form reports trust income, deductions, assets, and distributions. "
            "The foreign trust must also provide a Beneficiary Statement to each U.S. beneficiary by March 15."
        ),
        "who_must_file": [
            "The foreign trust itself (if it has a U.S. owner under IRC § 671-679).",
            "The trust must designate a U.S. Agent authorized to accept IRS service and provide books/records.",
        ],
        "filing_deadline": f"{MARCH_15_DEADLINE} (15th day of 3rd month after tax year end; 6-month extension via Form 7004)",
        "beneficiary_statement_deadline": f"{MARCH_15_DEADLINE} (Foreign Grantor Trust Beneficiary Statement to each U.S. beneficiary)",
        "penalties": {
            "base_penalty_usd": BASE_PENALTY_USD,
            "monthly_penalty": f"{int(PENALTY_RATE_PER_MONTH * 100)}% of trust corpus per month (or part thereof) that the return is late",
            "enhanced_penalty": f"{int(ENHANCED_PENALTY_RATE * 100)}% of gross reportable amount if no U.S. Agent designated AND books/records not provided during IRS examination",
            "statutory_reference": "IRC § 6677(a) and (b)",
        },
        "key_requirements": [
            "Foreign trust must have a U.S. owner (grantor trust rules apply).",
            "U.S. owner must file Form 3520 (separate from Form 3520-A) to report ownership.",
            "Beneficiary Statements must be provided to all U.S. beneficiaries by March 15.",
            "Trust must designate a U.S. Agent to avoid enhanced penalties.",
        ],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-3520-a",
    }
