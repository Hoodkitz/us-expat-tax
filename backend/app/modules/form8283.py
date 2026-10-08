"""
Form 8283 — Noncash Charitable Contributions.

Business logic for Form 8283 calculations under IRC §170.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8283Input:
    """Input for Form 8283 calculation."""
    property_type: str
    fair_market_value: Decimal
    cost_basis: Decimal
    appraisal_required: bool = False
    tax_year: int = 2025


@dataclass
class Form8283Result:
    """Result of Form 8283 calculation."""
    deductible_amount: Decimal
    appraisal_required: bool
    explanation: str


def calculate_form8283(inp: Form8283Input) -> Form8283Result:
    """Calculate Form 8283 noncash charitable contributions."""
    # Deduction limited to fair market value
    deductible_amount = inp.fair_market_value
    
    # Appraisal required for property over $5,000
    appraisal_required = inp.fair_market_value > Decimal("5000")
    
    explanation = (
        f"Noncash contribution: FMV ${deductible_amount:,.2f}, "
        f"Appraisal {'required' if appraisal_required else 'not required'}"
    )
    
    return Form8283Result(
        deductible_amount=deductible_amount,
        appraisal_required=appraisal_required,
        explanation=explanation,
    )


def get_form8283_overview() -> dict:
    """Returns a structured explanation of Form 8283."""
    return {
        "form": "Form 8283",
        "title": "Noncash Charitable Contributions",
        "purpose": "Form 8283 is used to report noncash charitable contributions exceeding $500.",
        "who_must_file": [
            "Taxpayers who donated property worth more than $500",
            "Taxpayers who donated vehicles, boats, or aircraft",
            "Taxpayers who donated intellectual property",
        ],
        "key_rules": [
            "Required for noncash contributions over $500",
            "Appraisal required for property over $5,000",
            "Deduction limited to fair market value",
            "Special rules for vehicles and intellectual property",
        ],
        "statutory_references": ["IRC §170", "IRC §170(f)(11)"],
        "related_forms": ["Schedule A", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8283",
    }
