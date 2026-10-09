"""
Schedule R — Credit for the Elderly or the Disabled.

Business logic for Schedule R calculations under IRC §22 and §37.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


# 2025 Tax Constants
BASE_AMOUNT_SINGLE = 5_000.0
BASE_AMOUNT_MARRIED_BOTH_65 = 7_500.0
BASE_AMOUNT_MARRIED_ONE_65 = 5_000.0
BASE_AMOUNT_MARRIED_SEPARATE = 3_750.0

# AGI threshold for 50% reduction
AGI_THRESHOLD_SINGLE = 7_500.0
AGI_THRESHOLD_MARRIED_JOINTLY = 10_000.0
AGI_THRESHOLD_MARRIED_SEPARATELY = 5_000.0

# Credit rate
CREDIT_RATE = 0.15  # 15%

FilingStatus = Literal[
    "single",
    "married_filing_jointly",
    "married_filing_separately",
    "head_of_household",
    "qualifying_widow",
]


class ScheduleRInput(BaseModel):
    """Input for Schedule R calculation."""

    filing_status: FilingStatus = Field(
        default="single",
        description="Tax filing status",
    )
    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Taxpayer age (must be 65+ or disabled)",
    )
    spouse_age: int | None = Field(
        default=None,
        ge=0,
        le=120,
        description="Spouse age (if married filing jointly)",
    )
    is_disabled: bool = Field(
        default=False,
        description="Whether taxpayer is permanently and totally disabled",
    )
    spouse_is_disabled: bool = Field(
        default=False,
        description="Whether spouse is permanently and totally disabled",
    )
    agi: float = Field(
        ...,
        ge=0,
        description="Adjusted gross income",
    )
    nontaxable_social_security: float = Field(
        default=0.0,
        ge=0,
        description="Nontaxable Social Security benefits",
    )
    nontaxable_pension: float = Field(
        default=0.0,
        ge=0,
        description="Nontaxable pension or annuity income",
    )
    nontaxable_other: float = Field(
        default=0.0,
        ge=0,
        description="Other nontaxable income (e.g., nontaxable railroad retirement)",
    )
    tax_year: int = Field(
        default=2025,
        ge=2025,
        le=2025,
        description="Tax year (only 2025 supported)",
    )


class ScheduleRResult(BaseModel):
    """Schedule R calculation result."""

    filing_status: str
    base_amount: float
    total_nontaxable_income: float
    agi_threshold: float
    excess_agi: float
    agi_reduction: float
    total_reduction: float
    credit_before_rate: float
    credit_rate: float
    credit_amount: float
    eligible: bool
    explanation: str


def _get_base_amount(
    filing_status: str,
    age: int,
    spouse_age: int | None,
    is_disabled: bool,
    spouse_is_disabled: bool,
) -> float:
    """Determine the base amount based on filing status and age/disability."""
    if filing_status == "married_filing_jointly":
        # Both 65+ or disabled → $7,500
        # Only one 65+ or disabled → $5,000
        taxpayer_qualified = age >= 65 or is_disabled
        spouse_qualified = (spouse_age is not None and spouse_age >= 65) or spouse_is_disabled
        if taxpayer_qualified and spouse_qualified:
            return BASE_AMOUNT_MARRIED_BOTH_65
        elif taxpayer_qualified or spouse_qualified:
            return BASE_AMOUNT_MARRIED_ONE_65
        else:
            return 0.0
    elif filing_status == "married_filing_separately":
        return BASE_AMOUNT_MARRIED_SEPARATE
    else:
        # Single, head of household, qualifying widow
        return BASE_AMOUNT_SINGLE


def _get_agi_threshold(filing_status: str) -> float:
    """Get the AGI threshold for the 50% reduction."""
    if filing_status == "married_filing_jointly":
        return AGI_THRESHOLD_MARRIED_JOINTLY
    elif filing_status == "married_filing_separately":
        return AGI_THRESHOLD_MARRIED_SEPARATELY
    else:
        return AGI_THRESHOLD_SINGLE


def _is_eligible(
    age: int,
    spouse_age: int | None,
    is_disabled: bool,
    spouse_is_disabled: bool,
    filing_status: str,
) -> bool:
    """Check if taxpayer is eligible for Schedule R."""
    if filing_status == "married_filing_jointly":
        taxpayer_qualified = age >= 65 or is_disabled
        spouse_qualified = (spouse_age is not None and spouse_age >= 65) or spouse_is_disabled
        return taxpayer_qualified or spouse_qualified
    else:
        return age >= 65 or is_disabled


def calculate_schedule_r(input_data: ScheduleRInput) -> ScheduleRResult:
    """
    Calculate Schedule R credit for the elderly or disabled.

    Steps:
    1. Check eligibility (age 65+ or disabled)
    2. Determine base amount based on filing status
    3. Sum all nontaxable income (SS, pension, other)
    4. Subtract nontaxable income from base amount
    5. Calculate AGI reduction: 50% of AGI over threshold
    6. Subtract AGI reduction from remaining amount
    7. Multiply by 15% to get final credit
    """
    eligible = _is_eligible(
        input_data.age,
        input_data.spouse_age,
        input_data.is_disabled,
        input_data.spouse_is_disabled,
        input_data.filing_status,
    )

    if not eligible:
        return ScheduleRResult(
            filing_status=input_data.filing_status,
            base_amount=0.0,
            total_nontaxable_income=0.0,
            agi_threshold=0.0,
            excess_agi=0.0,
            agi_reduction=0.0,
            total_reduction=0.0,
            credit_before_rate=0.0,
            credit_rate=CREDIT_RATE,
            credit_amount=0.0,
            eligible=False,
            explanation="Not eligible: taxpayer must be 65 or older, or permanently and totally disabled.",
        )

    # Step 2: Base amount
    base_amount = _get_base_amount(
        input_data.filing_status,
        input_data.age,
        input_data.spouse_age,
        input_data.is_disabled,
        input_data.spouse_is_disabled,
    )

    # Step 3: Total nontaxable income
    total_nontaxable = (
        input_data.nontaxable_social_security
        + input_data.nontaxable_pension
        + input_data.nontaxable_other
    )

    # Step 4: Subtract nontaxable income from base
    remaining_after_nontaxable = max(0.0, base_amount - total_nontaxable)

    # Step 5: AGI reduction (50% of AGI over threshold)
    agi_threshold = _get_agi_threshold(input_data.filing_status)
    excess_agi = max(0.0, input_data.agi - agi_threshold)
    agi_reduction = excess_agi * 0.5

    # Step 6: Subtract AGI reduction
    total_reduction = total_nontaxable + agi_reduction
    credit_before_rate = max(0.0, base_amount - total_reduction)

    # Step 7: Apply 15% rate
    credit_amount = round(credit_before_rate * CREDIT_RATE, 2)

    explanation = (
        f"Schedule R Credit: ${credit_amount:,.2f}. "
        f"Base amount: ${base_amount:,.2f}, "
        f"less nontaxable income: ${total_nontaxable:,.2f}, "
        f"less AGI reduction (50% of ${excess_agi:,.2f} excess): ${agi_reduction:,.2f}, "
        f"× 15% = ${credit_amount:,.2f}."
    )

    return ScheduleRResult(
        filing_status=input_data.filing_status,
        base_amount=round(base_amount, 2),
        total_nontaxable_income=round(total_nontaxable, 2),
        agi_threshold=round(agi_threshold, 2),
        excess_agi=round(excess_agi, 2),
        agi_reduction=round(agi_reduction, 2),
        total_reduction=round(total_reduction, 2),
        credit_before_rate=round(credit_before_rate, 2),
        credit_rate=CREDIT_RATE,
        credit_amount=credit_amount,
        eligible=True,
        explanation=explanation,
    )


def get_schedule_r_overview() -> dict:
    """Return a summary of Schedule R law and calculation rules."""
    return {
        "title": "Schedule R: Credit for the Elderly or the Disabled",
        "statutory_authority": [
            "IRC §22 — Credit for the elderly",
            "IRC §37 — Credit for the elderly or the disabled (prior law)",
            "IRC §86 — Social Security and tier 1 railroad retirement benefits",
        ],
        "tax_year": 2025,
        "eligibility": {
            "age_requirement": "Taxpayer must be 65 or older by end of tax year",
            "disability_requirement": "Permanently and total disabled (physician certification required)",
            "married_filing_jointly": "Either spouse can qualify the couple",
        },
        "base_amounts": {
            "single": f"${BASE_AMOUNT_SINGLE:,.0f}",
            "married_filing_jointly_both_65": f"${BASE_AMOUNT_MARRIED_BOTH_65:,.0f}",
            "married_filing_jointly_one_65": f"${BASE_AMOUNT_MARRIED_ONE_65:,.0f}",
            "married_filing_separately": f"${BASE_AMOUNT_MARRIED_SEPARATE:,.0f}",
        },
        "agi_thresholds": {
            "single": f"${AGI_THRESHOLD_SINGLE:,.0f}",
            "married_filing_jointly": f"${AGI_THRESHOLD_MARRIED_JOINTLY:,.0f}",
            "married_filing_separately": f"${AGI_THRESHOLD_MARRIED_SEPARATELY:,.0f}",
        },
        "calculation_steps": [
            "1. Determine eligibility (age 65+ or disabled)",
            "2. Determine base amount based on filing status",
            "3. Sum nontaxable income (Social Security, pensions, other)",
            "4. Subtract nontaxable income from base amount",
            "5. Calculate AGI reduction: 50% of AGI over threshold",
            "6. Subtract AGI reduction from remaining amount",
            "7. Multiply result by 15% to get final credit",
        ],
        "notes": [
            "Credit is nonrefundable — can only reduce tax liability to zero",
            "Nontaxable Social Security includes benefits not included in gross income",
            "Nontaxable pensions include veterans' benefits and certain railroad retirement",
            "AGI reduction is 50% of AGI exceeding the filing-status threshold",
            "Maximum credit is approximately $5,000 for single filers",
        ],
    }
