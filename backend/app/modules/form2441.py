"""
Form 2441 — Child and Dependent Care Expenses.

Business logic for Form 2441 calculations under IRC §21.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form2441Input:
    """Input for Form 2441 calculation."""
    num_dependents: int
    care_expenses: Decimal
    agi: Decimal
    tax_year: int = 2025


@dataclass
class Form2441Result:
    """Result of Form 2441 calculation."""
    max_expenses: Decimal
    applicable_percentage: Decimal
    credit_amount: Decimal
    explanation: str


def calculate_form2441(inp: Form2441Input) -> Form2441Result:
    """Calculate Form 2441 child and dependent care credit."""
    # Maximum expenses: $3,000 for one dependent, $6,000 for two or more
    max_expenses = Decimal("3000") if inp.num_dependents == 1 else Decimal("6000")
    
    # Applicable percentage based on AGI (2025)
    if inp.agi <= Decimal("15000"):
        applicable_percentage = Decimal("0.35")
    elif inp.agi >= Decimal("43000"):
        applicable_percentage = Decimal("0.20")
    else:
        # Linear phase-out from 35% to 20%
        applicable_percentage = Decimal("0.35") - ((inp.agi - Decimal("15000")) / Decimal("28000")) * Decimal("0.15")
        applicable_percentage = applicable_percentage.quantize(Decimal("0.01"))
    
    # Calculate credit
    eligible_expenses = min(inp.care_expenses, max_expenses)
    credit_amount = (eligible_expenses * applicable_percentage).quantize(Decimal("0.01"))
    
    explanation = (
        f"Child care credit: ${credit_amount:,.2f} "
        f"({applicable_percentage*100:.0f}% of ${eligible_expenses:,.2f})"
    )
    
    return Form2441Result(
        max_expenses=max_expenses,
        applicable_percentage=applicable_percentage,
        credit_amount=credit_amount,
        explanation=explanation,
    )


def get_form2441_overview() -> dict:
    """Returns a structured explanation of Form 2441."""
    return {
        "form": "Form 2441",
        "title": "Child and Dependent Care Expenses",
        "purpose": "Form 2441 is used to claim the Child and Dependent Care Credit for expenses paid for care of qualifying children or dependents.",
        "who_must_file": [
            "Taxpayers who paid for childcare for children under 13",
            "Taxpayers who paid for care of a disabled spouse or dependent",
            "Taxpayers who need to work or look for work",
        ],
        "key_rules": [
            "Credit is 20-35% of up to $3,000 (one dependent) or $6,000 (two or more)",
            "Percentage decreases as AGI increases",
            "Provider must be identified with TIN",
            "Both parents must work (if married filing jointly)",
        ],
        "statutory_references": ["IRC §21", "IRC §21(e)"],
        "related_forms": ["Schedule 3", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-2441",
    }
