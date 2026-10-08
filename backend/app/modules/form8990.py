"""
Form 8990 — Business Interest Expense Limitation.

Business logic for Form 8990 calculations under IRC §163(j).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8990Input:
    """Input for Form 8990 calculation."""
    business_interest_expense: Decimal
    adjusted_taxable_income: Decimal
    floor_plan_financing_interest: Decimal = Decimal("0")
    small_business_exception: bool = False
    tax_year: int = 2025


@dataclass
class Form8990Result:
    """Result of Form 8990 calculation."""
    limitation: Decimal
    deductible_interest: Decimal
    excess_interest: Decimal
    carryforward: Decimal
    explanation: str


ATI_PERCENTAGE = Decimal("0.30")
SMALL_BUSINESS_THRESHOLD = Decimal("31000000")


def calculate_form8990(inp: Form8990Input) -> Form8990Result:
    """Calculate Form 8990 business interest expense limitation."""
    # Small business exception
    if inp.small_business_exception:
        limitation = inp.business_interest_expense
    else:
        # 30% of ATI
        limitation = (inp.adjusted_taxable_income * ATI_PERCENTAGE).quantize(Decimal("0.01"))
    
    # Add back floor plan financing interest
    limitation += inp.floor_plan_financing_interest
    
    # Deductible interest
    deductible_interest = min(inp.business_interest_expense, limitation)
    
    # Excess interest
    excess_interest = inp.business_interest_expense - deductible_interest
    
    # Carryforward
    carryforward = excess_interest
    
    explanation = (
        f"Business interest: Deductible ${deductible_interest:,.2f}, "
        f"Excess ${excess_interest:,.2f}, Carryforward ${carryforward:,.2f}"
    )
    
    return Form8990Result(
        limitation=limitation,
        deductible_interest=deductible_interest,
        excess_interest=excess_interest,
        carryforward=carryforward,
        explanation=explanation,
    )


def get_form8990_overview() -> dict:
    """Returns a structured explanation of Form 8990."""
    return {
        "form": "Form 8990",
        "title": "Business Interest Expense Limitation",
        "purpose": "Form 8990 is used to calculate the limitation on business interest expense deductions under IRC §163(j).",
        "who_must_file": [
            "Businesses with average annual gross receipts over $31 million",
            "Taxpayers with business interest expense",
            "Partnerships and S-corporations with excess business interest",
        ],
        "key_rules": [
            "Deduction limited to 30% of ATI (adjusted taxable income)",
            "ATI approximates EBITDA through 2021, EBIT thereafter",
            "Excess can be carried forward indefinitely",
            "Small business exception for gross receipts under $31 million",
        ],
        "statutory_references": ["IRC §163(j)", "IRC §163(j)(10)"],
        "related_forms": ["Form 1040", "Form 1065", "Form 1120-S"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8990",
    }
