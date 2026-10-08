"""
Form 8889 — Health Savings Accounts.

Business logic for Form 8889 calculations under IRC §223.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8889Input:
    """Input for Form 8889 calculation."""
    coverage_type: str  # 'self_only' or 'family'
    employee_contributions: Decimal
    employer_contributions: Decimal
    catch_up_contributions: Decimal = Decimal("0")
    distributions: Decimal = Decimal("0")
    qualified_medical_expenses: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form8889Result:
    """Result of Form 8889 calculation."""
    contribution_limit: Decimal
    total_contributions: Decimal
    excess_contributions: Decimal
    deduction: Decimal
    taxable_distribution: Decimal
    penalty: Decimal
    explanation: str


# 2025 HSA limits
HSA_LIMITS = {
    "self_only": Decimal("4300"),
    "family": Decimal("8550"),
}

CATCH_UP_LIMIT = Decimal("1000")


def calculate_form8889(inp: Form8889Input) -> Form8889Result:
    """Calculate Form 8889 HSA contributions and distributions."""
    # Contribution limit
    contribution_limit = HSA_LIMITS.get(inp.coverage_type, Decimal("4300"))
    if inp.catch_up_contributions > 0:
        contribution_limit += CATCH_UP_LIMIT
    
    # Total contributions
    total_contributions = inp.employee_contributions + inp.employer_contributions + inp.catch_up_contributions
    
    # Excess contributions
    excess_contributions = max(total_contributions - contribution_limit, Decimal("0"))
    
    # Deduction (employee contributions only)
    deduction = inp.employee_contributions
    
    # Taxable distribution
    taxable_distribution = max(inp.distributions - inp.qualified_medical_expenses, Decimal("0"))
    
    # 20% penalty on non-qualified distributions
    penalty = (taxable_distribution * Decimal("0.20")).quantize(Decimal("0.01"))
    
    explanation = (
        f"HSA: Contributions ${total_contributions:,.2f}, "
        f"Deduction ${deduction:,.2f}, Excess ${excess_contributions:,.2f}, "
        f"Taxable distribution ${taxable_distribution:,.2f}"
    )
    
    return Form8889Result(
        contribution_limit=contribution_limit,
        total_contributions=total_contributions,
        excess_contributions=excess_contributions,
        deduction=deduction,
        taxable_distribution=taxable_distribution,
        penalty=penalty,
        explanation=explanation,
    )


def get_form8889_overview() -> dict:
    """Returns a structured explanation of Form 8889."""
    return {
        "form": "Form 8889",
        "title": "Health Savings Accounts",
        "purpose": "Form 8889 is used to report HSA contributions, distributions, and calculate the HSA deduction.",
        "who_must_file": [
            "Taxpayers with a Health Savings Account",
            "Taxpayers who contributed to an HSA",
            "Taxpayers who took distributions from an HSA",
        ],
        "key_rules": [
            "2025 contribution limits: $4,300 (self-only), $8,550 (family)",
            "Catch-up contribution: $1,000 for age 55+",
            "Distributions for qualified medical expenses are tax-free",
            "6% excise tax on excess contributions",
        ],
        "statutory_references": ["IRC §223", "IRC §223(f)"],
        "related_forms": ["Form 1040", "Form 5329"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8889",
    }
