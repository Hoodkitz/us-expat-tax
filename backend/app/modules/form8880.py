"""
Form 8880 — Credit for Retirement Savings.

Business logic for Form 8880 calculations under IRC §25B.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8880Input:
    """Input for Form 8880 calculation."""
    retirement_contributions: Decimal
    agi: Decimal
    filing_status: str
    tax_year: int = 2025


@dataclass
class Form8880Result:
    """Result of Form 8880 calculation."""
    credit_rate: Decimal
    credit_amount: Decimal
    explanation: str


# 2025 Saver's Credit rates and thresholds
SAVERS_CREDIT_RATES = {
    "single": [
        (Decimal("0"), Decimal("21750"), Decimal("0.50")),
        (Decimal("21750"), Decimal("23625"), Decimal("0.20")),
        (Decimal("23625"), Decimal("36500"), Decimal("0.10")),
        (Decimal("36500"), Decimal("999999999"), Decimal("0")),
    ],
    "married_joint": [
        (Decimal("0"), Decimal("43500"), Decimal("0.50")),
        (Decimal("43500"), Decimal("47250"), Decimal("0.20")),
        (Decimal("47250"), Decimal("73000"), Decimal("0.10")),
        (Decimal("73000"), Decimal("999999999"), Decimal("0")),
    ],
    "head_of_household": [
        (Decimal("0"), Decimal("32625"), Decimal("0.50")),
        (Decimal("32625"), Decimal("35438"), Decimal("0.20")),
        (Decimal("35438"), Decimal("54750"), Decimal("0.10")),
        (Decimal("54750"), Decimal("999999999"), Decimal("0")),
    ],
}

MAX_CONTRIBUTION_FOR_CREDIT = Decimal("2000")


def calculate_form8880(inp: Form8880Input) -> Form8880Result:
    """Calculate Form 8880 retirement savings credit."""
    # Get rates for filing status
    rates = SAVERS_CREDIT_RATES.get(inp.filing_status, SAVERS_CREDIT_RATES["single"])
    
    # Find applicable rate
    credit_rate = Decimal("0")
    for low, high, rate in rates:
        if low <= inp.agi < high:
            credit_rate = rate
            break
    
    # Calculate credit
    eligible_contributions = min(inp.retirement_contributions, MAX_CONTRIBUTION_FOR_CREDIT)
    credit_amount = (eligible_contributions * credit_rate).quantize(Decimal("0.01"))
    
    explanation = (
        f"Saver's credit: ${credit_amount:,.2f} "
        f"({credit_rate*100:.0f}% of ${eligible_contributions:,.2f})"
    )
    
    return Form8880Result(
        credit_rate=credit_rate,
        credit_amount=credit_amount,
        explanation=explanation,
    )


def get_form8880_overview() -> dict:
    """Returns a structured explanation of Form 8880."""
    return {
        "form": "Form 8880",
        "title": "Credit for Retirement Savings",
        "purpose": "Form 8880 is used to claim the Saver's Credit for contributions to retirement accounts.",
        "who_must_file": [
            "Low to moderate income taxpayers with retirement contributions",
            "Taxpayers who contributed to 401(k), IRA, or other qualified plans",
            "Taxpayers who are not full-time students",
        ],
        "key_rules": [
            "Credit: 10%, 20%, or 50% of up to $2,000 ($4,000 married)",
            "Income limits: $39,500 (single), $79,000 (married) for 50% rate",
            "Must be at least 18 years old",
            "Cannot be claimed as a dependent",
        ],
        "statutory_references": ["IRC §25B", "IRC §25B(b)"],
        "related_forms": ["Form 1040", "Schedule 3"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8880",
    }
