"""
Form 8962 — Premium Tax Credit.

Business logic for Form 8962 calculations under IRC §36B.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8962Input:
    """Input for Form 8962 calculation."""
    household_income: Decimal
    federal_poverty_line: Decimal
    advance_premium_tax_credit: Decimal
    benchmark_plan_premium: Decimal
    actual_premium_paid: Decimal
    family_size: int
    tax_year: int = 2025


@dataclass
class Form8962Result:
    """Result of Form 8962 calculation."""
    fpl_percentage: Decimal
    expected_contribution: Decimal
    premium_tax_credit: Decimal
    repayment: Decimal
    net_credit: Decimal
    explanation: str


# 2025 FPL percentage thresholds (simplified)
FPL_PERCENTAGE_RATES = [
    (Decimal("0"), Decimal("1.5"), Decimal("0.00")),
    (Decimal("1.5"), Decimal("2.0"), Decimal("0.02")),
    (Decimal("2.0"), Decimal("2.5"), Decimal("0.04")),
    (Decimal("2.5"), Decimal("3.0"), Decimal("0.06")),
    (Decimal("3.0"), Decimal("4.0"), Decimal("0.08")),
    (Decimal("4.0"), Decimal("999"), Decimal("0.085")),
]


def calculate_form8962(inp: Form8962Input) -> Form8962Result:
    """Calculate Form 8962 Premium Tax Credit."""
    # FPL percentage
    fpl_percentage = (inp.household_income / inp.federal_poverty_line).quantize(Decimal("0.01"))
    
    # Expected contribution percentage
    contribution_rate = Decimal("0.085")
    for low, high, rate in FPL_PERCENTAGE_RATES:
        if low <= fpl_percentage < high:
            contribution_rate = rate
            break
    
    # Expected contribution
    expected_contribution = (inp.household_income * contribution_rate).quantize(Decimal("0.01"))
    
    # Premium tax credit
    premium_tax_credit = max(inp.benchmark_plan_premium - expected_contribution, Decimal("0"))
    
    # Repayment (if advance PTC exceeds calculated credit)
    repayment = max(inp.advance_premium_tax_credit - premium_tax_credit, Decimal("0"))
    
    # Net credit
    net_credit = premium_tax_credit - inp.advance_premium_tax_credit
    
    explanation = (
        f"PTC: ${premium_tax_credit:,.2f}, Repayment: ${repayment:,.2f}, "
        f"Net: ${net_credit:,.2f}"
    )
    
    return Form8962Result(
        fpl_percentage=fpl_percentage,
        expected_contribution=expected_contribution,
        premium_tax_credit=premium_tax_credit,
        repayment=repayment,
        net_credit=net_credit,
        explanation=explanation,
    )


def get_form8962_overview() -> dict:
    """Returns a structured explanation of Form 8962."""
    return {
        "form": "Form 8962",
        "title": "Premium Tax Credit",
        "purpose": "Form 8962 is used to calculate the Premium Tax Credit for health insurance purchased through the Marketplace.",
        "who_must_file": [
            "Taxpayers who received advance premium tax credit payments",
            "Taxpayers who purchased health insurance through the Marketplace",
            "Taxpayers who want to claim the premium tax credit",
        ],
        "key_rules": [
            "Credit based on household income as percentage of federal poverty line",
            "Income limits: 100%-400% of FPL (special rules for 2021-2025)",
            "Reconciliation required if advance payments received",
            "Repayment limitations based on income level",
        ],
        "statutory_references": ["IRC §36B", "IRC §36B(f)"],
        "related_forms": ["Form 1040", "Form 1095-A"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8962",
    }
