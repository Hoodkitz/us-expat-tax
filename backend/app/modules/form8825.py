"""
Form 8825 – Rental Real Estate Income and Expenses.

Form 8825 is used by U.S. taxpayers to report income and expenses from
rental real estate. It is typically filed with Form 1040.

Key concepts:
- Rental income (rents received, advance rents, security deposits retained)
- Rental expenses (advertising, auto/travel, cleaning, commissions, insurance,
  legal fees, management fees, mortgage interest, repairs, supplies, taxes,
  utilities, depreciation)
- Passive activity loss limitations
- At-risk rules
- Schedule E attachment

Filing thresholds:
- Generally required if you receive rental income
- Passive activity loss rules apply if you actively participate
- Real estate professional status may allow full deduction
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Filing thresholds
RENTAL_INCOME_THRESHOLD = 0.0  # Any rental income triggers filing
PASSIVE_LOSS_LIMIT = 25_000.0  # Maximum passive loss deduction (active participation)
PASSIVE_LOSS_PHASE_OUT_START = 100_000.0  # AGI where phase-out begins
PASSIVE_LOSS_PHASE_OUT_END = 150_000.0  # AGI where phase-out ends

# Expense categories
EXPENSE_CATEGORIES = [
    "advertising",
    "auto_travel",
    "cleaning_maintenance",
    "commissions",
    "insurance",
    "legal_professional_fees",
    "management_fees",
    "mortgage_interest",
    "repairs",
    "supplies",
    "taxes",
    "utilities",
    "depreciation",
    "other",
]

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

EntityTypeLiteral = Literal["individual", "trust", "estate", "partnership", "corporation", "llc"]
FilingStatusLiteral = Literal["single", "married_filing_jointly", "married_filing_separately", "head_of_household", "qualifying_widow"]
ParticipationLevelLiteral = Literal["active", "passive", "real_estate_professional"]

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class FilingRequirementInput(BaseModel):
    """Input for checking Form 8825 filing requirement."""
    entity_type: EntityTypeLiteral = Field(..., description="Type of taxpayer entity")
    rental_income: float = Field(..., ge=0.0, description="Total rental income received")
    rental_expenses: float = Field(..., ge=0.0, description="Total rental expenses incurred")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")
    filing_status: FilingStatusLiteral = Field("single", description="Filing status")
    participation_level: ParticipationLevelLiteral = Field("active", description="Level of participation in rental activity")
    modified_agi: float = Field(0.0, ge=0.0, description="Modified adjusted gross income for passive loss limitation")


class IncomeSummaryInput(BaseModel):
    """Input for rental income summary calculation."""
    rents_received: float = Field(..., ge=0.0, description="Total rents received")
    advance_rents: float = Field(0.0, ge=0.0, description="Advance rents received")
    security_deposits_retained: float = Field(0.0, ge=0.0, description="Security deposits retained (not returned)")
    rental_expenses_paid_by_tenant: float = Field(0.0, ge=0.0, description="Rental expenses paid by tenant on your behalf")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")


class ExpenseCalculationInput(BaseModel):
    """Input for rental expense calculation."""
    advertising: float = Field(0.0, ge=0.0, description="Advertising expenses")
    auto_travel: float = Field(0.0, ge=0.0, description="Auto and travel expenses")
    cleaning_maintenance: float = Field(0.0, ge=0.0, description="Cleaning and maintenance")
    commissions: float = Field(0.0, ge=0.0, description="Commissions paid")
    insurance: float = Field(0.0, ge=0.0, description="Insurance premiums")
    legal_professional_fees: float = Field(0.0, ge=0.0, description="Legal and professional fees")
    management_fees: float = Field(0.0, ge=0.0, description="Management fees")
    mortgage_interest: float = Field(0.0, ge=0.0, description="Mortgage interest paid")
    repairs: float = Field(0.0, ge=0.0, description="Repairs and maintenance")
    supplies: float = Field(0.0, ge=0.0, description="Supplies purchased")
    taxes: float = Field(0.0, ge=0.0, description="Property taxes")
    utilities: float = Field(0.0, ge=0.0, description="Utilities expenses")
    depreciation: float = Field(0.0, ge=0.0, description="Depreciation expense")
    other_expenses: float = Field(0.0, ge=0.0, description="Other rental expenses")
    tax_year: int = Field(..., ge=2000, le=2099, description="Tax year")


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class FilingRequirementResult(BaseModel):
    """Result of filing requirement check."""
    filing_required: bool
    reasons: list[str]
    rental_income: float
    rental_expenses: float
    net_rental_income: float
    entity_type: str
    tax_year: int
    passive_loss_limit: float
    allowed_passive_loss: float
    suspended_passive_loss: float
    related_forms: list[str]
    recommendation: str


class IncomeSummaryResult(BaseModel):
    """Result of rental income summary."""
    gross_rental_income: float
    advance_rents: float
    security_deposits_retained: float
    tenant_paid_expenses: float
    total_rental_income: float
    tax_year: int
    explanation: str


class ExpenseCalculationResult(BaseModel):
    """Result of rental expense calculation."""
    total_expenses: float
    expense_breakdown: dict[str, float]
    deductible_expenses: float
    non_deductible_expenses: float
    tax_year: int
    explanation: str


class Form8825Overview(BaseModel):
    """Overview of Form 8825 requirements."""
    title: str
    description: str
    who_must_file: list[str]
    income_types: list[str]
    expense_categories: list[str]
    passive_loss_rules: str
    filing_deadline: str
    related_forms: list[str]
    recommendation: str


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def check_filing_requirement(inp: FilingRequirementInput) -> FilingRequirementResult:
    """
    Check if the taxpayer has a filing requirement for Form 8825.

    Form 8825 is required when:
    1. Taxpayer receives any rental income
    2. Net rental income is positive (profit)
    3. Passive activity loss rules apply
    """
    reasons: list[str] = []
    filing_required = False

    # Check if any rental income exists
    if inp.rental_income > RENTAL_INCOME_THRESHOLD:
        filing_required = True
        reasons.append(
            f"You received ${inp.rental_income:,.2f} in rental income. "
            f"Form 8825 is required to report this income."
        )
    else:
        reasons.append(
            "No rental income received. Form 8825 may not be required "
            "unless you have expenses to report."
        )

    # Calculate net rental income
    net_rental_income = inp.rental_income - inp.rental_expenses

    # Passive loss limitation calculation
    passive_loss_limit = PASSIVE_LOSS_LIMIT
    allowed_passive_loss = 0.0
    suspended_passive_loss = 0.0

    if inp.participation_level == "active" and inp.modified_agi > PASSIVE_LOSS_PHASE_OUT_START:
        # Phase-out calculation
        if inp.modified_agi >= PASSIVE_LOSS_PHASE_OUT_END:
            passive_loss_limit = 0.0
        else:
            phase_out_ratio = (inp.modified_agi - PASSIVE_LOSS_PHASE_OUT_START) / (
                PASSIVE_LOSS_PHASE_OUT_END - PASSIVE_LOSS_PHASE_OUT_START
            )
            passive_loss_limit = PASSIVE_LOSS_LIMIT * (1 - phase_out_ratio)

    if net_rental_income < 0:
        # Loss situation
        potential_loss = abs(net_rental_income)
        if inp.participation_level == "real_estate_professional":
            allowed_passive_loss = potential_loss
            reasons.append(
                "Real estate professional status allows full deduction of rental losses."
            )
        elif inp.participation_level == "active":
            allowed_passive_loss = min(potential_loss, passive_loss_limit)
            suspended_passive_loss = potential_loss - allowed_passive_loss
            reasons.append(
                f"Active participation allows up to ${passive_loss_limit:,.2f} "
                f"in passive loss deduction."
            )
            if suspended_passive_loss > 0:
                reasons.append(
                    f"${suspended_passive_loss:,.2f} of passive loss is suspended "
                    f"and carried forward to future years."
                )
        else:
            suspended_passive_loss = potential_loss
            reasons.append(
                "Passive participation: losses are suspended and carried forward."
            )
    else:
        reasons.append(
            f"Net rental income of ${net_rental_income:,.2f} is fully taxable."
        )

    if not filing_required:
        recommendation = (
            "Form 8825 is not required based on the information provided. "
            "However, if you have rental expenses, you may want to file to "
            "establish a basis for future deductions."
        )
    else:
        recommendation = (
            f"Form 8825 is REQUIRED for {inp.tax_year}. "
            f"Report all rental income and expenses. "
            f"Attach Form 8825 to your Form 1040. "
            f"Consider consulting a tax professional for passive activity loss planning."
        )

    return FilingRequirementResult(
        filing_required=filing_required,
        reasons=reasons,
        rental_income=inp.rental_income,
        rental_expenses=inp.rental_expenses,
        net_rental_income=net_rental_income,
        entity_type=inp.entity_type,
        tax_year=inp.tax_year,
        passive_loss_limit=passive_loss_limit,
        allowed_passive_loss=allowed_passive_loss,
        suspended_passive_loss=suspended_passive_loss,
        related_forms=["Schedule E", "Form 4562"] if filing_required else [],
        recommendation=recommendation,
    )


def calculate_income_summary(inp: IncomeSummaryInput) -> IncomeSummaryResult:
    """
    Calculate total rental income for Form 8825.

    Includes:
    - Rents received
    - Advance rents
    - Security deposits retained
    - Expenses paid by tenant
    """
    total_rental_income = (
        inp.rents_received
        + inp.advance_rents
        + inp.security_deposits_retained
        + inp.rental_expenses_paid_by_tenant
    )

    explanation = (
        f"Gross rental income: ${inp.rents_received:,.2f}\n"
        f"Advance rents: ${inp.advance_rents:,.2f}\n"
        f"Security deposits retained: ${inp.security_deposits_retained:,.2f}\n"
        f"Tenant-paid expenses: ${inp.rental_expenses_paid_by_tenant:,.2f}\n"
        f"Total rental income: ${total_rental_income:,.2f}"
    )

    return IncomeSummaryResult(
        gross_rental_income=inp.rents_received,
        advance_rents=inp.advance_rents,
        security_deposits_retained=inp.security_deposits_retained,
        tenant_paid_expenses=inp.rental_expenses_paid_by_tenant,
        total_rental_income=total_rental_income,
        tax_year=inp.tax_year,
        explanation=explanation,
    )


def calculate_expenses(inp: ExpenseCalculationInput) -> ExpenseCalculationResult:
    """
    Calculate total rental expenses for Form 8825.

    All listed expenses are generally deductible against rental income.
    """
    expense_breakdown = {
        "advertising": inp.advertising,
        "auto_travel": inp.auto_travel,
        "cleaning_maintenance": inp.cleaning_maintenance,
        "commissions": inp.commissions,
        "insurance": inp.insurance,
        "legal_professional_fees": inp.legal_professional_fees,
        "management_fees": inp.management_fees,
        "mortgage_interest": inp.mortgage_interest,
        "repairs": inp.repairs,
        "supplies": inp.supplies,
        "taxes": inp.taxes,
        "utilities": inp.utilities,
        "depreciation": inp.depreciation,
        "other": inp.other_expenses,
    }

    total_expenses = sum(expense_breakdown.values())

    # All expenses listed are deductible (no non-deductible categories in this simplified model)
    deductible_expenses = total_expenses
    non_deductible_expenses = 0.0

    explanation = (
        f"Total rental expenses: ${total_expenses:,.2f}\n"
        f"Deductible expenses: ${deductible_expenses:,.2f}\n"
        f"Non-deductible expenses: ${non_deductible_expenses:,.2f}\n\n"
        f"Expense breakdown:\n"
    )
    for category, amount in expense_breakdown.items():
        if amount > 0:
            explanation += f"  {category.replace('_', ' ').title()}: ${amount:,.2f}\n"

    return ExpenseCalculationResult(
        total_expenses=total_expenses,
        expense_breakdown=expense_breakdown,
        deductible_expenses=deductible_expenses,
        non_deductible_expenses=non_deductible_expenses,
        tax_year=inp.tax_year,
        explanation=explanation,
    )


def get_overview() -> Form8825Overview:
    """Return overview of Form 8825 requirements."""
    return Form8825Overview(
        title="Form 8825: Rental Real Estate Income and Expenses",
        description=(
            "Form 8825 is used by U.S. taxpayers to report income and expenses "
            "from rental real estate. It is typically filed with Form 1040 and "
            "attached to Schedule E."
        ),
        who_must_file=[
            "U.S. taxpayers who receive rental income from real estate",
            "Taxpayers with rental expenses to report",
            "Taxpayers with passive activity losses to report",
            "Real estate professionals with rental activities",
        ],
        income_types=[
            "Rents received",
            "Advance rents",
            "Security deposits retained",
            "Expenses paid by tenant on your behalf",
        ],
        expense_categories=EXPENSE_CATEGORIES,
        passive_loss_rules=(
            f"Active participants can deduct up to ${PASSIVE_LOSS_LIMIT:,.0f} "
            f"in rental losses against other income. The limit phases out "
            f"for AGI between ${PASSIVE_LOSS_PHASE_OUT_START:,.0f} and "
            f"${PASSIVE_LOSS_PHASE_OUT_END:,.0f}. Real estate professionals "
            f"can deduct all rental losses."
        ),
        filing_deadline=(
            "Form 8825 is due with your annual tax return (Form 1040). "
            "Deadline: typically April 15, or October 15 with extension."
        ),
        related_forms=[
            "Schedule E (Supplemental Income and Loss)",
            "Form 4562 (Depreciation and Amortization)",
            "Form 8582 (Passive Activity Loss Limitations)",
        ],
        recommendation=(
            "If you receive rental income, you must file Form 8825. "
            "Keep detailed records of all income and expenses. "
            "Consider consulting a tax professional for depreciation "
            "and passive activity loss planning."
        ),
    )
