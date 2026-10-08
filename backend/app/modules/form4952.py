"""
Form 4952 — Investment Interest Expense Deduction.

Business logic for Form 4952 calculations under IRC §163.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form4952Input:
    """Input for Form 4952 calculation."""
    investment_interest_expense: Decimal
    investment_income: Decimal
    disallowed_interest_carryforward: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form4952Result:
    """Result of Form 4952 calculation."""
    deductible_interest: Decimal
    disallowed_interest: Decimal
    carryforward: Decimal
    explanation: str


def calculate_form4952(inp: Form4952Input) -> Form4952Result:
    """Calculate Form 4952 investment interest expense deduction."""
    # Deduction limited to net investment income
    deductible_interest = min(inp.investment_interest_expense, inp.investment_income)
    
    # Disallowed interest carried forward
    disallowed_interest = inp.investment_interest_expense - deductible_interest
    carryforward = disallowed_interest + inp.disallowed_interest_carryforward
    
    explanation = (
        f"Investment interest deduction: ${deductible_interest:,.2f}, "
        f"Carryforward: ${carryforward:,.2f}"
    )
    
    return Form4952Result(
        deductible_interest=deductible_interest,
        disallowed_interest=disallowed_interest,
        carryforward=carryforward,
        explanation=explanation,
    )


def get_form4952_overview() -> dict:
    """Returns a structured explanation of Form 4952."""
    return {
        "form": "Form 4952",
        "title": "Investment Interest Expense Deduction",
        "purpose": "Form 4952 is used to calculate the deductible amount of investment interest expense.",
        "who_must_file": [
            "Taxpayers with investment interest expense",
            "Taxpayers with investment income",
            "Taxpayers with disallowed investment interest from prior years",
        ],
        "key_rules": [
            "Deduction limited to net investment income",
            "Excess can be carried forward indefinitely",
            "Investment income includes interest, dividends, capital gains (if elected)",
            "Does not include passive activity income",
        ],
        "statutory_references": ["IRC §163(d)", "IRC §163(h)"],
        "related_forms": ["Schedule A", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-4952",
    }
