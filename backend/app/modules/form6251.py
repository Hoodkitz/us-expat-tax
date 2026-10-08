"""
Form 6251 — Alternative Minimum Tax.

Business logic for Form 6251 calculations under IRC §55.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Form6251Input:
    """Input for Form 6251 calculation."""
    filing_status: str
    regular_taxable_income: Decimal
    tax_preferences: Decimal = Decimal("0")
    adjustments: Decimal = Decimal("0")
    tax_year: int = 2025


@dataclass
class Form6251Result:
    """Result of Form 6251 calculation."""
    amt_income: Decimal
    exemption: Decimal
    amt_base: Decimal
    amt: Decimal
    regular_tax: Decimal
    amt_due: Decimal
    explanation: str


AMT_EXEMPTIONS = {
    "single": Decimal("85700"),
    "married_joint": Decimal("133300"),
    "married_separate": Decimal("66650"),
    "head_of_household": Decimal("85700"),
}

AMT_EXEMPTION_PHASEOUT = {
    "single": Decimal("626350"),
    "married_joint": Decimal("1252700"),
    "married_separate": Decimal("626350"),
    "head_of_household": Decimal("626350"),
}


def calculate_form6251(inp: Form6251Input) -> Form6251Result:
    """Calculate Form 6251 Alternative Minimum Tax."""
    # AMT income
    amt_income = inp.regular_taxable_income + inp.tax_preferences + inp.adjustments
    
    # AMT exemption
    exemption = AMT_EXEMPTIONS.get(inp.filing_status, Decimal("85700"))
    
    # Phase-out
    phaseout_threshold = AMT_EXEMPTION_PHASEOUT.get(inp.filing_status, Decimal("626350"))
    if amt_income > phaseout_threshold:
        excess = amt_income - phaseout_threshold
        exemption_reduction = (excess * Decimal("0.25")).quantize(Decimal("0.01"))
        exemption = max(exemption - exemption_reduction, Decimal("0"))
    
    # AMT base
    amt_base = max(amt_income - exemption, Decimal("0"))
    
    # AMT calculation (26% on first $239,100, 28% above)
    if amt_base <= Decimal("239100"):
        amt = (amt_base * Decimal("0.26")).quantize(Decimal("0.01"))
    else:
        amt = (Decimal("239100") * Decimal("0.26") + (amt_base - Decimal("239100")) * Decimal("0.28")).quantize(Decimal("0.01"))
    
    # Regular tax (simplified)
    regular_tax = (inp.regular_taxable_income * Decimal("0.22")).quantize(Decimal("0.01"))
    
    # AMT due
    amt_due = max(amt - regular_tax, Decimal("0"))
    
    explanation = (
        f"AMT: Income ${amt_income:,.2f}, Exemption ${exemption:,.2f}, "
        f"AMT ${amt:,.2f}, Due ${amt_due:,.2f}"
    )
    
    return Form6251Result(
        amt_income=amt_income,
        exemption=exemption,
        amt_base=amt_base,
        amt=amt,
        regular_tax=regular_tax,
        amt_due=amt_due,
        explanation=explanation,
    )


def get_form6251_overview() -> dict:
    """Returns a structured explanation of Form 6251."""
    return {
        "form": "Form 6251",
        "title": "Alternative Minimum Tax",
        "purpose": "Form 6251 is used to calculate the Alternative Minimum Tax (AMT) for high-income taxpayers.",
        "who_must_file": [
            "Taxpayers with high income and certain deductions",
            "Taxpayers with incentive stock options",
            "Taxpayers with large state and local tax deductions",
        ],
        "key_rules": [
            "AMT exemption: $85,700 (single), $133,300 (married filing jointly)",
            "AMT rates: 26% and 28%",
            "Exemption phases out at higher income levels",
            "Certain deductions are added back for AMT",
        ],
        "statutory_references": ["IRC §55", "IRC §56", "IRC §57"],
        "related_forms": ["Form 1040", "Schedule A"],
        "irs_reference": "https://www.irs.gov/forms-pubs/about-form-6251",
    }
