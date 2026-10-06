"""
Form 8865 – Return of U.S. Persons With Respect to Certain Foreign Partnerships.

Form 8865 is required by U.S. persons who:
- Control a foreign partnership (Category 1: >50% interest)
- Own 10%+ interest in a foreign partnership controlled by U.S. persons (Category 2)
- Have a reportable event (Category 3: acquisition/disposition/change in interest ≥10%)
- Contribute property worth >$100,000 (Category 4)
- Own 10%+ interest in a foreign partnership (Category 5, post-2020)

Penalties (IRC §6679):
- Failure to file: $10,000 per tax year
- Continued failure after IRS notice: additional $10,000 per 30-day period (up to $50,000)
- Willful failure: criminal penalties possible

Subpart F / GILTI / §199A QBI considerations apply.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Filing thresholds
CATEGORY_1_CONTROL_THRESHOLD = 0.50  # >50% interest
CATEGORY_2_OWNERSHIP_THRESHOLD = 0.10  # ≥10% interest
CATEGORY_3_EVENT_THRESHOLD = 0.10  # ≥10% interest change
CATEGORY_4_CONTRIBUTION_THRESHOLD = 100_000.0  # $100k property contribution
CATEGORY_5_OWNERSHIP_THRESHOLD = 0.10  # ≥10% interest (post-2020)

# Penalty amounts (IRC §6679)
PENALTY_BASE = 10_000.0
PENALTY_CONTINUED_PER_30_DAYS = 10_000.0
PENALTY_CONTINUED_MAX = 50_000.0
PENALTY_WILLFUL_PERCENTAGE = 0.50  # 50% of partnership value (if determinable)

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

CategoryLiteral = Literal["category_1", "category_2", "category_3", "category_4", "category_5"]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class PartnershipInput(BaseModel):
    """A single foreign partnership interest."""
    name: str = Field(..., min_length=1, description="Name of the foreign partnership")
    country: str = Field(..., min_length=2, description="Country where partnership is organized")
    ownership_percentage: float = Field(..., ge=0.0, le=100.0, description="Ownership % (0-100)")
    us_controlled: bool = Field(False, description="Whether U.S. persons control >50% of the partnership")
    fair_market_value_usd: float = Field(0.0, ge=0.0, description="FMV of partnership interest (USD)")
    capital_contributed_usd: float = Field(0.0, ge=0.0, description="Capital contributed this year (USD)")
    reportable_event: bool = Field(False, description="Acquisition/disposition/change ≥10% this year")


class FilingRequirementInput(BaseModel):
    """Input for checking Form 8865 filing requirement."""
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    partnerships: list[PartnershipInput] = Field(..., description="List of foreign partnership interests")


class IncomeSummaryInput(BaseModel):
    """Input for partnership income summary (Subpart F, GILTI, QBI)."""
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    partnership_name: str = Field(..., min_length=1, description="Name of the foreign partnership")
    subpart_f_income_usd: float = Field(0.0, description="Subpart F income (CFC context, USD)")
    gilti_usd: float = Field(0.0, description="GILTI (Global Intangible Low-Taxed Income, USD)")
    qbi_199a_usd: float = Field(0.0, description="Qualified Business Income under §199A (USD)")
    ordinary_income_usd: float = Field(0.0, description="Ordinary business income (USD)")
    capital_gain_usd: float = Field(0.0, description="Capital gain (USD)")
    foreign_tax_paid_usd: float = Field(0.0, ge=0.0, description="Foreign taxes paid (USD)")


class PenaltyCalculationInput(BaseModel):
    """Input for penalty calculation."""
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    partnerships: list[PartnershipInput] = Field(..., description="List of foreign partnership interests")
    days_unreported: int = Field(0, ge=0, description="Days the failure continues after IRS notice")
    is_willful: bool = Field(False, description="Whether the failure was willful")


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    filing_required: bool
    categories: list[str]  # Which Category 1-5 apply
    total_partnerships: int
    reasons: list[str]
    penalty_if_not_filed: float
    recommendation: str


class IncomeSummaryResult(BaseModel):
    """Result of income summary calculation."""
    partnership_name: str
    subpart_f_income_usd: float
    gilti_usd: float
    qbi_199a_usd: float
    ordinary_income_usd: float
    capital_gain_usd: float
    foreign_tax_paid_usd: float
    total_income_usd: float
    foreign_tax_credit_eligible: bool
    notes: list[str]


class PenaltyResult(BaseModel):
    """Result of penalty calculation."""
    base_penalty: float
    continued_failure_penalty: float
    willful_penalty: float
    total_penalty: float
    days_unreported: int
    is_willful: bool
    explanation: str


class Form8865Overview(BaseModel):
    """Overview of Form 8865 requirements."""
    title: str
    description: str
    category_1: str
    category_2: str
    category_3: str
    category_4: str
    category_5: str
    penalties: str
    filing_deadline: str
    recommendation: str


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Check if the taxpayer has a filing requirement for Form 8865.

    Categories:
    1. Control: >50% interest (direct/indirect/constructive)
    2. Ownership: ≥10% interest in a U.S.-controlled foreign partnership
    3. Reportable event: acquisition/disposition/change ≥10%
    4. Contribution: property worth >$100,000
    5. Ownership: ≥10% interest (post-2020, simplified reporting)
    """
    reasons: list[str] = []
    categories: list[str] = []

    for p in inp.partnerships:
        ownership_frac = p.ownership_percentage / 100.0

        # Category 1: Control (>50%)
        if ownership_frac > CATEGORY_1_CONTROL_THRESHOLD:
            categories.append("Category 1: Control")
            reasons.append(
                f"You control '{p.name}' ({p.ownership_percentage:.1f}% > 50%). "
                f"Category 1 filer (constructive ownership rules apply)."
            )

        # Category 2: ≥10% ownership in U.S.-controlled partnership
        if ownership_frac >= CATEGORY_2_OWNERSHIP_THRESHOLD and p.us_controlled:
            categories.append("Category 2: Ownership (U.S.-controlled)")
            reasons.append(
                f"You own {p.ownership_percentage:.1f}% of U.S.-controlled partnership '{p.name}'. "
                f"Category 2 filer."
            )

        # Category 3: Reportable event (≥10% change)
        if p.reportable_event and ownership_frac >= CATEGORY_3_EVENT_THRESHOLD:
            categories.append("Category 3: Reportable Event")
            reasons.append(
                f"Reportable event (acquisition/disposition/change ≥10%) for '{p.name}'. "
                f"Category 3 filer."
            )

        # Category 4: Contribution >$100k
        if p.capital_contributed_usd > CATEGORY_4_CONTRIBUTION_THRESHOLD:
            categories.append("Category 4: Contribution")
            reasons.append(
                f"You contributed ${p.capital_contributed_usd:,.0f} to '{p.name}' "
                f"(>${CATEGORY_4_CONTRIBUTION_THRESHOLD:,.0f} threshold). Category 4 filer."
            )

        # Category 5: ≥10% ownership (post-2020)
        if ownership_frac >= CATEGORY_5_OWNERSHIP_THRESHOLD:
            categories.append("Category 5: Ownership (≥10%)")
            reasons.append(
                f"You own {p.ownership_percentage:.1f}% of '{p.name}' (≥10%). "
                f"Category 5 filer (post-2020 rules)."
            )

    # Deduplicate categories
    categories = sorted(set(categories))

    filing_required = len(categories) > 0

    if not filing_required:
        reasons.append(
            "No filing requirement: none of the 5 categories apply. "
            "Verify ownership percentages and U.S. control status."
        )
        recommendation = (
            "Form 8865 is not required based on the information provided. "
            "However, consult a tax professional to verify constructive ownership "
            "and indirect control rules."
        )
    else:
        recommendation = (
            f"Form 8865 is REQUIRED for {inp.tax_year}. "
            f"You must file under: {', '.join(categories)}. "
            f"Filing deadline: typically April 15 (or October 15 with extension). "
            f"Attach Form 8865 to your Form 1040."
        )

    return FilingRequirementResult(
        filing_required=filing_required,
        categories=categories,
        total_partnerships=len(inp.partnerships),
        reasons=reasons,
        penalty_if_not_filed=PENALTY_BASE if filing_required else 0.0,
        recommendation=recommendation,
    )


