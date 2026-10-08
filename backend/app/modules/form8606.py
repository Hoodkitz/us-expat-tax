"""
Form 8606 — Nondeductible IRAs.

Business logic for Form 8606 calculations under IRC §408.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8606Input:
    """Input for Form 8606 calculation."""
    nondeductible_contributions: Decimal
    traditional_ira_basis: Decimal
    distributions: Decimal
    ira_balance: Decimal
    tax_year: int = 2025


@dataclass
class Form8606Result:
    """Result of Form 8606 calculation."""
    total_basis: Decimal
    taxable_distribution: Decimal
    nontaxable_distribution: Decimal
    remaining_basis: Decimal
    explanation: str


def calculate_form8606(inp: Form8606Input) -> Form8606Result:
    """Calculate Form 8606 nondeductible IRA distributions."""
    # Total basis
    total_basis = inp.traditional_ira_basis + inp.nondeductible_contributions
    
    # Pro-rata rule
    if inp.ira_balance > 0:
        nontaxable_ratio = total_basis / inp.ira_balance
    else:
        nontaxable_ratio = Decimal("0")
    
    nontaxable_distribution = (inp.distributions * nontaxable_ratio).quantize(Decimal("0.01"))
    taxable_distribution = inp.distributions - nontaxable_distribution
    
    # Remaining basis
    remaining_basis = total_basis - nontaxable_distribution
    
    explanation = (
        f"IRA distribution: Taxable ${taxable_distribution:,.2f}, "
        f"Nontaxable ${nontaxable_distribution:,.2f}, Remaining basis ${remaining_basis:,.2f}"
    )
    
    return Form8606Result(
        total_basis=total_basis,
        taxable_distribution=taxable_distribution,
        nontaxable_distribution=nontaxable_distribution,
        remaining_basis=remaining_basis,
        explanation=explanation,
    )


def get_form8606_overview() -> dict:
    """Returns a structured explanation of Form 8606."""
    return {
        "form": "Form 8606",
        "title": "Nondeductible IRAs",
        "purpose": "Form 8606 is used to report nondeductible IRA contributions and calculate the taxable portion of distributions.",
        "who_must_file": [
            "Taxpayers who made nondeductible IRA contributions",
            "Taxpayers who took distributions from IRAs with basis",
            "Taxpayers who converted traditional IRAs to Roth IRAs",
        ],
        "key_rules": [
            "Required for any nondeductible contribution",
            "Tracks basis in traditional IRAs",
            "Pro-rata rule applies to distributions",
            "Must be filed even if no tax is due",
        ],
        "statutory_references": ["IRC §408", "IRC §408A"],
        "related_forms": ["Form 1040", "Form 5329"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8606",
    }
