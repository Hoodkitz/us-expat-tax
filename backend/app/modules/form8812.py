"""
Form 8812 — Credits for Qualifying Children.

Business logic for Form 8812 calculations under IRC §24.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8812Input:
    """Input for Form 8812 calculation."""
    num_qualifying_children: int
    num_other_dependents: int
    agi: Decimal
    tax_year: int = 2025


@dataclass
class Form8812Result:
    """Result of Form 8812 calculation."""
    child_tax_credit: Decimal
    credit_for_other_dependents: Decimal
    refundable_credit: Decimal
    total_credit: Decimal
    explanation: str


CHILD_TAX_CREDIT_PER_CHILD = Decimal("2000")
CREDIT_FOR_OTHER_DEPENDENTS = Decimal("500")
REFUNDABLE_CREDIT_PER_CHILD = Decimal("1700")

# Phase-out thresholds
PHASEOUT_SINGLE = Decimal("200000")
PHASEOUT_MARRIED = Decimal("400000")


def calculate_form8812(inp: Form8812Input) -> Form8812Result:
    """Calculate Form 8812 child tax credit."""
    # Base credits
    child_tax_credit = inp.num_qualifying_children * CHILD_TAX_CREDIT_PER_CHILD
    credit_for_other_dependents = inp.num_other_dependents * CREDIT_FOR_OTHER_DEPENDENTS
    
    total_credit = child_tax_credit + credit_for_other_dependents
    
    # Phase-out (simplified - assumes single filer)
    if inp.agi > PHASEOUT_SINGLE:
        excess = inp.agi - PHASEOUT_SINGLE
        phaseout = (excess / Decimal("1000")) * Decimal("50")
        total_credit = max(total_credit - phaseout, Decimal("0"))
    
    # Refundable portion
    refundable_credit = min(inp.num_qualifying_children * REFUNDABLE_CREDIT_PER_CHILD, total_credit)
    
    explanation = (
        f"Child tax credit: ${child_tax_credit:,.2f}, "
        f"Other dependents: ${credit_for_other_dependents:,.2f}, "
        f"Refundable: ${refundable_credit:,.2f}"
    )
    
    return Form8812Result(
        child_tax_credit=child_tax_credit,
        credit_for_other_dependents=credit_for_other_dependents,
        refundable_credit=refundable_credit,
        total_credit=total_credit,
        explanation=explanation,
    )


def get_form8812_overview() -> dict:
    """Returns a structured explanation of Form 8812."""
    return {
        "form": "Form 8812",
        "title": "Credits for Qualifying Children",
        "purpose": "Form 8812 is used to calculate the Child Tax Credit and Credit for Other Dependents.",
        "who_must_file": [
            "Taxpayers with qualifying children under 17",
            "Taxpayers with other dependents",
            "Taxpayers claiming the Additional Child Tax Credit",
        ],
        "key_rules": [
            "Child Tax Credit: up to $2,000 per qualifying child",
            "Credit for Other Dependents: up to $500",
            "Refundable portion: up to $1,700 per child (2025)",
            "Phase-out begins at $200,000 (single), $400,000 (married)",
        ],
        "statutory_references": ["IRC §24", "IRC §24(h)"],
        "related_forms": ["Schedule 8812", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8812",
    }