def summarize_income(inp: IncomeSummaryInput) -> IncomeSummaryResult:
    """
    Summarize partnership income for tax reporting.

    Includes:
    - Subpart F income (if partnership owns CFC)
    - GILTI (Global Intangible Low-Taxed Income)
    - QBI (Qualified Business Income under §199A)
    - Ordinary income, capital gains
    - Foreign tax credit eligibility
    """
    notes: list[str] = []

    total_income = (
        inp.subpart_f_income_usd
        + inp.gilti_usd
        + inp.qbi_199a_usd
        + inp.ordinary_income_usd
        + inp.capital_gain_usd
    )

    # Foreign tax credit eligibility
    ftc_eligible = inp.foreign_tax_paid_usd > 0
    if ftc_eligible:
        notes.append(
            f"Foreign taxes paid: ${inp.foreign_tax_paid_usd:,.2f}. "
            f"May be eligible for Foreign Tax Credit (Form 1116) or deduction."
        )

    # Subpart F
    if inp.subpart_f_income_usd > 0:
        notes.append(
            f"Subpart F income: ${inp.subpart_f_income_usd:,.2f}. "
            f"Reportable if partnership owns ≥10% of CFC."
        )

    # GILTI
    if inp.gilti_usd > 0:
        notes.append(
            f"GILTI: ${inp.gilti_usd:,.2f}. "
            f"Report on Form 8992 (if U.S. shareholder of CFC)."
        )

    # QBI (§199A)
    if inp.qbi_199a_usd > 0:
        notes.append(
            f"QBI: ${inp.qbi_199a_usd:,.2f}. "
            f"May qualify for 20% deduction under §199A (domestic business only, limitations apply)."
        )

    if total_income == 0:
        notes.append("No income reported for this partnership.")

    return IncomeSummaryResult(
        partnership_name=inp.partnership_name,
        subpart_f_income_usd=inp.subpart_f_income_usd,
        gilti_usd=inp.gilti_usd,
        qbi_199a_usd=inp.qbi_199a_usd,
        ordinary_income_usd=inp.ordinary_income_usd,
        capital_gain_usd=inp.capital_gain_usd,
        foreign_tax_paid_usd=inp.foreign_tax_paid_usd,
        total_income_usd=total_income,
        foreign_tax_credit_eligible=ftc_eligible,
        notes=notes,
    )


