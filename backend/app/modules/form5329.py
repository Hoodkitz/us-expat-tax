"""
Form 5329 — Additional Taxes on Qualified Plans.

Business logic for Form 5329 calculations under IRC §72.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form5329Input:
    """Input for Form 5329 calculation."""
    early_distribution: Decimal = Decimal("0")
    excess_ira_contribution: Decimal = Decimal("0")
    excess_hsa_contribution: Decimal = Decimal("0")
    excess_rmd: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form5329Result:
    """Result of Form 5329 calculation."""
    early_distribution_penalty: Decimal
    excess_ira_penalty: Decimal
    excess_hsa_penalty: Decimal
    excess_rmd_penalty: Decimal
    total_penalty: Decimal
    explanation: str


def calculate_form5329(inp: Form5329Input) -> Form5329Result:
    """Calculate Form 5329 additional taxes."""
    # 10% penalty on early distributions
    early_distribution_penalty = (inp.early_distribution * Decimal("0.10")).quantize(Decimal("0.01"))
    
    # 6% excise tax on excess IRA contributions
    excess_ira_penalty = (inp.excess_ira_contribution * Decimal("0.06")).quantize(Decimal("0.01"))
    
    # 6% excise tax on excess HSA contributions
    excess_hsa_penalty = (inp.excess_hsa_contribution * Decimal("0.06")).quantize(Decimal("0.01"))
    
    # 25% penalty on excess RMD
    excess_rmd_penalty = (inp.excess_rmd * Decimal("0.25")).quantize(Decimal("0.01"))
    
    total_penalty = early_distribution_penalty + excess_ira_penalty + excess_hsa_penalty + excess_rmd_penalty
    
    explanation = (
        f"Additional taxes: Early distribution ${early_distribution_penalty:,.2f}, "
        f"Excess IRA ${excess_ira_penalty:,.2f}, Excess HSA ${excess_hsa_penalty:,.2f}, "
        f"Excess RMD ${excess_rmd_penalty:,.2f}"
    )
    
    return Form5329Result(
        early_distribution_penalty=early_distribution_penalty,
        excess_ira_penalty=excess_ira_penalty,
        excess_hsa_penalty=excess_hsa_penalty,
        excess_rmd_penalty=excess_rmd_penalty,
        total_penalty=total_penalty,
        explanation=explanation,
    )


def get_form5329_overview() -> dict:
    """Returns a structured explanation of Form 5329."""
    return {
        "form": "Form 5329",
        "title": "Additional Taxes on Qualified Plans",
        "purpose": "Form 5329 is used to report additional taxes on IRAs, other qualified plans, and health savings accounts.",
        "who_must_file": [
            "Taxpayers who took early distributions from retirement accounts",
            "Taxpayers who contributed excess amounts to IRAs",
            "Taxpayers who failed to take required minimum distributions",
        ],
        "key_rules": [
            "10% additional tax on early distributions (before age 59½)",
            "6% excise tax on excess IRA contributions",
            "25% additional tax on excess HSA contributions",
            "Exceptions apply for certain distributions",
        ],
        "statutory_references": ["IRC §72(t)", "IRC §4973", "IRC §4974"],
        "related_forms": ["Form 1040", "Form 8606"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-5329",
    }
