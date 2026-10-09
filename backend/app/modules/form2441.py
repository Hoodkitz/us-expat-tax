"""
Form 2441 — Child and Dependent Care Expenses.

Business logic for Form 2441 calculations under IRC §21.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal


@dataclass
class QualifyingPerson:
    """A qualifying person for Form 2441."""
    name: str
    relationship: str  # "child", "spouse", "dependent"
    age: int
    is_disabled: bool = False
    care_expenses: Decimal = Decimal(0)

    def is_qualifying(self) -> bool:
        """Check if this person qualifies under IRC §21(b)(1)(A)."""
        if self.relationship == "child":
            return self.age < 13
        elif self.relationship == "spouse":
            return self.is_disabled
        elif self.relationship == "dependent":
            return self.is_disabled or self.age >= 13
        return False


@dataclass
class Form2441Input:
    """Input for Form 2441 calculation."""
    num_dependents: int
    care_expenses: Decimal
    agi: Decimal
    tax_year: int = 2025
    earned_income: Decimal | None = None
    filing_status: str = "single"  # single, married_joint, married_separate, head_of_household
    qualifying_persons: list[QualifyingPerson] = field(default_factory=list)


@dataclass
class Form2441Result:
    """Result of Form 2441 calculation."""
    max_expenses: Decimal
    applicable_percentage: Decimal
    credit_amount: Decimal
    explanation: str
    eligible_expenses: Decimal = Decimal(0)
    earned_income_limit: Decimal | None = None
    is_eligible: bool = True
    num_qualifying_persons: int = 0


def _get_max_expenses(num_qualifying: int) -> Decimal:
    """Get maximum allowable expenses based on number of qualifying persons."""
    if num_qualifying == 0:
        return Decimal(0)
    elif num_qualifying == 1:
        return Decimal(3000)
    else:
        return Decimal(6000)


def _get_applicable_percentage(agi: Decimal, tax_year: int = 2025) -> Decimal:
    """
    Get applicable percentage based on AGI.
    
    For 2025:
    - AGI <= $15,000: 35%
    - AGI >= $43,000: 20%
    - Between: linear phase-out from 35% to 20%
    """
    if agi <= Decimal(15000):
        return Decimal("0.35")
    elif agi >= Decimal(43000):
        return Decimal("0.20")
    else:
        # Linear phase-out: 35% at $15k, 20% at $43k
        # Slope = -0.15 / 28000 per dollar
        percentage = Decimal("0.35") - ((agi - Decimal(15000)) / Decimal(28000)) * Decimal("0.15")
        return percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_earned_income_limit(filing_status: str, earned_income: Decimal | None) -> Decimal | None:
    """
    Get earned income limit for the credit.
    
    The credit is limited to the earned income of the taxpayer (or spouse if married).
    """
    if earned_income is not None:
        return earned_income
    return None


def calculate_form2441(inp: Form2441Input) -> Form2441Result:
    """Calculate Form 2441 child and dependent care credit."""
    # Determine number of qualifying persons
    if inp.qualifying_persons:
        num_qualifying = sum(1 for p in inp.qualifying_persons if p.is_qualifying())
    else:
        num_qualifying = inp.num_dependents

    # Maximum expenses based on qualifying persons
    max_expenses = _get_max_expenses(num_qualifying)

    # Applicable percentage based on AGI
    applicable_percentage = _get_applicable_percentage(inp.agi, inp.tax_year)

    # Eligible expenses (lesser of actual expenses or max)
    eligible_expenses = min(inp.care_expenses, max_expenses)

    # Earned income limit
    earned_income_limit = _get_earned_income_limit(inp.filing_status, inp.earned_income)

    # Calculate credit
    credit_amount = (eligible_expenses * applicable_percentage).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Apply earned income limit if applicable
    if earned_income_limit is not None and credit_amount > earned_income_limit:
        credit_amount = earned_income_limit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Determine eligibility
    is_eligible = num_qualifying > 0 and inp.care_expenses > 0

    # Build explanation
    if not is_eligible:
        explanation = "No qualifying persons or no care expenses. Credit not available."
    else:
        explanation = (
            f"Child care credit: ${credit_amount:,.2f} "
            f"({applicable_percentage * 100:.0f}% of ${eligible_expenses:,.2f} eligible expenses)"
        )
        if earned_income_limit is not None and credit_amount >= earned_income_limit:
            explanation += f" (limited to earned income of ${earned_income_limit:,.2f})"

    return Form2441Result(
        max_expenses=max_expenses,
        applicable_percentage=applicable_percentage,
        credit_amount=credit_amount,
        explanation=explanation,
        eligible_expenses=eligible_expenses,
        earned_income_limit=earned_income_limit,
        is_eligible=is_eligible,
        num_qualifying_persons=num_qualifying,
    )


def get_form2441_overview() -> dict:
    """Returns a structured explanation of Form 2441."""
    return {
        "form": "Form 2441",
        "title": "Form 2441 — Child and Dependent Care Expenses",
        "purpose": (
            "Form 2441 is used to claim the Child and Dependent Care Credit for expenses "
            "paid for care of qualifying children under age 13 or disabled dependents/spouses, "
            "allowing the taxpayer (or spouse if married) to work or look for work."
        ),
        "who_must_file": [
            "Taxpayers who paid for childcare for children under 13",
            "Taxpayers who paid for care of a disabled spouse or dependent",
            "Taxpayers who need to work or look for work",
            "Married filing jointly: both spouses must have earned income (unless one is a student or disabled)",
        ],
        "key_rules": [
            "Credit is 20-35% of up to $3,000 (one qualifying person) or $6,000 (two or more)",
            "Percentage decreases as AGI increases from $15,000 to $43,000",
            "Provider must be identified with TIN on return",
            "Both parents must work (if married filing jointly)",
            "Credit is limited to the lesser of earned income or spouse's earned income",
            "Qualifying person must be under 13 or disabled",
            "Expenses must be for care (not education, food, or clothing)",
        ],
        "statutory_references": ["IRC §21", "IRC §21(e)", "IRC §21(b)(1)(A)"],
        "related_forms": ["Schedule 3", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-2441",
    }
