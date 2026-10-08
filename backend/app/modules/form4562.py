"""
Form 4562 — Depreciation and Amortization.

Business logic for Form 4562 calculations under IRC §167.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form4562Input:
    """Input for Form 4562 calculation."""
    asset_cost: Decimal
    asset_type: str  # '5_year', '7-year', '15-year', '27.5-year', '39-year'
    business_use_percentage: Decimal
    section_179_election: bool
    bonus_depreciation: bool
    tax_year: int = 2025


@dataclass
class Form4562Result:
    """Result of Form 4562 calculation."""
    section_179_deduction: Decimal
    bonus_depreciation: Decimal
    regular_depreciation: Decimal
    total_depreciation: Decimal
    explanation: str


# MACRS depreciation rates (simplified)
MACRS_RATES = {
    "5-year": [Decimal("0.20"), Decimal("0.32"), Decimal("0.192"), Decimal("0.1152"), Decimal("0.1152"), Decimal("0.0576")],
    "7-year": [Decimal("0.1429"), Decimal("0.2449"), Decimal("0.1749"), Decimal("0.1249"), Decimal("0.0893"), Decimal("0.0892"), Decimal("0.0893"), Decimal("0.0446")],
    "15-year": [Decimal("0.05"), Decimal("0.095"), Decimal("0.0855"), Decimal("0.077"), Decimal("0.0693"), Decimal("0.0623"), Decimal("0.059"), Decimal("0.059"), Decimal("0.0591"), Decimal("0.059"), Decimal("0.0591"), Decimal("0.059"), Decimal("0.0591"), Decimal("0.059"), Decimal("0.0591"), Decimal("0.0295")],
    "27.5-year": [Decimal("0.03636")],
    "39-year": [Decimal("0.02564")],
}

SECTION_179_LIMIT = Decimal("1220000")  # 2025
BONUS_DEPRECIATION_RATE = Decimal("0.40")  # 2025


def calculate_form4562(inp: Form4562Input) -> Form4562Result:
    """Calculate Form 4562 depreciation."""
    business_cost = inp.asset_cost * inp.business_use_percentage
    
    # Section 179 deduction
    section_179_deduction = Decimal("0")
    if inp.section_179_election:
        section_179_deduction = min(business_cost, SECTION_179_LIMIT)
    
    remaining_basis = business_cost - section_179_deduction
    
    # Bonus depreciation
    bonus_dep = Decimal("0")
    if inp.bonus_depreciation:
        bonus_dep = (remaining_basis * BONUS_DEPRECIATION_RATE).quantize(Decimal("0.01"))
    
    remaining_basis -= bonus_dep
    
    # Regular MACRS depreciation (first year)
    rates = MACRS_RATES.get(inp.asset_type, MACRS_RATES["5-year"])
    regular_dep = (remaining_basis * rates[0]).quantize(Decimal("0.01"))
    
    total_depreciation = section_179_deduction + bonus_dep + regular_dep
    
    explanation = (
        f"Depreciation: Section 179 ${section_179_deduction:,.2f}, "
        f"Bonus ${bonus_dep:,.2f}, MACRS ${regular_dep:,.2f}"
    )
    
    return Form4562Result(
        section_179_deduction=section_179_deduction,
        bonus_depreciation=bonus_dep,
        regular_depreciation=regular_dep,
        total_depreciation=total_depreciation,
        explanation=explanation,
    )


def get_form4562_overview() -> dict:
    """Returns a structured explanation of Form 4562."""
    return {
        "form": "Form 4562",
        "title": "Depreciation and Amortization",
        "purpose": "Form 4562 is used to claim depreciation and amortization deductions for business assets.",
        "who_must_file": [
            "Business owners with depreciable assets",
            "Self-employed individuals with business equipment",
            "Rental property owners",
        ],
        "key_rules": [
            "Section 179 expensing: up to $1,220,000 (2025)",
            "Bonus depreciation: 40% (2025)",
            "MACRS recovery periods: 5, 7, 15, 27.5, 39 years",
            "Listed property has special rules",
        ],
        "statutory_references": ["IRC §167", "IRC §168", "IRC §179"],
        "related_forms": ["Schedule C", "Form 1040"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-4562",
    }
