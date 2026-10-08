"""
Form 8917 — Tuition and Fees Deduction.

Business logic for Form 8917 calculations under IRC §222.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8917Input:
    """Input for Form 8917 calculation."""
    qualified_expenses: Decimal
    agi: Decimal
    filing_status: str
    tax_year: int = 2025


@dataclass
class Form8917Result:
    """Result of Form 8917 calculation."""
    deduction: Decimal
    explanation: str


MAX_DEDUCTION = Decimal("4000")

# Income limits
INCOME_LIMIT_SINGLE = Decimal("80000")
INCOME_LIMIT_MARRIED = Decimal("160000")


def calculate_form8917(inp: Form8917Input) -> Form8917Result:
    """Calculate Form 8917 tuition and fees deduction."""
    # Check income limits
    income_limit = INCOME_LIMIT_MARRIED if inp.filing_status == "married_joint" else INCOME_LIMIT_SINGLE
    
    if inp.agi > income_limit:
        deduction = Decimal("0")
    else:
        deduction = min(inp.qualified_expenses, MAX_DEDUCTION)
    
    explanation = f"Tuition and fees deduction: ${deduction:,.2f}"
    
    return Form8917Result(
        deduction=deduction,
        explanation=explanation,
    )


def get_form8917_overview() -> dict:
    """Returns a structured explanation of Form 8917."""
    return {
        "form": "Form 8917",
        "title": "Tuition and Fees Deduction",
        "purpose": "Form 8917 is used to calculate the tuition and fees deduction for qualified education expenses.",
        "who_must_file": [
            "Taxpayers with qualified tuition and related expenses",
            "Students or parents paying for higher education",
            "Taxpayers who cannot claim education credits",
        ],
        "key_rules": [
            "Maximum deduction: $4,000",
            "Income limits: $80,000 (single), $160,000 (married)",
            "Cannot be claimed with education credits for same student",
            "Suspended 2025-2025 under TCJA (check current status)",
        ],
        "statutory_references": ["IRC §222", "IRC §222(b)"],
        "related_forms": ["Form 1040", "Form 8863"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8917",
    }
