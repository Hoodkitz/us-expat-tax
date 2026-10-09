"""
Form 8938 FATCA (Foreign Account Tax Compliance Act) module.

Form 8938 requires US persons to report specified foreign financial assets
when the aggregate value exceeds certain thresholds:
- Single / Married Filing Separately: $50,000 (year-end) or $75,000 (any time)
- Married Filing Jointly: $100,000 (year-end) or $150,000 (any time)

Penalties:
- Failure to file: $10,000 per year
- Continued failure after IRS notice: additional $10,000 per 30-day period (max $50,000)
- Willful failure: greater of $100,000 or 50% of account value
- Criminal penalties possible for willful violations
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Filing thresholds (USD) — IRS Form 8938 Instructions (2025)
# Single / MFS: $50,000 year-end / $75,000 any time
# MFJ: $100,000 year-end / $150,000 any time
THRESHOLD_SINGLE_YEAR_END = 50_000.0
THRESHOLD_SINGLE_ANY_TIME = 75_000.0
THRESHOLD_MFJ_YEAR_END = 100_000.0
THRESHOLD_MFJ_ANY_TIME = 150_000.0

# Penalty amounts
PENALTY_FAILURE_TO_FILE = 10_000.0
PENALTY_CONTINUED_FAILURE_PER_30_DAYS = 10_000.0
PENALTY_CONTINUED_FAILURE_MAX = 50_000.0
PENALTY_WILLFUL_MINIMUM = 100_000.0
PENALTY_WILLFUL_PERCENTAGE = 0.50  # 50% of account value

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

FilingStatusLiteral = Literal["single", "mfj", "mfs", "hoh"]
AccountTypeLiteral = [
    "bank_account",
    "brokerage_account",
    "mutual_fund",
    "life_insurance",
    "pension_fund",
    "trust",
    "other",
]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class ForeignAccountInput(BaseModel):
    """A single foreign financial account."""
    account_name: str = Field(..., min_length=1, description="Name or description of the account")
    account_type: str = Field(..., description="Type of foreign financial account")
    country: str = Field(..., min_length=2, description="Country where account is held")
    max_value_usd: float = Field(..., ge=0, description="Maximum value during the tax year in USD")

class FilingRequirementInput(BaseModel):
    """Input for checking Form 8938 filing requirement."""
    filing_status: FilingStatusLiteral = Field(..., description="Filing status")
    accounts: list[ForeignAccountInput] = Field(..., description="List of foreign financial accounts")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")

class PenaltyCalculationInput(BaseModel):
    """Input for penalty calculation."""
    filing_status: FilingStatusLiteral = Field(..., description="Filing status")
    accounts: list[ForeignAccountInput] = Field(..., description="List of foreign financial accounts")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    days_unreported: int = Field(0, ge=0, description="Days the failure continues after IRS notice")
    is_willful: bool = Field(False, description="Whether the failure was willful")

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    filing_required: bool
    threshold_usd: float
    total_value_usd: float
    reasons: list[str]
    penalty_if_not_filed: float
    recommendation: str

class PenaltyResult(BaseModel):
    """Result of penalty calculation."""
    base_penalty: float
    continued_failure_penalty: float
    willful_penalty: float
    total_penalty: float
    days_unreported: int
    is_willful: bool
    explanation: str

class Form8938Overview(BaseModel):
    """Overview of Form 8938 requirements."""
    title: str
    filing_requirement: str
    thresholds: dict[str, float]
    penalties: dict[str, float]
    account_types: list[str]
    recommendation: str

# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def _get_threshold(filing_status: str) -> tuple[float, float]:
    """Return (year_end_threshold, any_time_threshold) for filing status."""
    if filing_status == "mfj":
        return THRESHOLD_MFJ_YEAR_END, THRESHOLD_MFJ_ANY_TIME
    return THRESHOLD_SINGLE_YEAR_END, THRESHOLD_SINGLE_ANY_TIME

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Determine if Form 8938 filing is required.

    Filing required if aggregate value of specified foreign financial assets
    exceeds the applicable threshold for the taxpayer's filing status.
    """
    year_end_threshold, any_time_threshold = _get_threshold(inp.filing_status)
    total_value = sum(acc.max_value_usd for acc in inp.accounts)

    reasons = []
    filing_required = False

    if total_value > year_end_threshold:
        filing_required = True
        reasons.append(
            f"Aggregate value of ${total_value:,.2f} exceeds the year-end threshold "
            f"of ${year_end_threshold:,.2f} for {inp.filing_status.upper()}"
        )

    # Check if any single account exceeds the any-time threshold
    for acc in inp.accounts:
        if acc.max_value_usd > any_time_threshold:
            filing_required = True
            reasons.append(
                f"Account '{acc.account_name}' (${acc.max_value_usd:,.2f}) exceeds "
                f"the any-time threshold of ${any_time_threshold:,.2f}"
            )

    if not filing_required:
        return FilingRequirementResult(
            filing_required=False,
            threshold_usd=year_end_threshold,
            total_value_usd=total_value,
            reasons=["Aggregate value below filing threshold"],
            penalty_if_not_filed=0.0,
            recommendation=(
                f"Form 8938 is not required. Your aggregate foreign financial assets "
                f"(${total_value:,.2f}) are below the ${year_end_threshold:,.2f} threshold "
                f"for {inp.filing_status.upper()} filers."
            ),
        )

    return FilingRequirementResult(
        filing_required=True,
        threshold_usd=year_end_threshold,
        total_value_usd=total_value,
        reasons=reasons,
        penalty_if_not_filed=PENALTY_FAILURE_TO_FILE,
        recommendation=(
            f"Form 8938 is REQUIRED. Your aggregate foreign financial assets "
            f"(${total_value:,.2f}) exceed the ${year_end_threshold:,.2f} threshold. "
            f"Failure to file can result in a ${PENALTY_FAILURE_TO_FILE:,.0f} penalty "
            f"per year, plus additional penalties for continued failure."
        ),
    )