def calculate_penalty(inp: PenaltyCalculationInput) -> PenaltyResult:
    """
    Calculate penalties for failure to file Form 8865.

    Penalties (IRC §6679):
    - Base: $10,000 per year
    - Continued failure: +$10,000 per 30-day period (max $50,000 additional)
    - Willful failure: 50% of partnership value (if determinable) or criminal penalties
    """
    # Check if filing is required
    filing_check = check_filing_requirement(
        FilingRequirementInput(
            tax_year=inp.tax_year,
            partnerships=inp.partnerships,
        )
    )

    if not filing_check.filing_required:
        return PenaltyResult(
            base_penalty=0.0,
            continued_failure_penalty=0.0,
            willful_penalty=0.0,
            total_penalty=0.0,
            days_unreported=inp.days_unreported,
            is_willful=inp.is_willful,
            explanation="No filing requirement; no penalty applies.",
        )

    # Base penalty
    base_penalty = PENALTY_BASE

    # Continued failure penalty
    periods_30_days = inp.days_unreported // 30
    continued_penalty = min(
        periods_30_days * PENALTY_CONTINUED_PER_30_DAYS,
        PENALTY_CONTINUED_MAX,
    )

    # Willful penalty
    willful_penalty = 0.0
    if inp.is_willful:
        # 50% of total partnership value
        total_value = sum(p.fair_market_value_usd for p in inp.partnerships)
        if total_value > 0:
            willful_penalty = total_value * PENALTY_WILLFUL_PERCENTAGE
        else:
            willful_penalty = 100_000.0  # Minimum for willful failure

    total_penalty = base_penalty + continued_penalty + willful_penalty

    explanation = (
        f"Base penalty: ${base_penalty:,.2f}. "
        f"Continued failure ({inp.days_unreported} days, {periods_30_days} periods): "
        f"${continued_penalty:,.2f}. "
    )
    if inp.is_willful:
        explanation += (
            f"Willful failure penalty (50% of partnership value): ${willful_penalty:,.2f}. "
            f"Criminal penalties may also apply."
        )
    explanation += f" Total: ${total_penalty:,.2f}."

    return PenaltyResult(
        base_penalty=base_penalty,
        continued_failure_penalty=continued_penalty,
        willful_penalty=willful_penalty,
        total_penalty=total_penalty,
        days_unreported=inp.days_unreported,
        is_willful=inp.is_willful,
        explanation=explanation,
    )


def get_overview() -> Form8865Overview:
    """Return overview of Form 8865 requirements."""
    return Form8865Overview(
        title="Form 8865: Return of U.S. Persons With Respect to Certain Foreign Partnerships",
        description=(
            "Form 8865 is required by U.S. persons who have certain interests in "
            "foreign partnerships. The filing requirement depends on the level of "
            "ownership, control, and transactions with the partnership."
        ),
        category_1=(
            "Category 1: Control. You own (directly, indirectly, or constructively) "
            "more than 50% of the partnership. Must file Form 8865 with complete schedules."
        ),
        category_2=(
            "Category 2: Ownership (U.S.-controlled). You own 10% or more of a "
            "foreign partnership that is controlled by U.S. persons (collectively >50%)."
        ),
        category_3=(
            "Category 3: Reportable Event. You had an acquisition, disposition, or "
            "change in proportional interest of 10% or more during the tax year."
        ),
        category_4=(
            "Category 4: Contribution. You contributed property worth more than "
            "$100,000 to the foreign partnership during the tax year."
        ),
        category_5=(
            "Category 5: Ownership (≥10%). Post-2020 rules: you own 10% or more "
            "of the partnership (simplified reporting, Schedule K-2/K-3)."
        ),
        penalties=(
            "Failure to file Form 8865: $10,000 base penalty per year. "
            "Continued failure after IRS notice: additional $10,000 per 30-day period "
            "(max $50,000). Willful failure: 50% of partnership value or criminal penalties."
        ),
        filing_deadline=(
            "Form 8865 is due with your annual tax return (Form 1040). "
            "Deadline: typically April 15, or October 15 with extension."
        ),
        recommendation=(
            "If you own 10% or more of a foreign partnership, or if you control a "
            "foreign partnership, you likely have a filing requirement. Consult a "
            "tax professional familiar with international tax (Subpart F, GILTI, §199A)."
        ),
    )
