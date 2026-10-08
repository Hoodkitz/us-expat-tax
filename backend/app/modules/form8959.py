"""
Form 8959 — Additional Medicare Tax.

Business logic for Form 8959 calculations under IRC §3101.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form8959Input:
    """Input for Form 8959 calculation."""
    wages: Decimal
    self_employment_income: Decimal
    filing_status: str
    medicare_withholding: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form8959Result:
    """Result of Form 8959 calculation."""
    threshold: Decimal
    excess_wages: Decimal
    additional_medicare_tax: Decimal
    total_tax: Decimal
    explanation: str


ADDITIONAL_MEDICARE_RATE = Decimal("0.009")

# Thresholds
THRESHOLDS = {
    "single": Decimal("200000"),
    "married_joint": Decimal("250000"),
    "married_separate": Decimal("125000"),
    "head_of_household": Decimal("200000"),
}


def calculate_form8959(inp: Form8959Input) -> Form8959Result:
    """Calculate Form 8959 Additional Medicare Tax."""
    threshold = THRESHOLDS.get(inp.filing_status, Decimal("200000"))
    
    # Total Medicare wages
    total_wages = inp.wages + inp.self_employment_income
    
    # Excess wages
    excess_wages = max(total_wages - threshold, Decimal("0"))
    
    # Additional Medicare tax
    additional_medicare_tax = (excess_wages * ADDITIONAL_MEDICARE_RATE).quantize(Decimal("0.01"))
    
    # Total tax (withholding + additional)
    total_tax = additional_medicare_tax - inp.medicare_withholding
    total_tax = max(total_tax, Decimal("0"))
    
    explanation = (
        f"Additional Medicare tax: ${additional_medicare_tax:,.2f} "
        f"on excess wages of ${excess_wages:,.2f}"
    )
    
    return Form8959Result(
        threshold=threshold,
        excess_wages=excess_wages,
        additional_medicare_tax=additional_medicare_tax,
        total_tax=total_tax,
        explanation=explanation,
    )


def get_form8959_overview() -> dict:
    """Returns a structured explanation of Form 8959."""
    return {
        "form": "Form 8959",
        "title": "Additional Medicare Tax",
        "purpose": "Form 8959 is used to calculate the Additional Medicare Tax on high-income earners.",
        "who_must_file": [
            "Taxpayers with wages above $200,000",
            "Taxpayers with self-employment income above thresholds",
            "Married taxpayers with combined income above $250,000",
        ],
        "key_rules": [
            "0.9% additional tax on wages above $200,000 (single)",
            "Thresholds: $200,000 (single), $250,000 (married), $125,000 (married separate)",
            "Employers must withhold at $200,000 regardless of filing status",
            "No employer withholding for self-employment income",
        ],
        "statutory_references": ["IRC §3101(b)(2)", "IRC §1401(b)(2)"],
        "related_forms": ["Form 1040", "Schedule SE"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-8959",
    }