def calculate_penalty(inp: PenaltyCalculationInput) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8938.

    Penalty structure:
    - Base penalty: $10,000 per year
    - Continued failure: $10,000 per 30-day period after IRS notice (max $50,000)
    - Willful failure: greater of $100,000 or 50% of account value
    """
    total_value = sum(acc.max_value_usd for acc in inp.accounts)

    # Base penalty
    base_penalty = PENALTY_FAILURE_TO_FILE

    # Continued failure penalty (after IRS notice)
    if inp.days_unreported > 0:
        periods = (inp.days_unreported + 29) // 30  # Ceiling division
        continued_penalty = min(
            periods * PENALTY_CONTINUED_FAILURE_PER_30_DAYS,
            PENALTY_CONTINUED_FAILURE_MAX,
        )
    else:
        continued_penalty = 0.0

    # Willful penalty
    if inp.is_willful:
        willful_penalty = max(
            PENALTY_WILLFUL_MINIMUM,
            total_value * PENALTY_WILLFUL_PERCENTAGE,
        )
    else:
        willful_penalty = 0.0

    total_penalty = base_penalty + continued_penalty + willful_penalty

    # Build explanation
    parts = [
        f"Base penalty for failure to file Form 8938: ${base_penalty:,.2f}."
    ]

    if continued_penalty > 0:
        parts.append(
            f"Continued failure penalty ({inp.days_unreported} days after IRS notice): "
            f"${continued_penalty:,.2f}."
        )

    if willful_penalty > 0:
        parts.append(
            f"Willful failure penalty (greater of ${PENALTY_WILLFUL_MINIMUM:,.0f} or "
            f"50% of ${total_value:,.2f} account value): ${willful_penalty:,.2f}."
        )

    parts.append(f"Total penalty: ${total_penalty:,.2f}.")

    explanation = " ".join(parts)

    return PenaltyResult(
        base_penalty=base_penalty,
        continued_failure_penalty=continued_penalty,
        willful_penalty=willful_penalty,
        total_penalty=total_penalty,
        days_unreported=inp.days_unreported,
        is_willful=inp.is_willful,
        explanation=explanation,
    )

def get_overview() -> Form8938Overview:
    """Return overview of Form 8938 FATCA reporting requirements."""
    return Form8938Overview(
        title="Form 8938: FATCA Foreign Financial Asset Reporting",
        filing_requirement=(
            "Form 8938 is required for US persons (citizens, residents, and certain "
            "domestic entities) who hold specified foreign financial assets with an "
            "aggregate value exceeding the applicable threshold. This includes foreign "
            "bank accounts, brokerage accounts, mutual funds, life insurance policies, "
            "pension funds, and certain foreign trusts."
        ),
        thresholds={
            "single_year_end": THRESHOLD_SINGLE_YEAR_END,
            "single_any_time": THRESHOLD_SINGLE_ANY_TIME,
            "mfj_year_end": THRESHOLD_MFJ_YEAR_END,
            "mfj_any_time": THRESHOLD_MFJ_ANY_TIME,
        },
        penalties={
            "failure_to_file": PENALTY_FAILURE_TO_FILE,
            "continued_failure_per_30_days": PENALTY_CONTINUED_FAILURE_PER_30_DAYS,
            "continued_failure_max": PENALTY_CONTINUED_FAILURE_MAX,
            "willful_minimum": PENALTY_WILLFUL_MINIMUM,
            "willful_percentage": PENALTY_WILLFUL_PERCENTAGE * 100,
        },
        account_types=[
            "Bank accounts (checking, savings, time deposits)",
            "Brokerage accounts (stocks, bonds, securities)",
            "Mutual funds and ETFs",
            "Life insurance policies with cash value",
            "Pension funds and retirement accounts",
            "Foreign trusts and estates",
            "Other financial instruments",
        ],
        recommendation=(
            "If you hold foreign financial assets, consult a tax professional "
            "specializing in international tax reporting. FATCA compliance is complex "
            "and penalties for non-compliance are severe. The IRS has increased "
            "enforcement of foreign asset reporting requirements in recent years."
        ),
    )
